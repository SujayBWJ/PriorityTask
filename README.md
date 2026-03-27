# PriorityTask - Intelligent Task Manager

A full-stack task management web application built with Python (Flask), SQLite, and Vanilla JavaScript. It features intelligent capacity management and automatic backlog recalculation.

## Features
- **Intelligent Capacity Management**: Automatically drops lower-priority tasks when daily capacity is exceeded.
- **Backlog Engine**: Identifies missed tasks and re-optimizes the schedule.
- **Secure Auth**: Session-based login with hashed passwords.
- **Glassmorphic UI**: Premium, responsive dark-mode design.

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd "Project - Skill Classes"
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   ```bash
   python app.py
   ```
   The app will automatically initialize the `tasks.db` database on first run.

## Tech Stack
- **Backend**: Python, Flask
- **Database**: SQLite (Raw SQL)
- **Frontend**: HTML5, Vanilla CSS3, Vanilla JavaScript
