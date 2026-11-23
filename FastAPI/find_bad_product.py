import requests

print("Finding problematic product...")

for skip in range(0, 120, 10):
    r = requests.get('http://localhost:8000/api/products', params={'limit': 10, 'skip': skip})
    if r.status_code != 200:
        print(f"❌ Issue in range skip={skip} to {skip+10}")
        
        # Narrow down to specific product
        for i in range(skip, skip + 10):
            r = requests.get('http://localhost:8000/api/products', params={'limit': 1, 'skip': i})
            if r.status_code != 200:
                print(f"   🔴 Product at skip={i} (ID likely {i+1}) causes 500 error")
                break
        break
    else:
        data = r.json()
        units = set([p['unit'] for p in data['items']])
        print(f"✅ Skip {skip:3d}-{skip+9:3d}: OK (units: {units})")
