import requests
import json

r = requests.get('http://localhost:1337/api/active-passengers?pagination[pageSize]=1000')
data = r.json()
passengers = data.get('data', [])
print(f'Found {len(passengers)} passengers to delete')

deleted = 0
failed = 0
for p in passengers:
    doc_id = p.get('documentId')  # Try documentId instead of id
    pid = p['id']
    passenger_id = p.get('passenger_id', '?')
    print(f'  {passenger_id}: id={pid}, documentId={doc_id}')
    
    # Try with documentId
    try:
        dr = requests.delete(f'http://localhost:1337/api/active-passengers/{doc_id}')
        if dr.status_code in [200, 204]:
            deleted += 1
            print(f'    [OK] Deleted')
        else:
            failed += 1
            print(f'    [FAIL] Status {dr.status_code}')
    except Exception as e:
        print(f'    [ERROR] {e}')
        failed += 1

print(f'\n[RESULT] Deleted: {deleted}')
print(f'[RESULT] Failed: {failed}')

# Verify
r2 = requests.get('http://localhost:1337/api/active-passengers?pagination[pageSize]=1000')
remaining = len(r2.json().get('data', []))
print(f'[RESULT] Remaining in DB: {remaining}')
