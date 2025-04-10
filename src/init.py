from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta
from src.api.event_apis import get_all_events, Event
from src.recommender.vector_recommender import VectorEventRecommender
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Create prompt template for event recommendations
event_prompt = PromptTemplate(
    input_variables=["zip_code", "interests", "events"],
    template="""
You are an assistant that recommends local events. The user is located in zip code {zip_code} and is interested in {interests}.
Here is a list of upcoming events with their relevance scores:

{events}

Please summarize and recommend the top 3 events that match the user's interests. For each event, include:
1. Event name and description
2. Date and time
3. Location and venue
4. Price (if available)
5. Direct link to purchase tickets (if available)
6. Why this event matches their interests (based on relevance score)
"""
)

def generate_event_suggestions(zip_code: str, interests: List[str]) -> List[Dict[str, Any]]:
    # Check if OpenAI key is set
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
    
    try:
        # Initialize OpenAI chat model
        llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-3.5-turbo",
            api_key=openai_key
        )
        
        # Fetch real events from various APIs
        logger.info("Fetching events from APIs...")
        events = get_all_events(zip_code, interests)
        
        logger.info(f"Found {len(events)} events")
        
        if not events:
            return []
        
        try:
            # Initialize vector recommender
            recommender = VectorEventRecommender(openai_key)
            
            # Index the events first
            logger.info("Indexing events...")
            recommender.index_events(events)
            logger.info("Events indexed successfully")
            
            # Get vector-based recommendations
            logger.info("Getting vector-based recommendations...")
            query = " ".join(interests)  # Join interests into a single query string
            vector_results = recommender.find_relevant_events(query)
            
            # Convert results to a list of dictionaries
            recommendations = []
            for result in vector_results:
                event = result['event']
                recommendations.append({
                    'title': event['name'],
                    'description': event['description'],
                    'categories': event['categories'],
                    'location': event['location'],
                    'date': event['date'],
                    'price': event['price'],
                    'url': event.get('url', 'N/A'),
                    'relevance_score': result['relevance_score'],
                    'reasoning': result['reasoning'],
                    'personalization': result['personalization']
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in vector-based recommendations: {str(e)}")
            # Fallback to basic event list if vector recommendations fail
            # Use a set to track unique event names
            seen_events = set()
            unique_events = []
            
            for event in events:
                if event.name not in seen_events:
                    seen_events.add(event.name)
                    unique_events.append(event)
            
            # Convert events to a list of dictionaries
            recommendations = []
            for event in unique_events[:5]:  # Show top 5 unique events
                recommendations.append({
                    'title': event.name,
                    'description': event.description,
                    'categories': event.categories,
                    'location': event.location,
                    'date': event.date,
                    'price': event.price,
                    'url': getattr(event, 'url', 'N/A')
                })
            
            return recommendations
        
    except Exception as e:
        logger.error(f"Error generating event suggestions: {str(e)}")
        return []

# Example usage
def main():
    # Using San Francisco zip code for better event coverage
    zip_code = "94102"  # San Francisco, CA
    interests = [
        "art", "technology", "music", "ballet", "standup comedy", 
        "opera", "broadway", "live sports", "dance festivals", 
        "food festivals", "new movies"
    ]
    
    logger.info("Fetching events and generating recommendations...")
    suggestions = generate_event_suggestions(zip_code, interests)
    logger.info(f"\nEvent recommendations for {zip_code} based on your interests:\n")
    print(suggestions)

if __name__ == "__main__":
    main()
