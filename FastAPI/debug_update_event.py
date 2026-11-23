"""
Debug script to test the event update API
"""
import urllib.request
import urllib.error
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

# First, get existing events
print("[*] Fetching events...")
try:
    with urllib.request.urlopen(f"{BASE_URL}/events") as resp:
        data = json.loads(resp.read().decode())
        print(f"Status: {resp.status}")
        
        if data.get("items"):
            event = data["items"][0]
            event_id = event["id"]
            print(f"[+] Found event ID: {event_id}")
            print(f"Current data: {json.dumps(event, indent=2, ensure_ascii=False)}")
            
            # Try to update the event
            # Filter out only the fields that the API accepts
            update_payload = {
                "name": event["name"],
                "menu_type": event["menu_type"],
                "date": event["date"],
                "event_time": event.get("event_time"),
                "guest_count": event["guest_count"],
                "is_real_dishes": event.get("is_real_dishes", False),
                "notes": event.get("notes"),
                "address": event.get("address"),
                "city": event.get("city"),
                # Only send the fields that EventOwnerCreate accepts
                "owners": [
                    {
                        "name": o["name"],
                        "phone": o.get("phone"),
                        "email": o.get("email"),
                        "order": o.get("order", 0)
                    }
                    for o in event.get("owners", [])
                ] if event.get("owners") else []
            }
            
            print(f"\n[*] Update payload:")
            print(json.dumps(update_payload, indent=2, ensure_ascii=False))
            
            print(f"\n[*] Sending PUT request...")
            payload_bytes = json.dumps(update_payload).encode('utf-8')
            
            req = urllib.request.Request(
                f"{BASE_URL}/events/{event_id}",
                data=payload_bytes,
                method='PUT',
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )
            
            try:
                with urllib.request.urlopen(req) as resp:
                    result = json.loads(resp.read().decode())
                    print(f"[+] Status: {resp.status}")
                    print(f"[+] SUCCESS! Response:")
                    print(json.dumps(result, indent=2, ensure_ascii=False)[:500] + "...")
            except urllib.error.HTTPError as e:
                print(f"[-] Status: {e.code}")
                error_data = json.loads(e.read().decode())
                print(f"[-] Error: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        else:
            print("[-] No events found")
            
except Exception as e:
    print(f"[-] Exception: {e}")
    import traceback
    traceback.print_exc()
