import sqlite3, random
from datetime import datetime, timedelta

conn = sqlite3.connect("rfid")
cursor = conn.cursor()

for i in range(0, 100):
    start_date = datetime.strptime('2024-02-08', '%Y-%m-%d')
    end_date = datetime.strptime('2024-03-08', '%Y-%m-%d')
    date_range = (end_date - start_date).days
    random_days = random.randint(0, date_range)
    random_date = start_date + timedelta(days=random_days)
    random_date = random_date.strftime('%Y-%m-%d')
    cursor.execute('''INSERT INTO Booking (facility_id, user_id, timeslot_id, booking_date, approved)
                   VALUES (?, ?, ?, ?, ?);''',
                   (random.randint(1, 6), f'S{random.randint(1, 9)}{random.randint(1, 9)}{random.randint(1, 9)}{random.randint(1, 9)}', random.randint(1, 270), random_date, random.choice((0, 1, None))))
conn.commit()
conn.close()
