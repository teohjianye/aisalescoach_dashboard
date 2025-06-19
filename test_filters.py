#!/usr/bin/env python3
from app import app
import json

def test_filters():
    with app.test_client() as client:
        print("Testing filter functionality:")
        
        # Test overview with no filters
        response = client.get('/api/dashboard/overview')
        print(f"1. Overview (no filter): Status {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"   Call types: {len(data['call_types'])}")
            print(f"   Total calls: {data['overall']['total_calls']}")
        
        # Test overview filtered by call type
        response = client.get('/api/dashboard/overview?call_type=Phone Call')
        print(f"2. Overview (Phone Call filter): Status {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"   Call types: {len(data['call_types'])}")
            if data['call_types']:
                print(f"   Call type: {data['call_types'][0]['call_type']}")
                print(f"   Phone calls count: {data['call_types'][0]['call_count']}")
        
        # Test overview filtered by outcome
        response = client.get('/api/dashboard/overview?outcome=Won')
        print(f"3. Overview (Won outcome filter): Status {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"   Call types: {len(data['call_types'])}")
            print(f"   Total won calls: {data['overall']['total_won']}")
        
        # Test call history filters
        response = client.get('/api/calls/filter?call_type=Google Meet')
        print(f"4. Call history (Google Meet filter): Status {response.status_code}")
        if response.status_code == 200:
            calls = json.loads(response.data)
            print(f"   Google Meet calls: {len(calls)}")
            if calls:
                print(f"   First call type: {calls[0]['call_type']}")
        
        # Test combined filters
        response = client.get('/api/calls/filter?call_type=Zoom&outcome=Won')
        print(f"5. Call history (Zoom + Won filter): Status {response.status_code}")
        if response.status_code == 200:
            calls = json.loads(response.data)
            print(f"   Zoom Won calls: {len(calls)}")
        
        # Test sales rep filter
        response = client.get('/api/calls/filter?sales_rep=John Smith')
        print(f"6. Call history (John Smith filter): Status {response.status_code}")
        if response.status_code == 200:
            calls = json.loads(response.data)
            print(f"   John Smith calls: {len(calls)}")
            if calls:
                print(f"   First call rep: {calls[0]['sales_rep_name']}")

if __name__ == "__main__":
    test_filters() 