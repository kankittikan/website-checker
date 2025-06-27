# Website Status Checker

A simple web application that allows you to monitor the online status of multiple websites. Built with FastAPI and modern UI using Tailwind CSS.

## Features

- Add and remove websites to monitor
- Real-time status checking
- Auto-refresh every 30 seconds
- Modern and responsive UI
- SQLite database storage with SQLAlchemy ORM
- Last checked timestamp for each website

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

3. Open your browser and navigate to:
```
http://localhost:8000
```

## Usage

1. Enter a website URL in the input field (make sure to include http:// or https://)
2. Click "Add Website" to start monitoring
3. The status indicator will show:
   - Green: Website is online
   - Red: Website is offline or unreachable
4. Click "Check All Status" to manually refresh all statuses
5. Click "Remove" to stop monitoring a website
6. Last checked time is displayed for each website

## Technical Details

- Backend: FastAPI
- Database: SQLite with SQLAlchemy ORM
- Frontend: HTML, JavaScript, Tailwind CSS
- Status Check: Async HTTP requests with timeout
- Auto-refresh: Every 30 seconds

## Database Schema

The application uses a SQLite database with the following schema:

```sql
CREATE TABLE websites (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    status BOOLEAN DEFAULT FALSE,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
``` # website-checker
