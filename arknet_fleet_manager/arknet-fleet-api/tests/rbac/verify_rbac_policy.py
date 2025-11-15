"""
Standalone RBAC Policy Verification Script
Task 4419: Test policy enforcement for all tiers

Usage:
  python verify_rbac_policy.py

Requires:
  pip install requests pyjwt
"""
import requests
import jwt

BASE_URL = 'http://localhost:1337'
USERS = [
    {
        'username': 'david',
        'password': 'Ga25w123!',
        'expected_tier': 'Admin',
        'allowed_routes': ['/admin'],
        'forbidden_routes': []
    }
]

def login(user):
    """Login the user and return the JWT token."""
    res = requests.post(f'{BASE_URL}/api/auth/local', json={
        'identifier': user['username'],
        'password': user['password']
    }, timeout=10)
    res.raise_for_status()
    token = res.json()['jwt']
    decoded = jwt.decode(token, options={"verify_signature": False})
    assert decoded['tier'] == user['expected_tier'], f"Tier mismatch for {user['username']}"
    print(f"{user['username']} login OK, tier: {decoded['tier']}")
    return token

def test_route(token, route, should_allow):
    """Test access to a route with the given token."""
    url = f'{BASE_URL}{route}'
    headers = {'Authorization': f'Bearer {token}'}
    res = requests.get(url, headers=headers, timeout=10)
    if should_allow:
        assert res.status_code == 200, f"Expected 200 for {route}, got {res.status_code}"
        print(f"Access OK: {route}")
    else:
        assert res.status_code == 403, f"Expected 403 for {route}, got {res.status_code}"
        print(f"Access forbidden as expected: {route}")

def main():
    """Main function to run the RBAC verification tests."""
    for user in USERS:
        print(f"\nTesting {user['username']}...")
        token = login(user)
        for route in user['allowed_routes']:
            test_route(token, route, True)
        for route in user['forbidden_routes']:
            test_route(token, route, False)
    print("\nRBAC policy verification complete.")

if __name__ == '__main__':
    main()
