from flask import Flask, jsonify, send_file, render_template
import pandas as pd
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

app = Flask(__name__)

INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "my-super-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "analytics_org")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "visits_bucket")

CSV_PATH = "/data/visits.csv"
OUTPUT_DIR = "/output"
FORECAST_PATH = os.path.join(OUTPUT_DIR, "forecast.png")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_client():
    return InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )


def build_forecast():
    df = pd.read_csv(CSV_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    daily = df.groupby(df["timestamp"].dt.date).size()
    daily.index = pd.to_datetime(daily.index)

    x = np.arange(len(daily))
    y = daily.values

    coeffs = np.polyfit(x, y, 1)
    trend = np.poly1d(coeffs)

    future_days = 7
    x_future = np.arange(len(daily) + future_days)
    y_future = trend(x_future)
    y_future = np.maximum(y_future, 0)

    dates_future = pd.date_range(
        start=daily.index.min(),
        periods=len(daily) + future_days
    )

    plt.figure(figsize=(12, 6))
    plt.plot(daily.index, y, marker="o", label="Фактические данные")
    plt.plot(dates_future, y_future, linestyle="--", label="Прогноз на 7 дней")
    plt.title("Прогноз посещаемости сайта")
    plt.xlabel("Дата")
    plt.ylabel("Количество посещений")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(FORECAST_PATH)
    plt.close()

    return {
        "historical_dates": [d.strftime("%Y-%m-%d") for d in daily.index],
        "historical_values": [int(v) for v in y],
        "forecast_dates": [d.strftime("%Y-%m-%d") for d in dates_future],
        "forecast_values": [round(float(v), 2) for v in y_future]
    }


def get_stats_data():
    df = pd.read_csv(CSV_PATH)

    return {
        "total_visits": int(len(df)),
        "unique_users": int(df["user_id"].nunique()),
        "avg_duration": round(float(df["duration"].mean()), 2),
        "top_pages": df["page"].value_counts().to_dict(),
        "top_sources": df["source"].value_counts().to_dict()
    }


@app.route("/")
def home():
    try:
        stats_result = get_stats_data()
        return render_template("index.html", stats=stats_result)
    except Exception as e:
        return f"Ошибка при загрузке главной страницы: {str(e)}", 500


@app.route("/load_data")
def load_data():
    try:
        df = pd.read_csv(CSV_PATH)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        client = get_client()
        write_api = client.write_api(write_options=SYNCHRONOUS)

        points = []
        for _, row in df.iterrows():
            point = (
                Point("visits")
                .tag("page", row["page"])
                .tag("source", row["source"])
                .field("user_id", int(row["user_id"]))
                .field("duration", int(row["duration"]))
                .time(row["timestamp"], WritePrecision.S)
            )
            points.append(point)

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
        client.close()

        return jsonify({
            "status": "success",
            "message": f"{len(df)} records loaded into InfluxDB"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/visits")
def visits():
    try:
        df = pd.read_csv(CSV_PATH)
        return df.to_json(orient="records")
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/stats")
def stats():
    try:
        return jsonify(get_stats_data())
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/forecast")
def forecast():
    try:
        build_forecast()
        return send_file(FORECAST_PATH, mimetype="image/png")
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/forecast_data")
def forecast_data():
    try:
        return jsonify(build_forecast())
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
