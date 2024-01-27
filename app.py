from flask import Flask, request, render_template
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import requests
import pandas as pd
from io import BytesIO
import base64
from dotenv import API_KEY


app = Flask(__name__)

# interacting with FRED API
class FredPy:
    def __init__(self, token=None):
        self.token = token
        self.url = "https://api.stlouisfed.org/fred/series/observations" + \
                    "?series_id={seriesID}&api_key={api_key}&file_type=json" + \
                    "&observation_start={start}&observation_end={end}&units={units}&frequency={frequency}"
    
    def set_token(self, token):
        self.token = token
    
    def get_series(self, seriesID, start, end, units, frequency):
        url_formatted = self.url.format(
            seriesID=seriesID,
            start=start,
            end=end,
            units=units,
            frequency=frequency,
            api_key=self.token
        )
        response = requests.get(url_formatted)

        if self.token:
            if response.status_code == 200:
                data = pd.DataFrame(response.json()['observations'])[['date', 'value']]\
                        .assign(date=lambda cols: pd.to_datetime(cols['date']))\
                        .assign(value=lambda cols: cols['value'].astype(float))\
                        .rename(columns={'value': seriesID})
                return data
            else:
                raise Exception("Bad response from API, status code = {}".format(response.status_code))
        else:
            raise Exception("You did not specify an API key.")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data', methods=['POST'])
def get_data():
    api_key = API_KEY
    fredpy = FredPy(api_key)

    series_id = request.form['series_id']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    units = request.form['units']
    frequency = request.form['frequency']

    data = fredpy.get_series(seriesID=series_id, start=start_date, end=end_date, units=units, frequency=frequency)

    # Generate plot
    plt.figure(figsize=(10, 6))
    plt.plot(data['date'], data[series_id])
    plt.title('Data from FRED API')
    plt.xlabel('Date')
    plt.ylabel(series_id)
    plt.grid(True)

    # Convert plot to base64
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template('display_data.html', plot_url=plot_url)  # Pass plot to template

if __name__ == '__main__':
    app.run(debug=True)
