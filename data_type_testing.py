import sqlite3
import csv
from pprint import pprint


# Connect to the database (if it doesn't exist, it will be created in the folder that your notebook is in):
sqlite_file = 'mydbb.db'    # name of the sqlite database file

# Connect to the database
conn = sqlite3.connect(sqlite_file)

# Create a cursor object , Get a cursor object
cur = conn.cursor()

# Create the table.
#In this case, I am using 'nodes_tags.csv' as an example, it has columns: 'id, key, value,type'
#Create the table, specifying the column names and data types:
cur.execute('''
    CREATE TABLE nodes( 
    id INTEGER PRIMARY KEY NOT NULL,
    lat REAL,
    lon REAL,
    user TEXT,
    uid INTEGER,
    version INTEGER,
    changeset INTEGER,
    timestamp TEXT)
''')
# commit the changes
conn.commit()

# Read in the csv file as a dictionary, format the
# data as a list of tuples:
with open('nodes.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['id'], i['lat'],i['lon'], i['user'], i['uid'],i['version'], i['changeset'],i['timestamp']) for i in dr]

# insert the formatted data
cur.executemany("INSERT INTO nodes(id,lat,lon,user,uid,version,changeset,timestamp) VALUES (?, ?, ?, ?,?,?,?,?);", to_db)
# commit the changes
conn.commit()

cur.execute('SELECT * FROM nodes_tags')
all_rows = cur.fetchall()
print('1):')
pprint(all_rows)

conn.close()    