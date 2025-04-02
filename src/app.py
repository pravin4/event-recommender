from flask import Flask, render_template, request, jsonify
from src.init import generate_event_suggestions
from flask_cors import CORS
import os
from src.api.event_apis import TicketmasterAPI, VividSeatsAPI, SeatGeekAPI
import atexit
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",  # Local development
            "https://your-frontend-domain.com",  # Production frontend
        ],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize API clients
api_clients = []

# Always include Ticketmaster API
ticketmaster_api = TicketmasterAPI(os.getenv('TICKETMASTER_API_KEY'))
api_clients.append(ticketmaster_api)

# Add VividSeats API if key is available
vividseats_key = os.getenv('VIVIDSEATS_API_KEY')
if vividseats_key and vividseats_key != "your_vividseats_api_key":
    vividseats_api = VividSeatsAPI(vividseats_key)
    api_clients.append(vividseats_api)

# Add SeatGeek API if both client ID and secret are available
seatgeek_client_id = os.getenv('SEATGEEK_CLIENT_ID')
seatgeek_client_secret = os.getenv('SEATGEEK_CLIENT_SECRET')
if (seatgeek_client_id and seatgeek_client_id != "your_client_id" and 
    seatgeek_client_secret and seatgeek_client_secret != "your_client_secret"):
    seatgeek_api = SeatGeekAPI(seatgeek_client_id)
    api_clients.append(seatgeek_api)

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

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    data = request.json
    zip_code = data.get('zip_code')
    interests = data.get('interests', [])
    
    if not zip_code or not interests:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        recommendations = generate_event_suggestions(zip_code, interests)
        return jsonify({'recommendations': recommendations})
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