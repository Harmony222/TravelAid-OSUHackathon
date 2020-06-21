from flask import Flask, render_template, url_for, request
from apscheduler.schedulers.background import BackgroundScheduler
from amadeus import Client, ResponseError
# from amadeusapi import *
import csv, json, requests


with open('static/restrictions_data.json', 'r') as infile:
    r_data = json.load(infile)


# travel restriction by country data is updated daily from this website: https://data.humdata.org/dataset/covid-19-global-travel-restrictions-and-airline-information
# pip3 install apscheduler to call updateJSON function everyday
# pip3 install requests to get csv file
# csv file is converted to JSON format
# https://stackoverflow.com/a/46738061
def updateJSON():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTxATUFm0tR6Vqq-UAOuqQ-BoQDvYYEe-BmJ20s50yBKDHEifGofP2P1LJ4jWFIu0Pb_4kRhQeyhHmn/pub?gid=0&single=true&output=csv"
    req = requests.get(url)
    with open("static/data.csv",'wb') as f: 
        f.write(req.content) 

    with open('static/data.csv', 'rt') as csvdata:
        next(csvdata, None)
        reader = csv.DictReader(csvdata,fieldnames=['adm0_name','iso3','X','Y','published','sources','info','optional1','optional2','optional3','ObjectId'])
        json.dump([row for row in reader], open('static/restrictions_data.json', 'w+'))
    print("Successfully executed this function!")


scheduler = BackgroundScheduler(daemon=True)
#scheduler.add_job(updateJSON,'interval',minutes=2)
# there's prob a better way to do this than min
scheduler.add_job(updateJSON,'interval',minutes=1440)
scheduler.start()

app = Flask(__name__)

# https://github.com/amadeus4dev/amadeus-python
amadeus = Client(
    client_id='u5zmdzdBHAKZt13AbvSmfsDFO6kfC68A',
    client_secret='PkfVAE5FMJc2G9Gv'
)

@app.route('/')
@app.route('/home', methods=['POST', 'GET'])
def home():
    if request.method == 'POST' or request.method == 'GET':
        country_list = []
        counter = 0
        for country in r_data:
                country_list.append(country["adm0_name"])
                counter += 1
        country_list.sort()
    if request.method == 'POST':
        if request.form['submit_button'] == "Get Country Restrictions":
            country_name = request.form['country']
            counter = 0
            try:
                for country in r_data:
                    if country_name == country["adm0_name"]:
                        data_obj = r_data[counter]
                        # data_obj = {
                        #     'name': data['adm0_name'],
                        #     'info': data['info'],
                        #     'optional2': data['optional2']
                        # }
                    counter += 1
                all_airport_codes, country_airport_codes = get_airport_codes(country_name)
                return render_template('home.html', country_submit=True, flight_submit=False, 
                                                    data_obj=data_obj, country_list=country_list, 
                                                    all_airport_codes=all_airport_codes, 
                                                    country_airport_codes=country_airport_codes,
                                                    country_name=country_name)
            except:
                return 'There was an issue finding that country info'
        elif request.form['submit_button'] == "Get Flights":
            country_name = request.form['country']
            destination = request.form['destination']
            origination = request.form['origination']
            departureDate = request.form['departure']
            counter = 0
            data_obj = None
            for country in r_data:
                if country_name == country["adm0_name"]:
                    data_obj = r_data[counter]
                counter += 1
            all_airport_codes, country_airport_codes = get_airport_codes(country_name)
            # Return page with error statement if departure date not entered
            if not departureDate:
                return render_template('home.html', country_submit=True, flight_submit=True,
                                    invalid_date=True, 
                                    data_obj=data_obj, country_list=country_list,
                                    all_airport_codes=all_airport_codes, 
                                    country_airport_codes=country_airport_codes, country_name=country_name)
            flight_data = flights(destination, origination, departureDate)
            return render_template('home.html', country_submit=True, flight_submit=True, 
                                                data_obj=data_obj, country_list=country_list,
                                                all_airport_codes=all_airport_codes, 
                                                country_airport_codes=country_airport_codes,
                                                flight_data=flight_data)
    else:
        return render_template('home.html', country_submit=False, flight_submit=False, 
                                            country_list=country_list)

    

def flights(destination, origination, departureDate):
    seat_classes = {
        'economy' : ['K', 'L', 'Q', 'V', 'W', 'U', 'T', 'X', 'N', 'O', 'S', 'Y', 'B', 'M', 'H', 'W', 'E'],
        'business' : ['D', 'I', 'Z', 'J', 'C', 'D'],
        'first' : ['A', 'F']
    }

    try:
        flights = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origination, 
            destinationLocationCode=destination,
            departureDate=departureDate,
            adults=1,
            currencyCode="USD")
        if len(flights.data) > 0: 
            cheapest_flight = flights.data[0]
        else:
            return None
        airline_code = cheapest_flight['itineraries'][0]['segments'][0]['carrierCode']
        airline = amadeus.reference_data.airlines.get(airlineCodes=airline_code).data[0]['businessName']
        class_code = cheapest_flight['travelerPricings'][0]['fareDetailsBySegment'][0]['class'] 

        for cl in seat_classes:
            for code in seat_classes[cl]:
                if class_code == code:
                    class_name = cl
                else:
                    class_name = "economy"

        duration = cheapest_flight['itineraries'][0]['segments'][0]['duration']
        duration_shortened = duration[2:]
        flight_data = {
            'airline' : airline,
            'num_stops' : cheapest_flight['itineraries'][0]['segments'][0]['numberOfStops'],
            'price' : cheapest_flight['price']['total'],
            'duration' : duration_shortened,
            'seat_class' : class_name
        }
        return flight_data
    except ResponseError as error:
        raise error

def get_airport_codes(country):
    with open('static/airports.json', 'r') as infile:
        airport_data = json.load(infile)
    all_airports = []
    airports = []
    for airport in airport_data:
        all_airports.append(airport['code'])
        if country == airport['country']:
            airports.append(airport['code'])
    all_airports.sort()
    airports.sort()
    return all_airports, airports


if __name__ == '__main__':
    app.run(debug=True)
