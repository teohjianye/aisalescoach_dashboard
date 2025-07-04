# AI Sales Coaching Web Dashboard

A Flask-based web application for viewing and analyzing sales call recordings and AI-generated feedback from the AI Sales Coaching mobile app.

## Features

- **Live Data Integration**: Uses the same Azure PostgreSQL database as the mobile app
- **Dashboard Analytics**: Overview statistics with call method performance and sales rep rankings
- **Call History**: Complete call history with advanced filtering capabilities
- **Real-time Filtering**: Filter by call method, sales rep, and outcome
- **Detailed Call Analysis**: View conversation transcripts with AI-generated feedback
- **Modern UI**: Responsive design using Tailwind CSS with interactive charts

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Database

The application connects to the **same Azure PostgreSQL database** used by the Flutter mobile app:

- **Host**: `aisalescoach.postgres.database.azure.com`
- **Database**: `postgres`
- **Tables**: `call_records`, `conversation_turns`, `call_feedback`

This ensures complete data synchronization between the mobile app and web dashboard. All calls recorded on the mobile app immediately appear in the web dashboard.

## Development

- **Backend**: Flask with PostgreSQL using psycopg2
- **Frontend**: HTML, JavaScript, and Tailwind CSS
- **Charts**: Chart.js for interactive data visualizations
- **API**: RESTful endpoints returning JSON data
- **Responsive**: Works on both desktop and mobile devices

## API Endpoints

### Core Data
- `GET /api/calls` - Get list of all calls
- `GET /api/calls/<call_id>` - Get detailed information for a specific call
- `POST /api/calls/<call_id>/update` - Update call information
- `POST /api/calls/new` - Create new call record

### Dashboard & Analytics
- `GET /api/dashboard/overview` - Get dashboard overview with statistics
- `GET /api/calls/filter` - Get filtered calls by method, rep, or outcome

### Query Parameters for Filtering
- `call_type` - Filter by call method (Phone Call, Google Meet, etc.)
- `sales_rep` - Filter by sales representative name
- `outcome` - Filter by call outcome (Won, Lost, Follow up required, Escalated)

## Live Data Features

The webapp shows real-time data from the mobile app including:

- **Call Records**: All recordings made through the mobile app
- **Conversation Transcripts**: Complete AI-transcribed conversations with speaker identification
- **AI Feedback**: Detailed coaching feedback and scores generated by the mobile app
- **Performance Analytics**: Aggregated statistics across call methods and sales reps

## Testing

To verify the database connection and functionality:

```bash
python test_api.py
```

This will test all API endpoints and confirm live data integration.
