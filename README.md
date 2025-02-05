# Fiction Timelines

A modern web application for creating, visualizing, and sharing fictional timelines. Perfect for fan communities who want to map out events in their favorite fictional universes, from Middle Earth to a galaxy far, far away.

## Features

### Timeline Creation & Management
- Create custom timelines with arbitrary dating systems
- Fork existing timelines while maintaining attribution
- Collaborative editing with permission controls
- Event management with conflict detection

### Event Features
- Add, edit, and delete events
- Custom labels and filtering
- Rich text descriptions
- Event categorization and tagging
- Conflict detection for overlapping events

### Visualization & Sharing
- Dynamic, interactive timeline visualization
- Customizable display options
- Social media sharing
- Embeddable timeline widgets
- Export timeline data

### User Management
- User accounts and authentication
- Timeline ownership and permissions
- Collaborative editing
- Activity tracking

## Technology Stack

- Backend: Python with Flask
- Frontend: HTML, CSS, JavaScript
- Database: PostgreSQL
- Authentication: Flask-Login
- Styling: Bootstrap 5
- Template Engine: Jinja2

## Getting Started

### Prerequisites
- Python 3.8 or higher
- PostgreSQL (v14 or higher)
- pip

### Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file in the root directory with the following variables:
    - `DATABASE_URL`: Your PostgreSQL connection string
    - `SECRET_KEY`: A secret key for Flask sessions
    - `FLASK_ENV`: Set to 'development' or 'production'
5. Initialize the database: `flask db upgrade`
6. Start the development server: `flask run`

### Usage

1. Create an account or log in
2. Create a new timeline or fork an existing one

