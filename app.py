from flask import Flask, render_template, url_for
import json

with open('static/restrictions_data.json', 'r') as infile:
    r_data = json.load(infile)

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', r_data=r_data)

if __name__ == '__main__':
    app.run(debug=True)