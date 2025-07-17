from flask import Flask, render_template, request, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from models import *
app = Flask(__name__)
CORS(app)

# Configurations (example, update as needed)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Example route
@app.route('/dashboard')
def home():
    return render_template('base.html')

# Dashboard route
# @app.route('/dashboard')
# def dashboard():
#     return "Admin/User Dashboard - Status of parking spots and lots."

# Parking lots route
@app.route('/lots')
def lots():
    return "List of all parking lots."

# Reserve spot route
@app.route('/reserve')
def reserve():
    return "Reserve a parking spot."

# Logout route
@app.route('/logout')
def logout():
    return "You have been logged out."

# Sign Up route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Handle user registration logic here
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        # Add user creation logic (hash password, save to DB)
        return "User registered successfully!"  # Replace with redirect or template
    return render_template('signup.html')

# Sign In route
@app.route('/', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        # Handle user authentication logic here
        username = request.form['username']
        password = request.form['password']
        # Add authentication logic (check user, verify password)
        return "User signed in successfully!"  # Replace with redirect or template
    return render_template('signin.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


