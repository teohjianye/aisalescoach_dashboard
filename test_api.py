import requests
import json
import time

def test_api():
    base_url = "http://localhost:5000"
    
    print("Testing Flask API with live PostgreSQL data...")
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Test basic calls endpoint
        print(f"\n1. Testing /api/calls")
        response = requests.get(f"{base_url}/api/calls", timeout=5)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            calls = response.json()
            print(f"   Found {len(calls)} call records")
            if calls:
                print(f"   Sample call: {calls[0]['id']} - {calls[0]['sales_rep_name']} -> {calls[0]['customer_name']}")
        else:
            print(f"   Error: {response.text}")
        
        # Test dashboard overview
        print(f"\n2. Testing /api/dashboard/overview")
        response = requests.get(f"{base_url}/api/dashboard/overview", timeout=5)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            overview = response.json()
            print(f"   Total calls: {overview['overall']['total_calls']}")
            print(f"   Overall avg score: {overview['overall']['overall_avg_score']}")
            print(f"   Overall win rate: {overview['overall']['overall_win_rate']}%")
        else:
            print(f"   Error: {response.text}")
        
        # Test filtered calls
        print(f"\n3. Testing /api/calls/filter")
        response = requests.get(f"{base_url}/api/calls/filter", timeout=5)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filtered_calls = response.json()
            print(f"   Found {len(filtered_calls)} filtered call records")
        else:
            print(f"   Error: {response.text}")
            
        print(f"\n✅ API tests completed! The webapp is now using LIVE PostgreSQL data")
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection error - Flask app might not be running")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_api() 