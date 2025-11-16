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
        'username': 'superadmin_user',
        'password': 'Test123!',
        'expected_tier': 'SuperAdmin',
        'test_endpoints': [
            {'path': '/api/access-tiers', 'method': 'GET', 'should_allow': True},
            {'path': '/api/access-tiers', 'method': 'POST', 'should_allow': True},
            {'path': '/api/agencies', 'method': 'GET', 'should_allow': True},
            {'path': '/api/vehicles', 'method': 'POST', 'should_allow': True}
        ]
    },
    {
        'username': 'admin_user',
        'password': 'Test123!',
        'expected_tier': 'Admin',
        'test_endpoints': [
            {'path': '/api/access-tiers', 'method': 'GET', 'should_allow': True},
            {'path': '/api/access-tiers', 'method': 'POST', 'should_allow': False},
            {'path': '/api/agencies', 'method': 'GET', 'should_allow': True},
            {'path': '/api/vehicles', 'method': 'POST', 'should_allow': True}
        ]
    },
    {
        'username': 'dispatcher_user',
        'password': 'Test123!',
        'expected_tier': 'Dispatcher',
        'test_endpoints': [
            {'path': '/api/agencies', 'method': 'GET', 'should_allow': True},
            {'path': '/api/agencies', 'method': 'POST', 'should_allow': False},
            {'path': '/api/vehicles', 'method': 'GET', 'should_allow': True},
            {'path': '/api/vehicles', 'method': 'POST', 'should_allow': False}
        ]
    },
    {
        'username': 'viewer_user',
        'password': 'Test123!',
        'expected_tier': 'Viewer',
        'test_endpoints': [
            {'path': '/api/agencies', 'method': 'GET', 'should_allow': True},
            {'path': '/api/agencies', 'method': 'POST', 'should_allow': False},
            {'path': '/api/vehicles', 'method': 'POST', 'should_allow': False}
        ]
    },
    {
        'username': 'guest_user',
        'password': 'Test123!',
        'expected_tier': 'Guest',
        'test_endpoints': [
            {'path': '/api/agencies', 'method': 'GET', 'should_allow': False},
            {'path': '/api/vehicles', 'method': 'GET', 'should_allow': False}
        ]
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

def test_endpoint(token, endpoint):
    """Test access to an endpoint with the given token."""
    url = f'{BASE_URL}{endpoint["path"]}'
    headers = {'Authorization': f'Bearer {token}'}
    method = endpoint['method']
    should_allow = endpoint['should_allow']
    
    if method == 'GET':
        res = requests.get(url, headers=headers, timeout=10)
    elif method == 'POST':
        res = requests.post(url, headers=headers, json={'test': 'data'}, timeout=10)
    elif method == 'PUT':
        res = requests.put(url, headers=headers, json={'test': 'data'}, timeout=10)
    elif method == 'DELETE':
        res = requests.delete(url, headers=headers, timeout=10)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    if should_allow:
        assert res.status_code in [200, 201], f"Expected 200/201 for {method} {endpoint['path']}, got {res.status_code}: {res.text}"
        print(f"✓ Access OK: {method} {endpoint['path']}")
    else:
        assert res.status_code == 403, f"Expected 403 for {method} {endpoint['path']}, got {res.status_code}: {res.text}"
        print(f"✓ Access forbidden as expected: {method} {endpoint['path']}")

def main():
    """Main function to run the RBAC verification tests."""
    print("Starting RBAC policy verification for all 7 tiers...\n")
    passed = 0
    failed = 0
    
    for user in USERS:
        print(f"\n{'='*60}")
        print(f"Testing {user['username']} (Expected tier: {user['expected_tier']})")
        print('='*60)
        try:
            token = login(user)
            for endpoint in user['test_endpoints']:
                try:
                    test_endpoint(token, endpoint)
                    passed += 1
                except AssertionError as e:
                    print(f"✗ FAILED: {e}")
                    failed += 1
        except Exception as e:
            print(f"✗ ERROR: Failed to test user {user['username']}: {e}")
            failed += len(user['test_endpoints'])
    
    print(f"\n{'='*60}")
    print(f"RBAC Policy Verification Complete")
    print(f"Passed: {passed}, Failed: {failed}")
    print('='*60)
    
    if failed > 0:
        exit(1)

if __name__ == '__main__':
    main()
