# Event Recommendation System

This application provides personalized event recommendations based on user interests and location. It aggregates events from multiple sources including Ticketmaster, SeatGeek, Meetup, and Vivid Seats.

## Features

- Fetches real-time events from multiple sources
- Personalized recommendations based on user interests
- Includes event details like dates, locations, prices, and ticket links
- Supports various event categories (art, sports, music, theater, etc.)

## Project Structure

```
event-recommendation-system/
├── src/                    # Source code
│   ├── api/                # API clients
│   │   ├── __init__.py
│   │   └── event_apis.py   # Event API implementations
│   ├── utils/              # Utility functions
│   │   └── __init__.py
│   ├── templates/          # HTML templates
│   ├── __init__.py
│   ├── app.py              # Flask application
│   └── init.py             # Event recommendation logic
├── tests/                  # Test files
│   ├── __init__.py
│   ├── test_apis.py
│   ├── test_ticketmaster.py
│   └── ...
├── frontend/               # Frontend application
├── extension/              # Browser extension
├── .env                    # Environment variables
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Backend Dockerfile
├── main.py                 # Application entry point
├── Procfile                # Procfile for deployment
└── README.md               # Project documentation
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   TICKETMASTER_API_KEY=your_ticketmaster_api_key
   SEATGEEK_API_KEY=your_seatgeek_api_key
   MEETUP_API_KEY=your_meetup_api_key
   VIVIDSEATS_API_KEY=your_vividseats_api_key
   ```

   You can obtain API keys from:
   - OpenAI: https://platform.openai.com/api-keys
   - Ticketmaster: https://developer.ticketmaster.com/
   - SeatGeek: https://seatgeek.com/account/develop
   - Meetup: https://www.meetup.com/api/oauth/
   - Vivid Seats: https://skybox.vividseats.com/api-docs/#/

## Usage

Run the main script:
```bash
python main.py
```

Or using Docker Compose:
```bash
docker-compose up
```

The application will:
1. Fetch events from all configured APIs
2. Filter events based on user interests
3. Generate personalized recommendations using OpenAI's GPT model
4. Display the top 3 recommended events with detailed information

## Customization

You can modify the interests list and zip code in the `main()` function of `src/init.py` to get recommendations for different locations and interests.

## Note

Make sure to keep your API keys secure and never commit them to version control. 