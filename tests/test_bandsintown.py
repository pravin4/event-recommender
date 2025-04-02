import os
import sys
import json
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_bandsintown():
    """Test the Bandsintown API with a list of artists"""
    print("Testing Bandsintown API...")
    
    # Get API key from environment
    app_id = os.getenv("BANDSINTOWN_API_KEY")
    if not app_id:
        print("Error: BANDSINTOWN_API_KEY not found in environment variables")
        return
    
    # Test location
    location = "San Francisco, CA"
    
    # List of popular artists across genres
    artists = [
        # Pop
        "Taylor Swift", "Ed Sheeran", "The Weeknd",
        # Rock
        "Foo Fighters", "Red Hot Chili Peppers", "Arctic Monkeys",
        # Hip Hop
        "Kendrick Lamar", "Drake", "Travis Scott",
        # Electronic
        "Odesza", "Flume", "Disclosure",
        # Alternative
        "The National", "Arcade Fire", "The Strokes",
        # R&B
        "SZA", "Frank Ocean", "Daniel Caesar",
        # Country
        "Luke Combs", "Morgan Wallen", "Chris Stapleton"
    ]
    
    print(f"\nFetching events for {len(artists)} artists in {location}")
    
    all_events = []
    for artist in artists:
        try:
            # Make API request
            url = f"https://rest.bandsintown.com/artists/{artist}/events"
            params = {
                "app_id": app_id,
                "date": "upcoming"
            }
            
            print(f"\nRequesting events for {artist}...")
            response = requests.get(url, params=params)
            
            if response.status_code == 404:
                print(f"No events found for {artist}")
                continue
                
            response.raise_for_status()
            events = response.json()
            
            # Filter events by location
            for event in events:
                venue = event.get("venue", {})
                event_location = f"{venue.get('city', '')}, {venue.get('region', '')}"
                
                if location.lower() in event_location.lower():
                    all_events.append({
                        "artist": artist,
                        "name": event.get("title", ""),
                        "date": event.get("datetime", ""),
                        "venue": venue.get("name", ""),
                        "location": event_location,
                        "url": event.get("url", "")
                    })
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching events for {artist}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response text: {e.response.text}")
            continue
    
    # Print results
    print(f"\nFound {len(all_events)} events in {location}")
    
    if all_events:
        print("\nFirst few events:")
        for i, event in enumerate(sorted(all_events, key=lambda x: x["date"])[:5]):
            print(f"\nEvent {i+1}:")
            print(f"  Artist: {event['artist']}")
            print(f"  Name: {event['name']}")
            print(f"  Date: {event['date']}")
            print(f"  Venue: {event['venue']}")
            print(f"  Location: {event['location']}")
            print(f"  URL: {event['url']}")

if __name__ == "__main__":
    test_bandsintown() 