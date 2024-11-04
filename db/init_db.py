# sqlite DB initialization with "songSectionDataClean" table from kaggle csv

import sqlite3
import pandas as pd


database_name = "db/songs_database.db"
csv_file = "db/songSectionDataClean.csv"

conn = sqlite3.connect(database_name)
cursor = conn.cursor()

data = pd.read_csv(csv_file)

cursor.execute('''
DROP TABLE IF EXISTS songSectionDataClean;
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS songSectionDataClean (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_ INTEGER,
    extraneous INTEGER,
    name TEXT,
    artist TEXT,
    section TEXT,
    progression TEXT,
    end_diff INTEGER,
    unique_number INTEGER,
    diatonic_number INTEGER,
    extended_number INTEGER
);
''')

data.to_sql('songSectionDataClean', conn, if_exists='replace', index=False)

conn.close()
print("Data loaded")
