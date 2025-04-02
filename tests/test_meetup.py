import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
from dotenv import load_dotenv
from src.api.event_apis import MeetupAPI

# Load environment variables
load_dotenv()

def test_meetup():
    """Test the Meetup API with a simple request"""
    print("Testing Meetup API...")
    
    # Get API key from environment
    api_key = os.getenv("MEETUP_API_KEY")
    if not api_key:
        print("Error: MEETUP_API_KEY not found in environment variables")
        return
    
    # Create API client
    meetup_api = MeetupAPI(api_key)
    
    # Test location and interests
    location = "San Francisco, CA"
    interests = ["tech", "coding", "programming"]
    
    print(f"\nFetching events for location: {location}")
    print(f"Interests: {interests}")
    
    # Fetch events
    events = meetup_api.fetch_events(location, interests)
    
    # Print results
    print(f"\nFound {len(events)} events")
    
    if events:
        print("\nFirst few events:")
        for i, event in enumerate(events[:5]):
            print(f"\nEvent {i+1}:")
            print(f"  Name: {event.name}")
            print(f"  Date: {event.date}")
            print(f"  Location: {event.location}")
            print(f"  Price: {event.price}")
            print(f"  URL: {event.url}")
            print(f"  Categories: {', '.join(event.categories)}")
    else:
        print("\nNo events found")

if __name__ == "__main__":
    test_meetup() 