import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# параметры
NUM_RECORDS = 500

# возможные значения
pages = ['/home', '/product', '/cart', '/about', '/contact']
sources = ['organic', 'ads', 'direct', 'social']

data = []

start_date = datetime.now() - timedelta(days=30)

for i in range(NUM_RECORDS):
    # случайная дата за последние 30 дней
    random_days = random.randint(0, 29)
    
    # моделируем пики активности (вечером больше трафика)
    hour = int(np.random.normal(loc=19, scale=3))
    hour = max(0, min(23, hour))
    
    minute = random.randint(0, 59)
    
    timestamp = start_date + timedelta(days=random_days, hours=hour, minutes=minute)
    
    user_id = random.randint(1, 100)
    
    page = random.choices(
        pages,
        weights=[30, 25, 15, 15, 15]
    )[0]
    
    source = random.choices(
        sources,
        weights=[40, 25, 20, 15]
    )[0]
    
    # время на сайте (секунды)
    duration = max(5, int(np.random.normal(loc=120, scale=50)))
    
    data.append([
        user_id,
        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        page,
        duration,
        source
    ])

df = pd.DataFrame(data, columns=[
    'user_id',
    'timestamp',
    'page',
    'duration',
    'source'
])

# сортируем по времени (важно для аналитики)
df = df.sort_values(by='timestamp')

# сохраняем
df.to_csv('visits.csv', index=False)

print("CSV файл успешно создан: visits.csv")
