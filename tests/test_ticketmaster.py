from event_apis import TicketmasterAPI
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json

load_dotenv()

def test_ticketmaster():
    print("Testing Ticketmaster API...")
    api_key = os.getenv("TICKETMASTER_API_KEY")
    if not api_key:
        print("Error: TICKETMASTER_API_KEY not found in environment variables")
        return

    api = TicketmasterAPI(api_key)
    
    # Test parameters
    zip_code = "90210"  # Beverly Hills
    interests = ["art", "museum", "exhibit"]  # Interests related to the events we saw
    
    # Get current date and format it properly
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    
    print(f"\nTesting events for Beverly Hills (90210) in the next 30 days")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Interests: {', '.join(interests)}")
    
    try:
        # Make the API request directly to see the raw response
        params = {
            "apikey": api_key,
            "postalCode": zip_code,
            "radius": "50",
            "unit": "miles",
            "startDateTime": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endDateTime": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "size": 100,
            "sort": "date,asc"
        }
        
        print(f"\nRequest URL: https://app.ticketmaster.com/discovery/v2/events.json")
        print(f"Request params: {json.dumps(params, indent=2)}")
        
        import requests
        response = requests.get("https://app.ticketmaster.com/discovery/v2/events.json", params=params)
        print(f"\nResponse status code: {response.status_code}")
        data = response.json()
        
        # Print total number of events
        total_events = data.get("page", {}).get("totalElements", 0)
        print(f"\nTotal events found: {total_events}")
        
        # Now test the API class with interests
        events = api.fetch_events(zip_code, interests)
        print(f"\nFound {len(events)} events matching interests")
        if events:
            print("\nFirst event details:")
            event = events[0]
            print(f"Name: {event.name}")
            print(f"Date: {event.date}")
            print(f"Location: {event.location}")
            print(f"Price: {event.price}")
            print(f"URL: {event.url}")
            print(f"Categories: {', '.join(event.categories)}")
        else:
            print("\nNo events found matching the specified interests")
            
    except Exception as e:
        print(f"Error during API test: {str(e)}")

if __name__ == "__main__":
    test_ticketmaster() 