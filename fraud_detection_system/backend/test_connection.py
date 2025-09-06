"""
Script de prueba para verificar las APIs
backend/test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    print("=" * 50)
    print("PROBANDO ENDPOINTS DEL SISTEMA")
    print("=" * 50)
    
    # 1. Test Health
    print("\n1. Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # 2. Test Dashboard Stats
    print("\n2. Testing Dashboard Stats...")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Total Cases: {data.get('total_cases', 0)}")
        print(f"   Cases by Severity: {data.get('cases_by_severity', {})}")
        print(f"   Recent Cases: {len(data.get('recent_cases', []))}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # 3. Test Fraud Cases
    print("\n3. Testing Fraud Cases...")
    try:
        response = requests.get(f"{BASE_URL}/api/fraud-cases")
        print(f"   Status: {response.status_code}")
        cases = response.json()
        print(f"   Total cases returned: {len(cases)}")
        if cases:
            print(f"   First case: {cases[0].get('case_number', 'N/A')}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # 4. Test Available Detectors
    print("\n4. Testing Available Detectors...")
    try:
        response = requests.get(f"{BASE_URL}/api/detectors")
        print(f"   Status: {response.status_code}")
        detectors = response.json()
        print(f"   Detectors available: {len(detectors)}")
        for d in detectors:
            print(f"     - {d.get('name', 'Unknown')}: {d.get('enabled', False)}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # 5. Test Run Detection
    print("\n5. Testing Run Detection...")
    try:
        response = requests.post(f"{BASE_URL}/api/run-detection", json={})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success', False)}")
            print(f"   Cases detected: {data.get('cases_detected', 0)}")
            print(f"   Detectors run: {data.get('detectors_run', [])}")
        else:
            print(f"   Error Response: {response.text}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("PRUEBAS COMPLETADAS")
    print("=" * 50)

if __name__ == "__main__":
    test_endpoints()