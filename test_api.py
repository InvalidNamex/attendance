"""
Test script for Attendance API
Run this after starting the server: uvicorn main:app --reload
"""
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def test_root():
    """Test root endpoint (no auth required)"""
    print("\n=== Testing Root Endpoint ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_login():
    """Test login endpoint"""
    print("\n=== Testing Login ===")
    auth = HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)
    response = requests.post(f"{BASE_URL}/users/login", auth=auth)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_get_settings():
    """Test get settings"""
    print("\n=== Testing Get Settings ===")
    auth = HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)
    response = requests.get(f"{BASE_URL}/settings/", auth=auth)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_create_user():
    """Test create user (admin only)"""
    print("\n=== Testing Create User ===")
    auth = HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)
    user_data = {
        "userName": "testuser",
        "password": "test123",
        "deviceID": "device001",
        "isAdmin": False
    }
    response = requests.post(f"{BASE_URL}/users/", json=user_data, auth=auth)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 201

def test_get_users():
    """Test get all users"""
    print("\n=== Testing Get All Users ===")
    auth = HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)
    response = requests.get(f"{BASE_URL}/users/", auth=auth)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_update_settings():
    """Test update settings (admin only)"""
    print("\n=== Testing Update Settings ===")
    auth = HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)
    settings_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "radius": 200,
        "in_time": "08:30",
        "out_time": "17:30"
    }
    response = requests.put(f"{BASE_URL}/settings/", json=settings_data, auth=auth)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_create_transaction():
    """Test create transaction"""
    print("\n=== Testing Create Transaction (without photo) ===")
    auth = HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)
    transaction_data = {
        "stamp_type": 0  # Check-in
    }
    response = requests.post(f"{BASE_URL}/transactions/", data=transaction_data, auth=auth)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 201

def test_get_transactions():
    """Test get transactions"""
    print("\n=== Testing Get Transactions ===")
    auth = HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)
    response = requests.get(f"{BASE_URL}/transactions/", auth=auth)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_unauthorized():
    """Test unauthorized access"""
    print("\n=== Testing Unauthorized Access ===")
    auth = HTTPBasicAuth("wrong", "credentials")
    response = requests.post(f"{BASE_URL}/users/login", auth=auth)
    print(f"Status: {response.status_code}")
    print(f"Expected: 401 Unauthorized")
    return response.status_code == 401

if __name__ == "__main__":
    print("=" * 50)
    print("Attendance API Test Suite")
    print("=" * 50)
    
    tests = [
        ("Root Endpoint", test_root),
        ("Admin Login", test_login),
        ("Get Settings", test_get_settings),
        ("Create User", test_create_user),
        ("Get All Users", test_get_users),
        ("Update Settings", test_update_settings),
        ("Create Transaction", test_create_transaction),
        ("Get Transactions", test_get_transactions),
        ("Unauthorized Access", test_unauthorized),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"Error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed_count}/{total} tests passed")
