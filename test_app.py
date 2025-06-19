#!/usr/bin/env python3
from app import app
import json

def test_app():
    with app.test_client() as client:
        # Test the main route
        print("Testing main route (/)")
        response = client.get('/')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error: {response.data}")
        else:
            print("Main route works!")
            
        # Test API endpoints
        print("\nTesting API endpoints:")
        
        # Test dashboard overview
        response = client.get('/api/dashboard/overview')
        print(f"Dashboard overview status: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"Call types: {len(data['call_types'])}")
            print(f"Sales reps: {len(data['sales_reps'])}")
        
        # Test calls endpoint
        response = client.get('/api/calls')
        print(f"Calls endpoint status: {response.status_code}")
        if response.status_code == 200:
            calls = json.loads(response.data)
            print(f"Total calls: {len(calls)}")

if __name__ == "__main__":
    test_app() 