from flask import Flask, render_template, url_for, request
from apscheduler.schedulers.background import BackgroundScheduler
from amadeus import Client, ResponseError
import csv, json, requests
from datetime import datetime

app = Flask(__name__)

# travel restriction by country data is updated daily from this website: https://data.humdata.org/dataset/covid-19-global-travel-restrictions-and-airline-information
# csv file is converted to JSON format
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

# create scheduler to update daily 
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(updateJSON,'interval',minutes=1440)
scheduler.start()


# https://github.com/amadeus4dev/amadeus-python
amadeus = Client(
    client_id='u5zmdzdBHAKZt13AbvSmfsDFO6kfC68A',
    client_secret='PkfVAE5FMJc2G9Gv'
)

@app.route('/')
@app.route('/home', methods=['POST', 'GET'])
def home():
    # get data from restrictions file
    with open('static/restrictions_data.json', 'r') as infile:
            r_data = json.load(infile)

    # create country list for dropdown 
    country_list = []
    counter = 0
    for country in r_data:
            country_list.append(country["adm0_name"])
            counter += 1
    country_list.sort()

    # if post is sent
    if request.method == 'POST':

        # get country restrictions
        if request.form['submit_button'] == "Get Country Restrictions":
            country_name = request.form['country']
            counter = 0
            try:
                # find selected country in restriction file
                for country in r_data:
                    if country_name == country["adm0_name"]:
                        data_obj = r_data[counter]
                    counter += 1

                # get airport codes and specific country airport codes for flight finder
                all_airport_codes, country_airport_codes = get_airport_codes(country_name)
                results = {
                    'country_submit': True,
                    'flight_submit': False, 
                    'data_obj': data_obj, 
                    'country_list': country_list, 
                    'all_airport_codes': all_airport_codes, 
                    'country_airport_codes': country_airport_codes,
                    'country_name': country_name
                }
                return render_template('home.html', results = results)
            except:
                return 'There was an issue finding that country info'

        # get cheapest flight
        elif request.form['submit_button'] == "Get Flights":
            country_name = request.form['country']
            destination = request.form['destination']
            origination = request.form['origination']
            departureDate = request.form['departure']
            request_data = {
                'destination': destination,
                'origination': origination,
                'departureDate' : departureDate
            }

            # get country restrictions
            counter = 0
            data_obj = None
            for country in r_data:
                if country_name == country["adm0_name"]:
                    data_obj = r_data[counter]
                counter += 1
            all_airport_codes, country_airport_codes = get_airport_codes(country_name)

            # Return page with error statement if departure date not entered
            date_time_obj = datetime.strptime(departureDate,'%Y-%m-%d')
            if not departureDate or (date_time_obj.date() < datetime.date(datetime.now())):
                results = {
                    'country_submit': True,
                    'flight_submit': False, 
                    'invalid_date': True,
                    'data_obj': data_obj, 
                    'country_list': country_list, 
                    'all_airport_codes': all_airport_codes, 
                    'country_airport_codes': country_airport_codes,
                    'country_name': country_name
                }
                return render_template('home.html', results = results)

            # else get flight data for selected dates and country 
            flight_data = flights(destination, origination, departureDate)
            results = {
                    'country_submit': True,
                    'flight_submit': True,
                    'data_obj': data_obj, 
                    'country_list': country_list, 
                    'all_airport_codes': all_airport_codes, 
                    'country_airport_codes': country_airport_codes,
                    'flight_data': flight_data, 
                    'request_data': request_data
                }
            return render_template('home.html', results = results)

    # not post, render home page with original form to select a country 
    results = {
                'country_submit': False,
                'flight_submit': False,
                'country_list': country_list
            }
    return render_template('home.html', results = results)
    

def flights(destination, origination, departureDate):
    '''
    Takes origination and destination airport codes and departure date and returns the flight data
    for the cheapest flight
    '''

    # get the cheapest flight from amadeus flight API
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

        # get airline name from airline code and number of connecting flights
        airline_names, class_names = get_airlines(cheapest_flight)
        connecting_flights = len(cheapest_flight['itineraries'][0]['segments']) - 1

        duration = cheapest_flight['itineraries'][0]['duration'][2:]

        # get necesasary data for cheapest flight 
        data = cheapest_flight['itineraries'][0]['segments']

        # add class name and airline carrier 
        for i in range(len(data)):
            data[i]['airClass'] = class_names[i]
            data[i]['airName'] = airline_names[i]

        flight_data = {
            'num_stops' : connecting_flights,
            'price' : cheapest_flight['price']['total'],
            'duration' : duration,
            'data' : data
        }
        return flight_data
    except ResponseError as error:
        raise error


def get_airport_codes(country):
    '''
    Takes a country and returns a list of valid airport codes for the world as well as the airport 
    codes for that specific country
    '''

    # get all airports from airports file 
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


def get_airlines(flight_data):
    '''
    Takes a flight data object and returns a tuple of strings, airline name and class name for each 
    leg of the itinerary
    '''
    # get carrier codes for each flight in itinerary 
    all_codes = []
    for flight in flight_data['itineraries'][0]['segments']:
        all_codes.append(flight['carrierCode'])
    airline_names = []

    # get airline name from code for each flight in itinerary 
    for code in all_codes:
        airline = amadeus.reference_data.airlines.get(airlineCodes=code).data[0]['businessName']
        airline_names.append(airline)

    # get class name for each flight
    class_names = []
    for flight in flight_data['travelerPricings'][0]['fareDetailsBySegment']:
        class_names.append(flight['cabin'])
    return airline_names, class_names



if __name__ == '__main__':
    app.run(debug=True)
