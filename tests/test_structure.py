import os
import sys
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.event_apis import Event, EventAPI, TicketmasterAPI, MeetupAPI, SeatGeekAPI, VividSeatsAPI

class TestProjectStructure(unittest.TestCase):
    """Test that the project structure is working correctly."""
    
    def test_imports(self):
        """Test that we can import the necessary modules."""
        self.assertTrue(Event is not None)
        self.assertTrue(EventAPI is not None)
        self.assertTrue(TicketmasterAPI is not None)
        self.assertTrue(MeetupAPI is not None)
        self.assertTrue(SeatGeekAPI is not None)
        self.assertTrue(VividSeatsAPI is not None)
    
    def test_event_class(self):
        """Test that the Event class can be instantiated."""
        event = Event(
            name="Test Event",
            description="A test event",
            date="2023-01-01",
            location="Test Location",
            zip_code="12345",
            categories=["test"],
            url="https://example.com",
            price="$10",
            venue="Test Venue"
        )
        
        self.assertEqual(event.name, "Test Event")
        self.assertEqual(event.description, "A test event")
        self.assertEqual(event.date, "2023-01-01")
        self.assertEqual(event.location, "Test Location")
        self.assertEqual(event.zip_code, "12345")
        self.assertEqual(event.categories, ["test"])
        self.assertEqual(event.url, "https://example.com")
        self.assertEqual(event.price, "$10")
        self.assertEqual(event.venue, "Test Venue")

if __name__ == '__main__':
    unittest.main() 