# Find My trackers use a rotating public key, with key rotation every 15
# minutes from when the device was initially paired. In theory, this allows a
# consumer to generate the correct key for any time period with the private key
# and the date the device was first paired.
#
# In practice, it seems like when a Eufy Smart Track Link device has a dead
# battery, its sequence will stop updating, and therefore it will be come
# disconnected from the "correct" sequence computed from the PairedAt date.
#
# Apple tracks recent ID Sequence + timestamps in a secondary plist, stored
# under KeyAlignmentRecords in the searchpartyd directory; these are likely
# collected via the BTLE Keyroll_Indication indicator, which sends the KeyIndex
# from the accessory to a device (e.g. your phone) via a GATT subprocedure.
# However, for me in particular, the version of this data on my mac does not
# seem to always be up to date.
#
# This script is a hacky alternative:
#
#  - Generate one key per day (every 96th key, since key rotation period is 15
#    minutes)
#  - Query Apple's server for each key (in batches of 250)
#  - Once you've found records, compute the alignment between the returned
#    datestamp and the key you've generated

import sys
from datetime import datetime, timedelta
from findmy.reports import RemoteAnisetteProvider
from _login import get_account_sync
import beacons
import pytz

ANISETTE_SERVER = "http://ani.sternserv.xyz"

# 40,000 is about 16 months.
def run(beacon_id, max_idx=40000):

    keys = []
    tracker = beacons.fetch_tracker(beacon_id)
    for i in range(0, max_idx, 50):
        for key in tracker.keys_at(i):
            key.idx=i
            keys.append(key)
    anisette = RemoteAnisetteProvider(ANISETTE_SERVER)
    acc = get_account_sync(anisette)
    reports = acc.fetch_reports(list(keys), datetime.now(), datetime.now()) 
    print(reports)
    min_key = 9999999
    max_key = 0
    for key in reports:
        print("hi")
        if len(reports[key]) > 0:
            print(reports[key])
            if key.idx < min_key: min_key = key.idx
            if key.idx > max_key: max_key = key.idx
    print("found idx in range", min_key, max_key)
    keys = []
    for i in range(min_key, min_key+96):
        for key in tracker.keys_at(i):
            key.idx=i
            keys.append(key)
    min = datetime.now().astimezone()
    reports = acc.fetch_reports(keys, datetime.now(), datetime.now()) 
    for key in reports:
        for detection in reports[key]:    
            estimate = detection.timestamp - timedelta(minutes=15*key.idx)
            if estimate < min:
                min = estimate
    print(min.astimezone(pytz.UTC).replace(tzinfo=None).isoformat())
    
if __name__ == "__main__":
    beacon_id = sys.argv[1]
    run(int(beacon_id))
