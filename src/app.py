from flask import Flask, render_template, request, jsonify
from src.init import generate_event_suggestions
from flask_cors import CORS
import os
from src.api.event_apis import TicketmasterAPI, VividSeatsAPI, SeatGeekAPI, get_all_events
import atexit
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
# More permissive CORS settings for development
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize API clients
api_clients = []

# Always include Ticketmaster API
ticketmaster_api = TicketmasterAPI(os.getenv('TICKETMASTER_API_KEY'))
api_clients.append(ticketmaster_api)
logger.info("Initialized Ticketmaster API")

# Add VividSeats API if key is available
vividseats_key = os.getenv('VIVIDSEATS_API_KEY')
if vividseats_key and vividseats_key != "your_vividseats_api_key":
    vividseats_api = VividSeatsAPI(vividseats_key)
    api_clients.append(vividseats_api)
    logger.info("Initialized VividSeats API")
else:
    logger.warning("VividSeats API key not configured")

# Add SeatGeek API if both client ID and secret are available
seatgeek_client_id = os.getenv('SEATGEEK_CLIENT_ID')
seatgeek_client_secret = os.getenv('SEATGEEK_CLIENT_SECRET')
if (seatgeek_client_id and seatgeek_client_id != "your_client_id" and 
    seatgeek_client_secret and seatgeek_client_secret != "your_client_secret"):
    seatgeek_api = SeatGeekAPI(seatgeek_client_id)
    api_clients.append(seatgeek_api)
    logger.info("Initialized SeatGeek API")
else:
    logger.warning("SeatGeek API credentials not configured")

if len(api_clients) == 0:
    logger.error("No API clients initialized. Check your API keys in .env file")
    raise ValueError("No API clients initialized. Check your API keys in .env file")

def cleanup():
    """Cleanup function to be called on shutdown"""
    logger.info("Performing application cleanup...")
    # Add cleanup for each API client if needed
    for api_client in api_clients:
        try:
            if hasattr(api_client, 'cleanup'):
                api_client.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up {api_client.__class__.__name__}: {e}")

# Register cleanup function
atexit.register(cleanup)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/recommendations', methods=['POST', 'OPTIONS'])
def get_recommendations():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.json
    zip_code = data.get('zip_code')
    interests = data.get('interests', [])
    
    if not zip_code:
        return jsonify({'error': 'Missing required parameter: zip_code'}), 400
    
    try:
        logger.info(f"Generating recommendations for zip_code: {zip_code}, interests: {interests}")
        
        # Use the sophisticated recommendation system
        recommendations = generate_event_suggestions(zip_code, interests)
        
        if not recommendations:
            logger.warning("No recommendations generated")
            return jsonify({
                'recommendations': [],
                'message': 'No events found matching your criteria'
            })
            
        # Parse the recommendations into a structured format
        try:
            # The recommendations come as a string from the LLM
            # We need to parse it into a structured format
            recommendations_list = []
            
            # Split the recommendations by newlines and process each event
            current_event = {}
            for line in recommendations.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this is a new event (starts with a number)
                if line[0].isdigit() and '. ' in line:
                    if current_event:
                        recommendations_list.append(current_event)
                    # Split the line into number and content
                    number_content = line.split('. ', 1)
                    if len(number_content) > 1:
                        content = number_content[1]
                        # Split into name and date_venue, but keep the full name
                        parts = content.split(' - ', 1)
                        current_event = {
                            'name': parts[0].strip(),
                            'date_venue': parts[1].strip() if len(parts) > 1 else '',
                            'reasoning': '',
                            'details': {}
                        }
                    else:
                        current_event = {
                            'name': line,
                            'date_venue': '',
                            'reasoning': '',
                            'details': {}
                        }
                elif current_event and line.lower().startswith('reasoning:'):
                    # This is a reasoning line
                    current_event['reasoning'] = line[10:].strip()  # Remove "Reasoning:" prefix
                elif current_event and line:
                    # This is part of the reasoning (continuation)
                    if current_event['reasoning']:
                        current_event['reasoning'] += ' ' + line.strip()
                    else:
                        current_event['reasoning'] = line.strip()
            
            # Add the last event if exists
            if current_event:
                recommendations_list.append(current_event)
                
            if not recommendations_list:
                logger.warning("No events parsed from recommendations")
                return jsonify({
                    'recommendations': [],
                    'message': 'No events found matching your criteria'
                })
                
            logger.info(f"Successfully parsed {len(recommendations_list)} events")
            return jsonify({
                'recommendations': recommendations_list,
                'raw_recommendations': recommendations  # Include raw text for debugging
            })
            
        except Exception as parse_error:
            logger.error(f"Error parsing recommendations: {parse_error}")
            # If parsing fails, return the raw recommendations
            return jsonify({
                'recommendations': [{'raw': recommendations}],
                'error': 'Failed to parse recommendations into structured format'
            })
            
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'active_apis': [api.__class__.__name__ for api in api_clients]
    })

if __name__ == '__main__':
    app.run(debug=True) 