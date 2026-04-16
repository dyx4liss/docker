import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

DATA_PATH = "../data/visits.csv"
OUTPUT_DIR = "../output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# загрузка данных
df = pd.read_csv(DATA_PATH)
df["timestamp"] = pd.to_datetime(df["timestamp"])

# агрегируем по дням
daily = df.groupby(df["timestamp"].dt.date).size()
daily.index = pd.to_datetime(daily.index)

# -----------------------------
# Простая модель прогноза
# (линейный тренд)
# -----------------------------
x = np.arange(len(daily))
y = daily.values

# линейная регрессия
coeffs = np.polyfit(x, y, 1)
trend = np.poly1d(coeffs)

# прогноз на 7 дней вперед
future_days = 7
x_future = np.arange(len(daily) + future_days)

y_future = trend(x_future)

# даты
dates_future = pd.date_range(
    start=daily.index.min(),
    periods=len(daily) + future_days
)

# -----------------------------
# График
# -----------------------------
plt.figure(figsize=(12, 6))

# фактические данные
plt.plot(daily.index, y, label="Фактические данные", marker="o")

# прогноз
plt.plot(dates_future, y_future, linestyle="--", label="Прогноз")

plt.title("Прогноз посещаемости сайта")
plt.xlabel("Дата")
plt.ylabel("Количество посещений")
plt.legend()
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/forecast.png")
plt.close()

print("Прогноз построен: output/forecast.png")
