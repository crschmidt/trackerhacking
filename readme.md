hacky tools for managing your own Apple Find My bluetooth trackers.

 - pip install -r requirements.txt
 - Use https://gist.github.com/airy10/5205dc851fbd0715fcd7a5cdde25e7c8 to dump
   out your searchpartyd data.
 - Take a .plist file from OwnedBeacons and run: 
    `python3 run.py insert TrackerName uuid.plist`
 - Then run `python3 run.py history 1`

This will involve typing in your Apple account username and password, which will
then have information stored into ./account.json
