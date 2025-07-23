# 🚗 Vehicle Parking App (V1)

A full-stack multi-user parking management system built using Flask and SQLite. Designed to allow admins to manage parking lots and users to reserve, view, and vacate parking spots—all through a clean, responsive web interface.

## 🔧 Features

### 👤 User Functionality
- User Registration and Login
- Book parking spot in a selected lot
- View current and past bookings
- Vacate spots with real-time cost calculation
- Personalized user dashboard and analytics

### 🛠 Admin Functionality
- Admin login (no registration required)
- Add, edit, and delete parking lots
- Automatically generate and manage spots per lot
- View real-time parking status with filters
- Track users and their reservations
- Interactive visual charts (reservations, revenue, and spot status)

### 🤖 AI Assistant (Bonus)
- Integrated chatbot using Google Gemini 2.0 Flash
- Provides instant user support for parking-related queries

## 🧩 Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, Bootstrap 5, Jinja2
- **Database:** SQLite (programmatically created)
- **Charts & Visuals:** Matplotlib
- **AI Integration:** Google Gemini Flash API

## 📁 Folder Structure
    ├── app.py
    ├── admin.py
    ├── models.py
    ├── templates/
    │ ├── signin.html
    │ ├── dashboard.html
    │ ├── admin_dash.html
    │ └── ...
    ├── static/
    │ ├── charts/
    │ └── ...


