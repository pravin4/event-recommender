import signal
import sys
import os
from src.app import app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info('Received shutdown signal. Performing cleanup...')
    # Add any cleanup code here (e.g., closing database connections)
    sys.exit(0)

def run_server():
    """Run the Flask server with signal handling"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination

    port = int(os.getenv('PORT', 8081))
    retries = 3
    
    while retries > 0:
        try:
            logger.info(f'Starting server on port {port}')
            app.run(debug=True, host="0.0.0.0", port=port, use_reloader=False)
            break
        except OSError as e:
            if 'Address already in use' in str(e):
                logger.warning(f'Port {port} is in use. Attempting to kill existing process...')
                try:
                    # Try to kill the process using the port
                    os.system(f"lsof -ti :{port} | xargs kill -9")
                    logger.info(f'Successfully killed process on port {port}')
                except Exception as kill_error:
                    logger.error(f'Failed to kill process: {kill_error}')
                    port += 1  # Try the next port
                retries -= 1
                if retries == 0:
                    logger.error('Failed to start server after multiple attempts')
                    sys.exit(1)
            else:
                logger.error(f'Error starting server: {e}')
                sys.exit(1)

if __name__ == "__main__":
    run_server() 