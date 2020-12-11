# TravelAid-OSUHackathon

Try it out!
 https://travelaidapp.herokuapp.com

Team: Git Em

TravelAid is a web app where you can find all the most recent travel information and restrictions for each country in one place as well as the cheapest flight and pricing from your location to the country of your choice.

TravelAid gathers data daily that is provided in a CSV file from The Humanitarian Data Exchange (data.humdata.org). Users can select a country from a drop down menu and our client-side sends a request to our server-side app for the country's travel restrictions and COVID-19 rules in place. After that the user can choose to search flights by selecting any airport code from and origin dropdown and the destination dropdown is limited to the airport codes in the country that they have selected. Another request is sent to our server-side which sends a request to the flights API we used called Amadeus. We then query a file with all the airports to obtain the airport codes for each country. In order to get the airline name from the airline code, we send a request to another Amadeus API as well. The user can then view the cheapest flight from the origin to the destination of their choice.

None of our group members had used flask before so this proved to be a great opportunity to learn a new web framework.

Some challenges we faced included: Using GitHub to work together on the same files but after the initial struggle we were successful Getting country restrictions information to update automatically from a CSV file daily Displaying flights with multiple connections The flight API we used is a bit slow to display results Error handling was challenging, we tried to be comprehensive though

If we had more time we would make the flight search more comprehensive. It would display more results and theoretically the user would be able to filter the search by class, price, duration, stops, etc. We woud also improve our code organization. With more time we would explore additional Flask capabilites like asynchronous requests.

GitHub: https://github.com/Harmony222/TravelAid-OSUHackathon

Test out our app live on Heroku! https://travelaidapp.herokuapp.com/home

Built With: amadeus flight api, apscheduler, bootstrap, css, flask, heroku, html, javascript, json, python
