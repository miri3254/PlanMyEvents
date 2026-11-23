import requests

# Test Products API
print("Testing Products API...")
r = requests.get('http://localhost:8000/api/products', params={'limit': 500})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"✅ Products API: {data['total']} products loaded successfully")
    print(f"   Sample units: {[p['unit'] for p in data['items'][:5]]}")
else:
    print(f"❌ Products API failed: {r.text[:200]}")

print()

# Test Dishes API
print("Testing Dishes API...")
r = requests.get('http://localhost:8000/api/dishes', params={'is_active': True, 'limit': 50})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"✅ Dishes API: {data['total']} dishes loaded successfully")
    if data['items']:
        dish = data['items'][0]
        print(f"   Sample dish: {dish['name']}")
        print(f"   Ingredients: {len(dish['ingredients'])} items")
        if dish['ingredients']:
            ing = dish['ingredients'][0]
            print(f"   First ingredient: {ing['name']}, product_id={ing['product_id']}")
else:
    print(f"❌ Dishes API failed: {r.text[:200]}")

print()
print("=" * 60)
print("ALL TESTS PASSED ✅" if all([
    requests.get('http://localhost:8000/api/products', params={'limit': 500}).status_code == 200,
    requests.get('http://localhost:8000/api/dishes', params={'is_active': True}).status_code == 200
]) else "SOME TESTS FAILED ❌")
