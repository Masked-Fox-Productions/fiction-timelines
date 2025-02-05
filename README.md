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

- Frontend: React.js with TypeScript
- Backend: Node.js with Express
- Database: PostgreSQL
- Authentication: JWT
- Styling: Tailwind CSS

## Getting Started

### Prerequisites
- Node.js (v18 or higher)
- PostgreSQL (v14 or higher)
- npm or yarn

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file in the root directory with the following variables:
    - `DATABASE_URL`: Your PostgreSQL connection string
    - `JWT_SECRET`: A secret key for JWT authentication
    - `PORT`: The port number to run the server on
4. Start the server: `python app.py`

### Usage

1. Create an account or log in
2. Create a new timeline or fork an existing one

