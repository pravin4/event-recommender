from typing import List, Dict, Any, Optional, Callable, Union
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, ConfigDict
import logging
import time
from datetime import datetime, timedelta
import requests
from src.api.event_apis import Event
import os
import numpy as np
import json
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventRecommendation(BaseModel):
    """Structured output for event recommendations"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    event_name: str = Field(description="Name of the recommended event")
    relevance_score: float = Field(description="Relevance score between 0 and 1")
    reasoning: str = Field(description="Explanation of why this event is recommended")
    personalization: str = Field(description="How this recommendation is personalized based on user context")

class ConversationMemory:
    def __init__(self):
        self.history = []
        self.preferences = {}
        self.max_history = 10

    def add_interaction(self, query: str, results: List[Dict[str, Any]] = None) -> None:
        """Add a user interaction to the conversation history."""
        interaction = {
            'timestamp': time.time(),
            'query': query,
            'results': results or []
        }
        self.history.append(interaction)
        
        # Keep only the most recent interactions
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def update_preferences(self, event_name: str, liked: bool) -> None:
        """Update user preferences for an event."""
        if event_name not in self.preferences:
            self.preferences[event_name] = {'likes': 0, 'dislikes': 0}
        
        if liked:
            self.preferences[event_name]['likes'] += 1
        else:
            self.preferences[event_name]['dislikes'] += 1

    def get_recent_history(self) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        return self.history[-5:]  # Return last 5 interactions

    def get_preferences_summary(self) -> str:
        """Get a summary of user preferences."""
        if not self.preferences:
            return "No preferences recorded yet."
        
        summary_parts = []
        for event_name, counts in self.preferences.items():
            likes = counts.get('likes', 0)
            dislikes = counts.get('dislikes', 0)
            summary_parts.append(f"{event_name} (Likes: {likes}, Dislikes: {dislikes})")
        
        return " | ".join(summary_parts)

class VectorEventRecommender:
    def __init__(self, openai_api_key: str):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.vector_store = None
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4",
            temperature=0.7
        )
        self.conversation_memory = ConversationMemory()
        self.output_parser = PydanticOutputParser(pydantic_object=EventRecommendation)
        
        # Initialize caching
        self.cache = {}
        self.cache_expiry = timedelta(hours=1)
        self.last_cache_cleanup = datetime.now()
        
        # Enhanced prompt template with structured output
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert event recommender. Analyze the following event and provide a personalized recommendation.
            Consider the user's recent interactions and preferences when making recommendations.
            
            Recent Context:
            {recent_context}
            
            User Preferences:
            {user_preferences}
            
            Current Query: {query}
            
            Provide a recommendation in the following structured format:
            {format_instructions}
            """),
            ("human", "{event}")
        ])
        
        logger.info("VectorEventRecommender initialized with OpenAI API key")

    def _get_event_text(self, event: Union[Event, Dict[str, Any]]) -> str:
        """Format event data for vector search."""
        if isinstance(event, dict):
            categories = ', '.join(event.get('categories', []))
            return f"""Event: {event.get('name', '')}
Description: {event.get('description', '')}
Categories: {categories}
Venue: {event.get('venue', '')}
Location: {event.get('location', '')}
Date: {event.get('date', '')}
Price: {event.get('price', '')}
URL: {event.get('url', '')}"""
        else:
            categories = ', '.join(getattr(event, 'categories', []))
            return f"""Event: {event.name}
Description: {event.description}
Categories: {categories}
Venue: {getattr(event, 'venue', '')}
Location: {getattr(event, 'location', '')}
Date: {str(getattr(event, 'date', ''))}
Price: {getattr(event, 'price', '')}
URL: {getattr(event, 'url', '')}"""

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def _event_to_dict(self, event: Event) -> Dict[str, Any]:
        """Convert an Event object to a dictionary representation."""
        return {
            "name": event.name,
            "description": event.description,
            "categories": getattr(event, 'categories', []),
            "tags": getattr(event, 'tags', []),
            "location": getattr(event, 'location', ''),
            "date": str(getattr(event, 'date', '')),
            "venue": getattr(event, 'venue', ''),
            "price": getattr(event, 'price', ''),
            "url": getattr(event, 'url', '')
        }

    def index_events(self, events: List[Event]) -> None:
        if not events:
            logger.warning("No events provided for indexing")
            return
        
        try:
            logger.info(f"Processing {len(events)} events for indexing")
            texts = [self._get_event_text(event) for event in events]
            logger.info("Generated event texts")
            
            embeddings = self._get_embeddings(texts)
            logger.info("Generated embeddings")
            
            event_dicts = [{"event": self._event_to_dict(event)} for event in events]
            logger.info("Created event dictionaries")
            
            # Create an embedding function that matches langchain's expected interface
            def embedding_function(text: str) -> List[float]:
                return self._get_embeddings([text])[0]
            
            if self.vector_store is None:
                logger.info("Creating new vector store")
                self.vector_store = FAISS.from_embeddings(
                    text_embeddings=list(zip(texts, embeddings)),
                    embedding=embedding_function,  # Provide the embedding function
                    metadatas=event_dicts
                )
                logger.info("Vector store created successfully")
            else:
                logger.info("Adding embeddings to existing vector store")
                self.vector_store.add_embeddings(
                    text_embeddings=list(zip(texts, embeddings)),
                    metadatas=event_dicts
                )
                logger.info("Embeddings added successfully")
            
            logger.info(f"Successfully indexed {len(events)} events")

            # Add initial interactions for each event
            for event in events:
                self.conversation_memory.add_interaction(
                    f"Added event: {event.name}",
                    [{"event": self._event_to_dict(event)}]
                )

        except Exception as e:
            logger.error(f"Error indexing events: {str(e)}")
            raise

    def find_relevant_events(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Find relevant events based on the query."""
        try:
            logger.info(f"Finding relevant events for query: {query}")
            
            # Check if vector store exists
            if self.vector_store is None:
                logger.error("Vector store is None - no events have been indexed")
                raise ValueError("No events have been indexed yet")
            
            # Check cache first
            cache_key = f"{query}_{k}"
            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                if time.time() - cache_entry['timestamp'] < self.cache_expiry.total_seconds():
                    logger.info("Returning cached results")
                    return cache_entry['results']

            logger.info("Performing similarity search")
            # Get vector search results
            results = self.vector_store.similarity_search_with_score(
                query,
                k=k
            )
            logger.info(f"Found {len(results)} results")

            # Process results
            processed_results = []
            for doc, score in results:
                event_data = doc.metadata.get('event', {})
                # Normalize score to be between 0 and 1
                normalized_score = 1 / (1 + score)  # Convert distance to similarity score
                
                # Get personalization info
                personalization = self._get_personalization_info(event_data)
                
                # Get recent context and preferences
                recent_context = "\n".join([
                    f"- {interaction['query']}"
                    for interaction in self.conversation_memory.get_recent_history()
                ])
                user_preferences = self.conversation_memory.get_preferences_summary()
                
                # Format event data for the prompt
                event_str = f"""Name: {event_data.get('name', '')}
Description: {event_data.get('description', '')}
Categories: {', '.join(event_data.get('categories', []))}
Location: {event_data.get('location', '')}
Date: {event_data.get('date', '')}
Price: {event_data.get('price', '')}
URL: {event_data.get('url', '')}"""
                
                # Get recommendation from LLM
                prompt_args = {
                    "recent_context": recent_context,
                    "user_preferences": user_preferences,
                    "query": query,
                    "event": event_str,
                    "format_instructions": self.output_parser.get_format_instructions()
                }
                
                chain = self.prompt_template | self.llm | self.output_parser
                recommendation = chain.invoke(prompt_args)
                
                processed_results.append({
                    'event': event_data,
                    'relevance_score': normalized_score,
                    'reasoning': recommendation.reasoning,
                    'personalization': recommendation.personalization
                })

            # Update cache
            self.cache[cache_key] = {
                'results': processed_results,
                'timestamp': time.time()
            }

            # Update conversation memory with query and results
            self.conversation_memory.add_interaction(query, processed_results)

            return processed_results

        except Exception as e:
            logger.error(f"Error finding relevant events: {str(e)}")
            raise

    def _get_personalization_info(self, event_data: Dict[str, Any]) -> str:
        """Generate personalization information based on conversation history."""
        try:
            history = self.conversation_memory.get_recent_history()
            if not history:
                return "No personalization data available yet."

            # Analyze user's interests from history and event categories
            interests = set()
            for interaction in history:
                if 'query' in interaction:
                    interests.update(interaction['query'].lower().split())
                if 'results' in interaction:
                    for result in interaction['results']:
                        if 'event' in result:
                            event = result['event']
                            interests.update(event.get('categories', []))

            # Match interests with event
            matching_interests = []
            event_name = event_data.get('name', '').lower()
            event_description = event_data.get('description', '').lower()
            event_categories = [cat.lower() for cat in event_data.get('categories', [])]
            
            for interest in interests:
                if (interest.lower() in event_name or 
                    interest.lower() in event_description or 
                    interest.lower() in event_categories):
                    matching_interests.append(interest)

            if matching_interests:
                return f"This event matches your interests in: {', '.join(matching_interests)}"
            return "This event might introduce you to new interests."

        except Exception as e:
            logger.error(f"Error generating personalization info: {str(e)}")
            return "Error generating personalization information."

    def update_user_feedback(self, event_name: str, liked: bool):
        """Update user preferences based on feedback"""
        self.conversation_memory.update_preferences(event_name, liked)
        logger.info(f"Updated preferences for {event_name}: {'liked' if liked else 'disliked'}") 