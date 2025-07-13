from flask import (
    Blueprint, render_template, g, current_app, request, jsonify
)
import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta
import pandas as pd
from logger_display.db import get_db

bp = Blueprint('plot', __name__)

@bp.route('/')
def index():
    """Display the temperature plot for a given time frame.
    """
    # Get timeframe from query parameter, default to 24h
    return render_template('plot/index.html')

    # Select data from different time frames
    # Automatically update data when inserted
    # Get ambient data from an API and update automatically or manually
@bp.route('/get_data/', defaults={'ts': '24h'})
@bp.route('/get_data/<any(1h, 6h, 24h, 48h, 7d, 30d):ts>')
def get_data(ts):
    translation = {
        "1h": "1 hours",
        "6h": "6 hours",
        "24h": "24 hours",
        "48h": "2 days",
        "7d": "7 days",
        "30d": "30 days"
    }
    db = get_db()
    # Fetch data from the database
    data = db.execute(
        "SELECT * FROM temps WHERE timestamp >= datetime('now', 'localtime', ?)", 
        (f'-{translation[ts]}',)
    ).fetchall()
    # Convert Row objects to a list of lists, where each row is timestamp, temperature
    timestamps = [row['timestamp'] for row in data]
    temperatures = [row['temperature'] for row in data]
    data = list(zip(timestamps, temperatures))
    if not data:
        return []
    return data

@bp.route('/get_ambient_data/', defaults={'start_date': None, 'end_date': None})
@bp.route('/get_ambient_data/<start_date>&<end_date>')
def get_ambient_data(start_date=None, end_date=None):
    """Fetch ambient temperature data from an external API."""
    if 'openmeteo' not in g:
        cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        g.openmeteo = openmeteo_requests.Client(session = retry_session)

    if not start_date or not end_date:
        # Default to last 7 days if no dates provided
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": -33.39233738295373,
        "longitude": -70.54954703029358,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m",
        "timezone": "America/Santiago"
    }
    
    try:
        responses = g.openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        
        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s"),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s"),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}
        hourly_data["temperature_2m"] = hourly_temperature_2m
        # remove entries with NaN values
        hourly_data = {
            "date": [d for d, t in zip(hourly_data["date"], hourly_data["temperature_2m"]) if pd.notna(t)],
            "temperature_2m": [t for t in hourly_data["temperature_2m"] if pd.notna(t)]
        }
        # Convert to list of [timestamp, temperature] pairs
        data = []
        for i, timestamp in enumerate(hourly_data["date"]):
            data.append([timestamp.isoformat(), float(hourly_data["temperature_2m"][i])])
        
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error fetching weather data: {e}")
        return jsonify([])