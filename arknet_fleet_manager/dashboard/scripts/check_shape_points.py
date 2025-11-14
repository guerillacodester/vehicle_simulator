import requests

result = requests.post('http://localhost:1337/graphql', json={
    'query': '''
    query {
        shapes(filters: { shape_id: { eq: "17398c1d-45c9-4632-9608-eacf060fb836" } }) {
            shape_id
            shape_pt_sequence
        }
    }
    '''
}).json()

print(f"Points for shape 17398c1d-45c9-4632-9608-eacf060fb836: {len(result['data']['shapes'])}")
for pt in result['data']['shapes'][:5]:
    print(f"  seq={pt['shape_pt_sequence']}")
