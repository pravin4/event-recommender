from src.api.event_apis import EventAggregator, TicketmasterAPI, MeetupAPI, SeatGeekAPI, VividSeatsAPI
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import unittest
from unittest.mock import patch, MagicMock
import pytest

load_dotenv()

@pytest.mark.parametrize("api_name", ["ticketmaster", "meetup", "seatgeek", "vividseats"])
def test_api(api_name: str, zip_code: str = "90210", interests: list = ["music"]):
    print(f"\nTesting {api_name} API...")
    aggregator = EventAggregator()
    
    # Test only the specified API
    api = aggregator.apis.get(api_name)
    if not api:
        print(f"API {api_name} not found!")
        return
    
    try:
        events = api.fetch_events(zip_code, interests)
        print(f"Found {len(events)} events")
        for event in events:
            print(f"\nEvent: {event.name}")
            print(f"Date: {event.date}")
            print(f"Venue: {event.venue}")
            print(f"Price: {event.price}")
            print(f"Categories: {', '.join(event.categories)}")
            print("-" * 50)
    except Exception as e:
        print(f"Error testing {api_name}: {str(e)}")

def test_ticketmaster():
    print("\nTesting Ticketmaster API...")
    api_key = os.getenv('TICKETMASTER_API_KEY')
    if not api_key:
        print("Error: TICKETMASTER_API_KEY not found in environment variables")
        return
        
    api = TicketmasterAPI(api_key)
    try:
        events = api.fetch_events("90210", ["music", "sports"])
        print(f"Found {len(events)} events")
        if events:
            print("\nFirst event details:")
            event = events[0]
            print(f"Name: {event.name}")
            print(f"Date: {event.date}")
            print(f"Location: {event.location}")
            print(f"Price: {event.price}")
            print(f"URL: {event.url}")
    except Exception as e:
        print(f"Error testing Ticketmaster API: {str(e)}")

def test_meetup():
    print("\nTesting Meetup API...")
    api_key = os.getenv('MEETUP_API_KEY')
    if not api_key or api_key == "your_meetup_api_key":
        print("Error: Invalid MEETUP_API_KEY in environment variables")
        return
        
    api = MeetupAPI(api_key)
    try:
        events = api.fetch_events("90210", ["music", "sports"])
        print(f"Found {len(events)} events")
        if events:
            print("\nFirst event details:")
            event = events[0]
            print(f"Name: {event.name}")
            print(f"Date: {event.date}")
            print(f"Location: {event.location}")
            print(f"Price: {event.price}")
            print(f"URL: {event.url}")
    except Exception as e:
        print(f"Error testing Meetup API: {str(e)}")

def main():
    # Test each API individually
    apis = ["ticketmaster", "meetup", "seatgeek", "vividseats"]
    
    for api in apis:
        test_api(api)

if __name__ == "__main__":
    load_dotenv()
    print("Testing Event APIs...")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Testing events for Beverly Hills (90210) in the next 30 days")
    print("-" * 50)
    
    # Test each API
    test_ticketmaster()
    test_meetup() 