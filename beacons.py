import json
import math
import plistlib
import sqlite3
from datetime import datetime, timedelta
from findmy import FindMyAccessory
from findmy.reports import RemoteAnisetteProvider
from _login import get_account_sync
import logging
import pytz

ANISETTE_SERVER = "http://ani.sternserv.xyz"

logging.basicConfig(level=logging.INFO)


# Constants
db_filename = "beacon_tracker.db"

def initialize_database():
    """Initialize the database if it does not already exist."""
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    # Create Beacons table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Beacons (
        id INTEGER PRIMARY KEY,
        uuid TEXT NOT NULL,
        name TEXT NOT NULL,
        master_key TEXT NOT NULL,
        skn TEXT NOT NULL,
        sks TEXT NOT NULL,
        paired_at TIMESTAMP NOT NULL
    )
    ''')

    # Create Observations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Observations (
        beacon_id INTEGER NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        horizontal_accuracy INTEGER NOT NULL,
        PRIMARY KEY (beacon_id),
        FOREIGN KEY (beacon_id) REFERENCES Beacons(id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    conn.close()

def update_observation_keyreport(beacon_id, report):
    update_observation(beacon_id, report.timestamp, report.latitude, report.longitude, 0) # report.horizontal_accuracy)

def update_observation(beacon_id, timestamp, latitude, longitude, horizontal_accuracy):
    """Update the observation for a given Beacon."""
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO Observations (beacon_id, timestamp, latitude, longitude, horizontal_accuracy)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(beacon_id) DO UPDATE SET
        timestamp=excluded.timestamp,
        latitude=excluded.latitude,
        longitude=excluded.longitude,
        horizontal_accuracy=excluded.horizontal_accuracy
    ''', (beacon_id, timestamp, latitude, longitude, horizontal_accuracy))

    conn.commit()
    conn.close()

def insert_beacon(name, master_key, skn, sks, paired_at, uuid):
    """Insert a new Beacon into the database and return its ID."""
    initialize_database()
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO Beacons (uuid, name, master_key, skn, sks, paired_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (uuid, name, master_key, skn, sks, paired_at))

    beacon_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return beacon_id

def insert_from_plist(name, filename):
    plist_data = plistlib.load(open(filename,"rb"))
    beacon = {
    'uuid': plist_data['identifier'],
    'paired_at': plist_data['pairingDate'],
    'master_key': plist_data["privateKey"]["key"]["data"][-28:].hex(),
    'skn': plist_data["sharedSecret"]["key"]["data"].hex(),
    'sks': plist_data["secondarySharedSecret"]["key"]["data"].hex(),
    'name': name
    }
    return insert_beacon(**beacon)

def get_latest_observation(beacon_id, update=False):
    if update:
        update_latest_observation(beacon_id)
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute("SELECT * from observations where beacon_id=?", [int(beacon_id)])
    data = cursor.fetchone()
    return data

def update_latest_observation(beacon_id):
    tracker = fetch_tracker(beacon_id)
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp from observations where beacon_id=?", [int(beacon_id)])
    data = cursor.fetchone()
    hours = 7*24
    if data:
        last_update = datetime.fromisoformat(data[0]).astimezone()
        last_delta = datetime.now().astimezone() - last_update
        hours = math.ceil(float(last_delta.total_seconds())/3600)
    reports = query_apple(tracker, hours)
    if len(reports):
        latest = reports[-1]
        update_observation_keyreport(beacon_id, latest)
 
def fetch_tracker(beacon_id):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute("SELECT paired_at, master_key, skn, sks from beacons where id=?", [int(beacon_id)])
    [paired_at, master_key, skn, sks] = cursor.fetchone()
    local_paired = datetime.fromisoformat(paired_at).astimezone()
    tracker = FindMyAccessory(master_key=bytes.fromhex(master_key), skn=bytes.fromhex(skn), 
                    sks=bytes.fromhex(sks), paired_at=local_paired)
    return tracker
       
def query_apple(tracker, hours):
    anisette = RemoteAnisetteProvider(ANISETTE_SERVER)
    acc = get_account_sync(anisette)
    all_reports = acc.fetch_last_reports(tracker, hours=hours)
    return sorted(all_reports)

def history(beacon_id):
    tracker = fetch_tracker(beacon_id)
    reports = query_apple(tracker, 7*24)
    return reports

def update_beacons():
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute("SELECT id from beacons")
    for i in cursor.fetchall():
        update_latest_observation(i[0])
        print(i)

def reports_to_geojson(reports):
    geo = {'type': 'LineString', 'coordinates': []}
    for i in reports:
        geo['coordinates'].append([i.longitude, i.latitude])
    return geo        

def history_geojson(beacon_id):
    return json.dumps(reports_to_geojson(history(beacon_id)))
