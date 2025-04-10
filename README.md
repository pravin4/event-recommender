# Event Recommendations Application

A modern web application that helps users discover local events based on their interests and location.

## Features

- **Location-based Search**: Automatically detects user's location or accepts zip code input
- **Interest-based Recommendations**: Finds events matching user's interests
- **Multiple Event Sources**: Aggregates events from various APIs (Ticketmaster, Meetup, SeatGeek, VividSeats)
- **Personalized Results**: Uses vector-based similarity search to find relevant events
- **Modern UI**: Clean, responsive design with Tailwind CSS
- **Real-time Updates**: Shows loading states and error handling

## Limitations

- Currently returns a maximum of 10 recommendations per search
- Requires API keys for event sources (Ticketmaster, Meetup, etc.)
- Limited to events within 50 miles of the specified location
- Events are filtered for the next 30 days only

## UI Description

The application features a clean, modern interface with the following components:

1. **Main Layout**
   - Light gray background
   - Centered content with proper padding
   - Responsive design that works on all screen sizes

2. **Header**
   - Large, bold "Event Recommendations" title
   - Centered at the top of the page

3. **Search Form**
   - White card with shadow
   - Two input fields:
     - Zip code input with auto-detection
     - Interests input (comma-separated)
   - Blue "Get Recommendations" button
   - Loading spinner during API calls

4. **Recommendations Grid**
   - Responsive grid layout (1 column on mobile, 2 on tablet, 3 on desktop)
   - White event cards with rounded corners
   - Hover effects for better interactivity

5. **Event Cards**
   - Event title and description
   - Icons for date, venue, and price
   - Relevance score with star icon
   - Category tags with deduplication
   - "Get Tickets" button when available
   - Clean typography and spacing

## Technical Stack

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: Python + Flask
- **APIs**: Ticketmaster, Meetup, SeatGeek, VividSeats
- **Vector Search**: OpenAI embeddings for semantic matching

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   npm install
   ```

3. Set up environment variables:
   - Create a `.env` file in the root directory
   - Add required API keys:
     ```
     OPENAI_API_KEY=your_key
     TICKETMASTER_API_KEY=your_key
     MEETUP_API_KEY=your_key
     SEATGEEK_API_KEY=your_key
     VIVIDSEATS_API_KEY=your_key
     ```

4. Start the servers:
   ```bash
   # Backend
   python src/app.py
   
   # Frontend
   cd frontend
   npm run dev
   ```

## API Endpoints

- `GET /api/recommendations`
  - Parameters:
    - `zip_code`: User's location
    - `interests`: List of interests
  - Returns: List of up to 3 event recommendations

## Contributing

Feel free to submit issues and enhancement requests! 