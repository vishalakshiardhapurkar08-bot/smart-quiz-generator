# Smart Quiz Generator

A beginner-friendly Flask + SQLite DIY project for VS Code.

## Features
- Student registration and login
- Admin login
- Subject/topic/difficulty selection
- Random quiz generation (up to 10 questions)
- Timer
- Automatic scoring
- Answer review
- Result history
- Admin question management

## Demo Accounts
Admin:
- Email: admin@quiz.com
- Password: admin123

## Run in VS Code

1. Open this folder in VS Code.
2. Open Terminal.
3. Create virtual environment:
   `python -m venv venv`
4. Activate:
   Windows PowerShell: `venv\Scripts\Activate.ps1`
   Windows CMD: `venv\Scripts\activate`
5. Install:
   `pip install -r requirements.txt`
6. Run:
   `python app.py`
7. Open:
   `http://127.0.0.1:5000`

The SQLite database is created automatically on first run.

## Note
This is a DIY/academic project. Passwords are stored as plain text for simplicity; for a production system, use password hashing and stronger security.
