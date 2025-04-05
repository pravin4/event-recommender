from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import List, Dict
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

def generate_event_suggestions(zip_code: str, interests: List[str]) -> str:
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
        events = get_all_events(zip_code, [])  # Pass empty list for interests
        
        logger.info(f"Found {len(events)} events")
        
        if not events:
            return "No events found in your area. Try adjusting your zip code."
        
        try:
            # Initialize vector recommender
            recommender = VectorEventRecommender(openai_key)
            
            # Index the events first
            logger.info("Indexing events...")
            recommender.index_events(events)
            logger.info("Events indexed successfully")
            
            # Get vector-based recommendations
            logger.info("Getting vector-based recommendations...")
            # Get recommendations for each interest separately
            all_vector_results = []
            for interest in interests:
                vector_results = recommender.find_relevant_events(interest, k=5)  # Get 5 events per interest
                all_vector_results.extend(vector_results)
            
            # Remove duplicate events based on name, date, and venue
            seen_events = set()
            unique_results = []
            for result in all_vector_results:
                event_key = f"{result['event']['name']}_{result['event']['date']}_{result['event']['venue']}"
                if event_key not in seen_events:
                    seen_events.add(event_key)
                    unique_results.append(result)
            
            # Sort by relevance score and take top 10
            unique_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            unique_results = unique_results[:10]
            
            # Create a more detailed event summary with relevance scores
            event_summary = "\n".join([
                f"- {result['event']['name']}\n  Date: {result['event']['date']}\n  Location: {result['event']['location']}\n  Venue: {result['event']['venue']}\n  Price: {result['event']['price']}\n  Description: {result['event']['description']}\n  Categories: {', '.join(result['event']['categories'])}\n  Relevance Score: {result['relevance_score']:.2f}\n  {result['reasoning']}\n  {result['personalization']}"
                for result in unique_results
            ])
            
            # Create the prompt with the vector-based results
            prompt = f"""Based on the following events, recommend the top 10 most relevant events.
            The user is interested in: {', '.join(interests)}
            
            Available events with relevance scores:
            {event_summary}
            
            Please provide recommendations in this format:
            1. Event Name - Date and Venue
               Reasoning: Why this event might be interesting
            2. Event Name - Date and Venue
               Reasoning: Why this event might be interesting
            etc.
            
            Important rules:
            - Do not include duplicate events (same name, date, and venue)
            - Include a balanced mix of events matching different interests
            - Include at least 5 events if available
            - If no events are available, say "No events found in your area."
            """
            
            # Generate recommendations using the OpenAI model
            logger.info("Generating final recommendations...")
            response = llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            logger.error(f"Error in vector-based recommendations: {str(e)}")
            # Fallback to basic event list if vector recommendations fail
            event_summary = "\n".join([
                f"- {event.name}\n  Description: {event.description}\n  Categories: {', '.join(event.categories)}\n  Location: {event.location}\n  Date: {event.date}\n  Price: {event.price}"
                for event in events[:5]  # Show top 5 events
            ])
            return f"""Here are some events that match your interests:

{event_summary}

Note: The recommendation system encountered an error, so these are basic matches without relevance scoring."""
        
    except Exception as e:
        logger.error(f"Error generating event suggestions: {str(e)}")
        return f"Error generating recommendations: {str(e)}"

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
