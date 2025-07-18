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
@app.route('/dashboard/<string:username>')
def dashboard(username):
    return render_template('dashboard.html', username=username)  # Replace with actual user data

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
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', msg="Username already exists, please choose another.", type="alert")
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        # Add user creation logic (hash password, save to DB)
        return redirect(url_for("signin", msg="User registered successfully!",type= "success")) # Replace with redirect or template
    return render_template('signup.html')

# Sign In route
@app.route('/', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        # Handle user authentication logic here
        username = request.form.get('username')
        password = request.form.get('password')
        # Add authentication logic (check user, verify password)
        user = User.query.filter_by(username=username, password=password).first()
        if not user:
            return render_template('signin.html',msg="Invalid credentials, please try again.",type="alert")
        return redirect(url_for('dashboard',username=username))  # Replace with redirect or template
    return render_template('signin.html')

# Profile route
@app.route('/profile/<string:username>')
def profile(username):
    return render_template('profile.html', username=username)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)