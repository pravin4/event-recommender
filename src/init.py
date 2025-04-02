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
        events = get_all_events(zip_code, interests)
        
        if not events:
            return "No events found matching your interests. Try adjusting your search criteria or zip code."
        
        # Initialize vector recommender
        recommender = VectorEventRecommender()
        
        # Get vector-based recommendations
        logger.info("Getting vector-based recommendations...")
        vector_results = recommender.find_relevant_events(interests)
        
        # Create a more detailed event summary with relevance scores
        event_summary = "\n".join([
            f"- {result['event_text']}\n  Relevance Score: {result['relevance_score']:.2f}\n  Matching Interests: {', '.join(result['matching_interests'])}"
            for result in vector_results
        ])
        
        # Create the prompt with the vector-based results
        prompt = f"""Based on the following events and user interests, recommend the top 5 most relevant events.
        Consider the user's interests: {', '.join(interests)}
        
        Available events with relevance scores:
        {event_summary}
        
        Please provide recommendations in this format:
        1. Event Name - Date and Venue
           Why it matches your interests (based on relevance score)
        2. Event Name - Date and Venue
           Why it matches your interests (based on relevance score)
        etc.
        
        If no events match the interests, say "No events found matching your interests."
        """
        
        # Generate recommendations using the OpenAI model
        logger.info("Generating final recommendations...")
        response = llm.invoke(prompt)
        return response.content
        
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
