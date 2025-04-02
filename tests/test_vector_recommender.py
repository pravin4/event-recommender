import unittest
from src.recommender.vector_recommender import VectorEventRecommender, ConversationMemory
from src.api.event_apis import Event
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

class TestVectorRecommender(unittest.TestCase):
    def setUp(self):
        """Set up test data"""
        # Get OpenAI API key from environment
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
            
        self.recommender = VectorEventRecommender(self.api_key)
        
        # Create sample events
        self.events = [
            Event(
                name="Jazz in the Park",
                description="An outdoor jazz festival featuring local artists. Live music under the stars.",
                date=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                location="Central Park, New York",
                zip_code="10001",
                categories=["music", "jazz", "outdoor"],
                url="http://example.com/jazz",
                price="$25",
                venue="Central Park Bandshell"
            ),
            Event(
                name="Classical Symphony Night",
                description="An evening of classical music in the grand hall. Featuring Beethoven and Mozart.",
                date=(datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                location="Downtown Gallery, New York",
                zip_code="10001",
                categories=["music", "classical", "indoor"],
                url="http://example.com/classical",
                price="$15",
                venue="Downtown Gallery"
            ),
            Event(
                name="Blues Garden Party",
                description="Outdoor blues music festival with food trucks and craft vendors.",
                date=(datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                location="Blue Note, New York",
                zip_code="10001",
                categories=["music", "blues", "outdoor"],
                url="http://example.com/blues",
                price="$30",
                venue="Blue Note"
            ),
            Event(
                name="Tech Startup Meetup",
                description="Networking event for tech entrepreneurs and innovators",
                date=(datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                location="Innovation Hub, New York",
                zip_code="10001",
                categories=["technology", "networking", "business"],
                url="http://example.com/tech",
                price="Free",
                venue="Innovation Hub"
            )
        ]
        
        # Index the events
        self.recommender.index_events(self.events)
        
        # Simulate user interactions
        self.recommender.conversation_memory.add_interaction("jazz music", "Jazz in the Park")
        self.recommender.conversation_memory.update_preferences("Jazz in the Park", True)  # User liked this
        self.recommender.conversation_memory.update_preferences("Classical Symphony Night", False)  # User disliked this

    def test_vector_matching(self):
        """Test vector-based matching"""
        # Test with music-related query
        results = self.recommender.find_relevant_events("music jazz")
        
        self.assertTrue(len(results) > 0)
        self.assertTrue(any("Jazz in the Park" in r["event"]["name"] for r in results))
        self.assertTrue(any("Blues Garden Party" in r["event"]["name"] for r in results))

    def test_semantic_matching(self):
        """Test semantic matching capabilities"""
        # Test with related but different terms
        results = self.recommender.find_relevant_events("live performance concerts")
        
        # Should match music events even without exact keyword match
        self.assertTrue(len(results) > 0)
        self.assertTrue(any("music" in r["event"]["description"].lower() for r in results))

    def test_relevance_scores(self):
        """Test relevance scoring"""
        results = self.recommender.find_relevant_events("jazz")
        
        # Check that relevance scores are present and reasonable
        for result in results:
            self.assertIn("relevance_score", result)
            self.assertIsInstance(result["relevance_score"], float)
            self.assertGreaterEqual(result["relevance_score"], 0)
            self.assertLessEqual(result["relevance_score"], 1)

    def test_structured_output(self):
        """Test structured output parsing"""
        results = self.recommender.find_relevant_events("jazz")
        
        # Check structured output format
        for result in results:
            self.assertIn("event", result)
            self.assertIn("relevance_score", result)
            self.assertIn("reasoning", result)
            self.assertIn("personalization", result)
            
            # Check that event data is complete
            self.assertIn("name", result["event"])
            self.assertIn("description", result["event"])
            self.assertIn("categories", result["event"])
            
            # Check that reasoning and personalization are not empty
            self.assertTrue(len(result["reasoning"]) > 0)
            self.assertTrue(len(result["personalization"]) > 0)

    def test_conversation_memory(self):
        """Test conversation memory functionality"""
        # Check that memory is working
        self.assertTrue(len(self.recommender.conversation_memory.history) >= 2)
        
        # Check that preferences are stored
        preferences = self.recommender.conversation_memory.get_preferences_summary()
        self.assertIn("Jazz in the Park", preferences)
        self.assertIn("likes: 1", preferences.lower())
        self.assertIn("Classical Symphony Night", preferences)
        self.assertIn("dislikes: 1", preferences.lower())

    def test_caching(self):
        """Test caching functionality"""
        query = "jazz music"
        
        # First query - should compute results
        start_time = time.time()
        results1 = self.recommender.find_relevant_events(query)
        first_query_time = time.time() - start_time
        
        # Second query - should use cache
        start_time = time.time()
        results2 = self.recommender.find_relevant_events(query)
        second_query_time = time.time() - start_time
        
        # Check that results are the same
        self.assertEqual(len(results1), len(results2))
        
        # Check that second query is faster (using cache)
        self.assertLess(second_query_time, first_query_time)

    def test_personalized_recommendations(self):
        """Test that recommendations are personalized based on user history and preferences"""
        results = self.recommender.find_relevant_events("music events")
        
        # Verify the structure and personalization of recommendations
        self.assertTrue(len(results) > 0)
        
        for result in results:
            # Check that each result has the required fields
            self.assertIn("event", result)
            self.assertIn("relevance_score", result)
            self.assertIn("reasoning", result)
            self.assertIn("personalization", result)
            
            # Check that personalization considers user preferences
            if "Jazz in the Park" in result["event"]["name"]:
                self.assertIn("outdoor", result["personalization"].lower())
                self.assertIn("jazz", result["personalization"].lower())
            
            # Check that reasoning includes context
            self.assertIn("based on", result["reasoning"].lower())
            
            # Verify that disliked events are not highly recommended
            if "Classical Symphony Night" in result["event"]["name"]:
                self.assertLess(result["relevance_score"], 0.8)

    def test_conversation_memory_impact(self):
        """Test that conversation memory affects recommendations"""
        # First search
        initial_results = self.recommender.find_relevant_events("music")
        
        # Add more user interactions
        self.recommender.conversation_memory.add_interaction("outdoor music", "Blues Garden Party")
        self.recommender.conversation_memory.update_preferences("Blues Garden Party", True)
        
        # Second search
        later_results = self.recommender.find_relevant_events("music")
        
        # Verify that outdoor events are more relevant in later results
        outdoor_scores = [
            r["relevance_score"] 
            for r in later_results 
            if "outdoor" in r["event"]["description"].lower()
        ]
        indoor_scores = [
            r["relevance_score"] 
            for r in later_results 
            if "indoor" in r["event"]["description"].lower()
        ]
        
        if outdoor_scores and indoor_scores:
            self.assertGreater(min(outdoor_scores), max(indoor_scores))

if __name__ == '__main__':
    unittest.main() 