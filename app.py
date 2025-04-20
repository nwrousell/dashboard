from datetime import timedelta
from flask import Flask, render_template, request, jsonify

from database import Database
from util import get_start_of_week, get_timeperiods

DB_PATH = "./data.db"

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/query", methods=["GET"])
def execute_sql():
    table = "computer_use"
    metric = "duration"
    start_of_week = get_start_of_week()
    time_periods = get_timeperiods(start_of_week, timedelta(days=1), 7)
    group_by_column = "category"
    with Database() as db:
        result = db.query(table, metric, time_periods, "sum", group_by_column)

    days = {}
    for row in result:
        iso_str = row["timeperiod"].split(" ")[0]
        if iso_str not in days:
            days[iso_str] = {}
        days[iso_str][row["group"]] = round((row["value"] // 60) / 60, 2)

    print(days)

    return days


if __name__ == "__main__":
    app.run(debug=True)
