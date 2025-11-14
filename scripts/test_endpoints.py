import requests

endpoints = [
    '/api/active-passengers',
    '/api/passengers', 
    '/api/commuter-passengers',
    '/api/passenger'
]

print('Testing Strapi endpoints:')
print()

for ep in endpoints:
    try:
        r = requests.get(f'http://localhost:1337{ep}')
        print(f'{ep}: {r.status_code}')
        if r.status_code == 200:
            data = r.json()
            count = len(data.get('data', []))
            print(f'  → Found {count} records')
    except Exception as e:
        print(f'{ep}: ERROR - {e}')
