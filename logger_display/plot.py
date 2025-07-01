from flask import (
    Blueprint, render_template, url_for, current_app
)

from logger_display.db import get_db

bp = Blueprint('plot', __name__)

@bp.route('/', defaults={"ts":"48h"})
@bp.route('/<any(1h, 6h, 24h, 48h, 7d, 30d):ts>')
def index(ts):
    """Display the temperature plot for a given time frame.
    Args:
        ts (str): Time frame for the plot, e.g., '1h', '6h', '24h', '48h', '7d', '30d'.
    """
    data = get_data(ts)
    return render_template('plot/index.html', data=data, ts=ts)

    # Select data from different time frames
    # Automatically update data when inserted
    # Get ambient data from an API and update automatically or manually

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
    if data == None:
        return []
    return data

