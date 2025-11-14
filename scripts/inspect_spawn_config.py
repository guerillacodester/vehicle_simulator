import requests, json
url = 'http://localhost:1337/api/spawn-configs?filters[route][short_name][$eq]=1&populate=*'
r = requests.get(url)
js = r.json()
print('status', r.status_code)
if 'data' in js and js['data']:
    rec = js['data'][0]
    print('\nTOP-LEVEL KEYS:', list(rec.keys()))
    if isinstance(rec.get('attributes'), dict):
        print('ATTRIBUTES KEYS:', list(rec['attributes'].keys()))
    # Pretty print a trimmed version
    s = json.dumps(rec, indent=2)
    print('\nPREVIEW:\n', s[:1600])
else:
    print('no spawn config')
