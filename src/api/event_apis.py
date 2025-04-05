import os
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import math
from geopy.geocoders import Nominatim
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the distance between two points in miles using the Haversine formula."""
    R = 3959.87433  # Earth's radius in miles

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

@dataclass
class Event:
    name: str
    description: str
    date: str
    location: str
    zip_code: str
    categories: List[str]
    url: Optional[str] = None
    price: Optional[str] = None
    venue: Optional[str] = None

class EventAPI:
    def __init__(self, name):
        self.name = name
        self.session = requests.Session()

    def _get_coordinates(self, zip_code):
        """Get latitude and longitude for a zip code using OpenStreetMap Nominatim API"""
        try:
            url = f"https://nominatim.openstreetmap.org/search?postalcode={zip_code}&country=US&format=json"
            response = requests.get(url, headers={'User-Agent': 'EventFinder/1.0'})
            response.raise_for_status()
            data = response.json()
            
            if data:
                return {
                    'lat': data[0]['lat'],
                    'lng': data[0]['lon']
                }
            return None
        except Exception as e:
            print(f"Error getting coordinates for zip code {zip_code}: {e}")
            return None

    def fetch_events(self, location, interests=None):
        """Base method to fetch events. Should be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement fetch_events")

    def cleanup(self):
        """Cleanup method to be called on shutdown"""
        try:
            if self.session:
                self.session.close()
        except Exception as e:
            print(f"Error cleaning up {self.name} API: {e}")

    def __del__(self):
        """Destructor to ensure cleanup is called"""
        self.cleanup()

class TicketmasterAPI(EventAPI):
    def __init__(self, api_key):
        super().__init__("Ticketmaster")
        self.api_key = api_key
        self.base_url = "https://app.ticketmaster.com/discovery/v2/events.json"

    def fetch_events(self, location, interests=None):
        """Fetch events from Ticketmaster API"""
        try:
            # Get coordinates for the location
            logger.info(f"Getting coordinates for location: {location}")
            coords = self._get_coordinates(location)
            if not coords:
                logger.error("Could not get coordinates for location")
                return []

            # Calculate date range (next 30 days)
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30)

            # Make API request
            params = {
                "apikey": self.api_key,
                "latlong": f"{coords['lat']},{coords['lng']}",
                "radius": "50",
                "unit": "miles",
                "startDateTime": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "endDateTime": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "size": 100,
                "sort": "date,asc"
            }

            logger.info(f"Requesting Ticketmaster API with params: {params}")
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info("Successfully received response from Ticketmaster API")
            logger.info(f"Raw API response: {json.dumps(data, indent=2)}")

            events = []
            for event in data.get("_embedded", {}).get("events", []):
                try:
                    # Extract venue information
                    venue = event.get("_embedded", {}).get("venues", [{}])[0]
                    location = f"{venue.get('address', {}).get('line1', '')}, {venue.get('city', {}).get('name', '')}"

                    # Extract price information
                    logger.info(f"Processing event: {event.get('name')}")
                    
                    # Try to get prices from priceRanges
                    price_ranges = event.get("priceRanges", [])
                    if price_ranges:
                        min_price = price_ranges[0].get("min")
                        max_price = price_ranges[0].get("max")
                        if min_price and max_price:
                            # Always show the price range
                            price = f"${min_price:.2f} - ${max_price:.2f}"
                        elif min_price:
                            # If we only have a minimum price, show "From $X"
                            price = f"From ${min_price:.2f}"
                        else:
                            price = "Price not available"
                    else:
                        # Check if tickets are on sale
                        sales = event.get("sales", {})
                        public_sales = sales.get("public", {})
                        if public_sales and public_sales.get("startDateTime"):
                            # If tickets are on sale but we don't have price ranges, show "Price not available"
                            price = "Price not available"
                        else:
                            price = "Tickets not yet on sale"
                    
                    logger.info(f"Final price set to: {price}")

                    # Extract categories
                    categories = []
                    for classification in event.get("classifications", []):
                        if "segment" in classification:
                            categories.append(classification["segment"]["name"])
                        if "genre" in classification:
                            categories.append(classification["genre"]["name"])

                    # Get description from various possible fields, filtering out administrative content
                    raw_description = (
                        event.get("description") or 
                        event.get("info") or 
                        event.get("pleaseNote") or 
                        ""
                    )

                    # Filter out administrative content and create a more engaging description
                    if raw_description:
                        # Common administrative keywords to filter out
                        admin_keywords = [
                            "bag policy", "bag check", "security", "prohibited items",
                            "parking", "entry", "doors open", "re-entry", "refund",
                            "camera policy", "recording", "smoking", "alcohol",
                            "age restriction", "ID required", "ticket limit"
                        ]
                        
                        # Check if the description contains administrative content
                        is_admin_content = any(keyword.lower() in raw_description.lower() for keyword in admin_keywords)
                        
                        if is_admin_content:
                            # Create a more engaging description based on event details
                            description = (
                                f"Experience {event.get('name', 'this exciting event')} at {venue.get('name', 'this venue')}! "
                                f"This {', '.join(categories) if categories else 'event'} promises to be an unforgettable experience. "
                                f"Join us in {location} for an evening of entertainment and excitement."
                            )
                        else:
                            description = raw_description
                    else:
                        # Create a default engaging description
                        description = (
                            f"Join us for {event.get('name', 'this event')} at {venue.get('name', 'this venue')}! "
                            f"Experience an exciting {', '.join(categories) if categories else 'event'} in {location}. "
                            f"Don't miss out on this incredible opportunity to be part of the action!"
                        )

                    # Create event object
                    event_obj = Event(
                        name=event.get("name", "Untitled Event"),
                        description=description,
                        date=event.get("dates", {}).get("start", {}).get("localDate", "N/A"),
                        location=location,
                        zip_code=venue.get("postalCode", "00000"),  # Default zip code if not available
                        categories=categories,
                        url=event.get("url", "N/A"),
                        price=price,
                        venue=venue.get("name", "Unknown Venue")
                    )

                    # If no interests specified, include all events
                    if not interests:
                        events.append(event_obj)
                    else:
                        # Check if event matches any interests (OR condition)
                        event_name = event_obj.name.lower()
                        event_description = event_obj.description.lower()
                        event_categories = [cat.lower() for cat in event_obj.categories]
                        
                        # Create a combined text to search in
                        event_text = f"{event_name} {event_description} {' '.join(event_categories)}".lower()
                        
                        # Check if any interest matches (OR condition)
                        if any(interest.lower() in event_text for interest in interests):
                            events.append(event_obj)

                except Exception as e:
                    logger.error(f"Error processing event: {str(e)}")
                    continue

            logger.info(f"Successfully processed {len(events)} events from Ticketmaster")
            return events

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching events from Ticketmaster: {str(e)}")
            return []

# Bandsintown API requires a partnership program registration and cannot be used
# Commenting out the entire class as it cannot be fixed
"""
class BandsintownAPI(EventAPI):
    def __init__(self, api_key):
        super().__init__("Bandsintown")
        self.api_key = api_key
        self.base_url = "https://rest.bandsintown.com"
        # List of popular artists across genres
        self.artists = [
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

    def fetch_events(self, location, interests=None):
        # Implementation details...
        pass
"""

class MeetupAPI(EventAPI):
    def __init__(self, api_key):
        super().__init__("Meetup")
        self.api_key = api_key
        self.base_url = "https://api.meetup.com/api/v3"

    def fetch_events(self, location, interests=None):
        """Fetch events from Meetup API"""
        try:
            # Get coordinates for the location
            coords = self._get_coordinates(location)
            if not coords:
                return []

            # Calculate date range (next 30 days)
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30)

            # Make API request
            params = {
                "key": self.api_key,
                "lat": coords["lat"],
                "lon": coords["lng"],
                "radius": "50",
                "start_date_range": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_date_range": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "page": 100,
                "order": "time"
            }

            print(f"Requesting Meetup API with params: {params}")
            response = requests.get(f"{self.base_url}/events", params=params)
            
            if response.status_code == 401:
                print("Invalid Meetup API key")
                return []
                
            response.raise_for_status()
            data = response.json()

            events = []
            for event in data:
                try:
                    # Extract venue information
                    venue = event.get("venue", {})
                    venue_name = venue.get("name", "Unknown Venue")
                    event_location = f"{venue_name}, {venue.get('city', '')}, {venue.get('state', '')}"

                    # Skip events that don't match the requested location
                    if location.lower() not in event_location.lower():
                        continue

                    # Extract fee information
                    fee = event.get("fee", {})
                    price = "Free" if not fee or fee.get("amount", 0) == 0 else f"${fee.get('amount', 'N/A')}"

                    # Extract categories
                    categories = []
                    group = event.get("group", {})
                    if "category" in group:
                        categories.append(group["category"]["name"])
                    if "name" in group:
                        categories.append(group["name"])

                    # Create event object
                    event_obj = Event(
                        name=event.get("name", "Untitled Event"),
                        description=event.get("description", ""),
                        date=event.get("local_date", "N/A"),
                        location=event_location,
                        zip_code=venue.get("zip", ""),
                        price=price,
                        url=event.get("link", "N/A"),
                        categories=categories
                    )

                    # If no interests specified, include all events
                    if not interests:
                        events.append(event_obj)
                    else:
                        # Check if event matches any interests (OR condition)
                        event_text = f"{event_obj.name} {event_obj.description} {' '.join(event_obj.categories)}".lower()
                        if any(interest.lower() in event_text for interest in interests):
                            events.append(event_obj)

                except Exception as e:
                    print(f"Error processing event: {str(e)}")
                    continue

            return events

        except requests.exceptions.RequestException as e:
            print(f"Error fetching events from Meetup: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response text: {e.response.text}")
            return []

class SeatGeekAPI(EventAPI):
    def __init__(self, api_key):
        super().__init__("SeatGeek")
        self.api_key = api_key
        self.base_url = "https://api.seatgeek.com/2/events"

    def fetch_events(self, location, interests=None):
        start_date = datetime.now().replace(microsecond=0)
        end_date = start_date + timedelta(days=30)
        
        params = {
            "client_id": self.api_key,
            "postal_code": location,
            "per_page": 100,
            "datetime_local.gte": start_date.isoformat(),
            "datetime_local.lte": end_date.isoformat(),
            "sort": "datetime_local.asc"
        }
        
        try:
            response = requests.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            data = response.json()
            
            events = []
            for event in data.get("events", []):
                if any(interest.lower() in event.get("title", "").lower() for interest in interests):
                    venue = event.get("venue", {})
                    price = event.get("stats", {}).get("lowest_price", "N/A")
                    price = f"${price}" if price != "N/A" else "N/A"
                    
                    events.append(Event(
                        name=event.get("title", ""),
                        description=event.get("description", ""),
                        date=event.get("datetime_local", ""),
                        location=f"{venue.get('address', '')}, {venue.get('city', '')}",
                        zip_code=location,
                        categories=[cat.get("name", "").lower() for cat in event.get("taxonomies", [])],
                        url=event.get("url", ""),
                        price=price,
                        venue=venue.get("name", "")
                    ))
            return events
        except Exception as e:
            print(f"SeatGeek API Error: {e}")
            return []

class VividSeatsAPI(EventAPI):
    def __init__(self, api_key: str):
        super().__init__("Vivid Seats")
        self.api_key = api_key
        self.base_url = "https://skybox.vividseats.com/api/v1"

    def fetch_events(self, location, interests=None):
        """Fetch events from Vivid Seats Skybox API"""
        try:
            # Get coordinates for the location
            coords = self._get_coordinates(location)
            if not coords:
                return []

            # Calculate date range (next 30 days)
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30)

            # Make API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            params = {
                "latitude": coords["lat"],
                "longitude": coords["lng"],
                "radius": "50",
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "limit": 100
            }

            print(f"Requesting Vivid Seats API with params: {params}")
            response = requests.get(f"{self.base_url}/events", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            events = []
            for event in data.get("events", []):
                try:
                    # Extract venue information
                    venue = event.get("venue", {})
                    venue_name = venue.get("name", "Unknown Venue")
                    event_location = f"{venue_name}, {venue.get('city', '')}, {venue.get('state', '')}"

                    # Extract price information
                    price = event.get("minPrice", "N/A")
                    if price != "N/A":
                        price = f"${price}"

                    # Extract categories
                    categories = []
                    if event.get("category"):
                        categories.append(event["category"].lower())
                    if event.get("subcategory"):
                        categories.append(event["subcategory"].lower())

                    # Create event object
                    event_obj = Event(
                        name=event.get("name", "Untitled Event"),
                        description=event.get("description", ""),
                        date=event.get("dateTime", "N/A"),
                        location=event_location,
                        zip_code=venue.get("postalCode", ""),
                        categories=categories,
                        url=event.get("url", "N/A"),
                        price=price,
                        venue=venue_name
                    )

                    # If no interests specified, include all events
                    if not interests:
                        events.append(event_obj)
                    else:
                        # Check if event matches any interests (OR condition)
                        event_text = f"{event_obj.name} {event_obj.description} {' '.join(event_obj.categories)}".lower()
                        if any(interest.lower() in event_text for interest in interests):
                            events.append(event_obj)

                except Exception as e:
                    print(f"Error processing event: {str(e)}")
                    continue

            return events

        except requests.exceptions.RequestException as e:
            print(f"Error fetching events from Vivid Seats: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response text: {e.response.text}")
            return []

class EventAggregator:
    def __init__(self):
        logger.info("Initializing EventAggregator")
        # Initialize APIs dictionary with Ticketmaster as the default
        self.apis = {
            "ticketmaster": TicketmasterAPI(os.getenv("TICKETMASTER_API_KEY", ""))
        }
        logger.info("Initialized Ticketmaster API")
        
        # Add VividSeats API if key is available
        vividseats_key = os.getenv("VIVIDSEATS_API_KEY")
        if vividseats_key and vividseats_key != "your_vividseats_api_key":
            self.apis["vividseats"] = VividSeatsAPI(vividseats_key)
            logger.info("Initialized VividSeats API")
            
        # Add SeatGeek API if both client ID and secret are available
        seatgeek_client_id = os.getenv("SEATGEEK_CLIENT_ID")
        seatgeek_client_secret = os.getenv("SEATGEEK_CLIENT_SECRET")
        if (seatgeek_client_id and seatgeek_client_id != "your_client_id" and 
            seatgeek_client_secret and seatgeek_client_secret != "your_client_secret"):
            self.apis["seatgeek"] = SeatGeekAPI(seatgeek_client_id)
            logger.info("Initialized SeatGeek API")
        
        logger.info(f"Available APIs: {list(self.apis.keys())}")

    def get_all_events(self, zip_code: str, interests: List[str]) -> List[Event]:
        """Aggregate events from all available sources"""
        all_events = []
        
        for api_name, api in self.apis.items():
            try:
                logger.info(f"Fetching events from {api_name}...")
                events = api.fetch_events(zip_code, interests)
                logger.info(f"Found {len(events)} events from {api_name}")
                all_events.extend(events)
            except Exception as e:
                logger.error(f"Error fetching events from {api_name}: {e}")
                continue
        
        # Sort events by date
        all_events.sort(key=lambda x: x.date)
        logger.info(f"Total events found across all APIs: {len(all_events)}")
        
        return all_events

def get_all_events(zip_code: str, interests: Optional[List[str]] = None) -> List[Event]:
    """Get events from all available APIs"""
    logger.info(f"Getting events for zip code {zip_code}")
    aggregator = EventAggregator()
    # Ignore interests and get all events
    events = aggregator.get_all_events(zip_code, [])
    logger.info(f"Total events found: {len(events)}")
    return events 