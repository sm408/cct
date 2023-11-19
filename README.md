# Project Title

This is a Flask-based web application for managing club events in a college. The application supports different user roles including students, club members, club coordinators, and administrators. Each role has different permissions and capabilities within the application.

## Features

- **Admin**: Can view all events, approve or reject events.
- **Club**: Can add events, view club members and events.
- **Club Coordinator**: Can approve timesheets, view all events.
- **Student**: Can add timesheets, view clubs they are part of and their events.

## Installation
1. Clone the repository:
    ```
    git clone https://github.com/your-repo/project.git
    ```
2. Navigate to the project directory:
    ```
    cd project
    ```
3. Install the required Python packages:
    ```
    pip install -r requirements.txt
    ```
4. Set up your MySQL database and update the `pass_secret.py` file with your MySQL host, user, password, and database name.

5. Run the Flask application:
    ```
    python app.py
    ```

The application will be accessible at `http://localhost:5000`.

## Usage

After running the application, navigate to `http://localhost:5000` in your web browser. You can log in with different user roles to see their respective dashboards and capabilities.