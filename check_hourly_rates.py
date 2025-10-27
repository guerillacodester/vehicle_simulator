import requests

r = requests.get('http://localhost:1337/api/spawn-configs?filters[name][$eq]=Route 1 - St Lucy Rural&populate[hourly_spawn_rates]=*')
data = r.json()['data'][0]
rates = sorted(data.get('hourly_spawn_rates', []), key=lambda x: x['hour'])

print('Hourly spawn rates for Route 1 - St Lucy Rural:')
print('\nMorning hours:')
for hr in rates:
    if hr['hour'] in [6, 7, 8, 9, 10, 11, 12]:
        print(f"  Hour {hr['hour']:2d}: {hr['spawn_rate']}")
