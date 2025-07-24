from flask import Flask, render_template, request, redirect, url_for,flash, session,get_flashed_messages
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from models import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from admin import admin_bp
import random
import google.generativeai as genai
from datetime import timedelta

app = Flask(__name__)

# Configure session settings
app.secret_key= '19042004'  # Set a secret key for session management
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Set session lifetime

CORS(app)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


#------------------------------------------------------------#
#-------------------------Sign In route----------------------#
#------------------------------------------------------------#
@app.route('/', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "admin":
            session['username'] = 'admin'
            session['role'] = 'admin'
            session.permanent = True  # Make session permanent
            return redirect(url_for('admin.admin_dashboard'))

        user = User.query.filter_by(username=username, password=password).first()
        if not user:
            flash("Invalid credentials, please try again.", "danger")
            return redirect(url_for('signin'))

        session['username'] = user.username
        session['role'] = 'user'
        session.permanent = True  # Make session permanent
        return redirect(url_for('dashboard', username=user.username))

    return render_template('signin.html')


#------------------------------------------------------------#
#-------------------------Sign Up route----------------------#
#------------------------------------------------------------#
@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists, please choose another.", "danger")
            return redirect(url_for('signup'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash("User registered successfully! Please sign in.", "success")
        return redirect(url_for("signin"))

    return render_template('signup.html')

#------------------------------------------------------------#
#------------------- User Dashboard route  -------------------#
#------------------------------------------------------------#
@app.route('/dashboard/<string:username>')
def dashboard(username):
    if 'username' not in session or session['username'] != username:
        flash("Access denied. Please log in first.", "danger")
        return redirect(url_for('signin'))
    session.permanent = True  # Make session permanent
    return render_template("dashboard.html", username=username)

#------------------------------------------------------------#
#------------------- Profile Section route ------------------#
#------------------------------------------------------------#
@app.route('/profile/<username>/')
def profile(username):
    quotes = [
        "Drive safe, someone loves you.",
        "Life is a journey, enjoy the ride.",
        "Keep calm and drive on.",
        "Every mile is a memory.",
        "The road to success is always under construction.",
        "Stay alert, don’t get hurt.",
        "Your destination is never a place, but a new way of seeing things.",
        "Drive like every child on the street is your own.",
        "Safe driving is no accident.",
        "The best car safety device is a rear-view mirror with a cop in it.",
        "A smooth ride is a safe ride."
    ]
    quote = random.choice(quotes)
    return render_template("profile.html", username=username, quote=quote)

#------------------------------------------------------------#
#------------------------ Logout route ----------------------#
#------------------------------------------------------------#
@app.route('/logout/')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('signin'))
#------------------------------------------------------------#
#------------------- Parking lots route --------------------#
#------------------------------------------------------------#
@app.route('/lots/<string:username>/')
def lots(username):
    lots = ParkingLot.query.all() 
    return render_template('lots.html', username=username, lots=lots)


#-------- Reserve spot by giving vehicle number route -----------------#
@app.route('/reserve/<int:lot_id>/<string:username>/', methods=['GET', 'POST'])
def reserve(lot_id, username):
    lot = ParkingLot.query.filter_by(id=lot_id).first()
    spots = lot.spots 
    if request.method == 'POST':
        # Handle reservation logic here
        vehicle_num = request.form.get('vehicle')
        user = User.query.filter_by(username=username).first()
        spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first() 
        if spot:
            reservation = Reservation(spot_id=spot.id, user_id=user.id,vehicle_num=vehicle_num)
            spot.status = 'O'  # Mark spot as occupied
            lot.available_spots -= 1  # Decrease available spots count
            db.session.add(reservation) 
            db.session.commit()
            return render_template('spots.html', lot = lot, spots=spots, username=username, msg="Spot reserved successfully!", type="success")
        return render_template('lots.html', username=username, msg="Spot is not available.", type="alert")  
    if not lot:
        return render_template('lots.html', username=username, msg="Parking lot not found.", type="alert")
    return render_template('spots.html', username=username, lot=lot, spots=spots) 


#------------------------------------------------------------#
#------------------- View Bookings route --------------------#
#------------------------------------------------------------#
@app.route('/bookings/<string:username>/', methods=['GET', 'POST'])
def bookings(username):
    user = User.query.filter_by(username=username).first()
    reservations = Reservation.query.filter_by(user_id=user.id).all() 

    spots = ParkingSpot.query.all() 
    lots = ParkingLot.query.all() 
    return render_template('booking.html', username=username, lots=lots, spots=spots, reservations=reservations) 

#------------------------------------------------------------#
#------------------- Leave Spot route -----------------------#  
#------------------------------------------------------------#
@app.route('/leave/<int:id>/<string:username>/', methods=['GET', 'POST'])
def leave_spot(id, username):
    reservation = Reservation.query.filter_by(id=id).first()
    if reservation:
        spot = ParkingSpot.query.filter_by(id=reservation.spot_id).first()
        lot = ParkingLot.query.filter_by(id=spot.lot_id).first()
        lot.available_spots += 1  
        spot.status = 'A' 
        now = datetime.utcnow()
        duration = now - reservation.parking_timestamp
        hours = duration.total_seconds() / 3600
        reservation.leaving_timestamp = now
        reservation.parking_cost = round(hours * lot.price, 2)

        db.session.commit()
    return redirect(url_for('bookings', username=username, msg="Spot left successfully!", type="success"))

#----------------------------------------------------------------------------#
#---------------------- Stats For User --------------------------------------#
#----------------------------------------------------------------------------#
@app.route("/user/<string:username>/chart/")
def user_chart(username):
    make_user_time_chart(username)
    return render_template("userchart.html", username=username)

#--------------Total Time Parked (Per Booking)-----------------------------#
def make_user_time_chart(username):
    user = User.query.filter_by(username=username).first()
    reservations = Reservation.query.filter_by(user_id=user.id).all()
    labels = []
    durations = []
    for i, res in enumerate(reservations):
        if res.parking_timestamp and res.leaving_timestamp:
            hours = (res.leaving_timestamp - res.parking_timestamp).total_seconds() / 3600
            labels.append(f"Booking {i+1}")
            durations.append(round(hours, 2))
    plt.figure(figsize=(8, 4))
    plt.plot(labels, durations, marker='o', linestyle='-', color='darkgreen')
    plt.title("Total Time Parked (per Booking)")
    plt.xlabel("Booking")
    plt.ylabel("Hours")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig("static/total_time_parked.png")
    plt.close()

#----------------------------------------------------------------------------#
#---------------------- Chatbot for User -------------------------------------#
#----------------------------------------------------------------------------#
# Google Gemini Chatbot Configuration
GOOGLE_API_KEY = "AIzaSyBYWgscTJS7qzzEGD2fn3mRUiruBG1JNFU"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')


@app.route("/chatbot", methods=["GET","POST"])
def chatbot():
    response = None
    if request.method == "POST" or request.method == "GET":
        user_message = request.form.get("message", "")
        prompt = f"""
        You are an AI assistant for a Vehicle Parking Management System.

        Answer the user's question concisely and only if it's related to parking, reservations, or vehicle management. If it's not related, reply: "Please log in to get more details."

        Examples:
        Q: How do I reserve a parking spot?
        A: Visit the 'Reserve Spot' section, select a parking lot, and enter your vehicle number to reserve a spot.

        Q: How can I view my bookings?
        A: Go to the 'My Bookings' section to see all your reservations and their details.

        Q: What should I do if I want to leave a parking spot?
        A: Click on the 'Leave Spot' button next to your reservation to mark the spot as available.

        Q: Will I be charged for parking?
        A: Yes, you will be charged based on the duration of your parking. The cost will be calculated automatically when you leave the spot.

        Q: Will my parking spot be safe?
        A: Yes, all parking spots are monitored and maintained to ensure the safety of your vehicle.

        Now answer this question:
        Q: {user_message}
        A:"""
        reply = model.generate_content(prompt)
        response = reply.candidates[0].content.parts[0].text.strip().replace("\n", " ")
    return render_template("chatbot.html", response=response)


#----------Register the admin------#
app.register_blueprint(admin_bp)
   
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        user = User.query.filter_by(username="admin").first()  # Check if admin user exists
        if not user:
            user = User(username="admin", password="admin")
            admin_cred = User(username="admin", password="admin")
            db.session.add(admin_cred)
            db.session.commit()
    app.run(debug=True)  # Run the Flask app

