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
    client_id='key',
    client_secret='secret'
)

@app.route('/')
@app.route('/home', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        country_name = request.form['country']
        counter = 0
        try:
            for country in r_data:
                if country_name == country["adm0_name"]:
                    return render_template('home.html', r_data=r_data[counter])
                counter += 1
        except:
            return 'There was an issue finding that country info'
    else:
        return render_template('home.html')

try:
    flights = amadeus.shopping.flight_offers_search.get(
        originLocationCode='SEA', 
        destinationLocationCode='PDX',
        departureDate='2020-07-01', 
        adults=1,
        currencyCode="USD")
    cheapest_flight = flights.data[0]
    print(cheapest_flight)
    # un-comment the code below to write the data to a json file for easier viewing!
    # with open ('flight.json', 'w') as outfile:
    #     json.dump(cheapest_flight, outfile)
except ResponseError as error:
    raise error
if __name__ == '__main__':
    app.run(debug=True)