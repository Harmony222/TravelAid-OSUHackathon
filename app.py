from flask import Flask, render_template, url_for
import json
from amadeus import Client, ResponseError
from amadeusapi import *


with open('static/restrictions_data.json', 'r') as infile:
    r_data = json.load(infile)

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', r_data=r_data)



try:
    flights = amadeus.shopping.flight_offers_search.get(
        originLocationCode='SEA', 
        destinationLocationCode='PDX',
        departureDate='2020-07-01', 
        adults=1,
        currencyCode="USD")
    cheapest_flight = flights.data[0]
    #print(cheapest_flight)
    # un-comment the code below to write the data to a json file for easier viewing!
    # with open ('flight.json', 'w') as outfile:
    #     json.dump(cheapest_flight, outfile)
except ResponseError as error:
    raise error


if __name__ == '__main__':
    app.run(debug=True)