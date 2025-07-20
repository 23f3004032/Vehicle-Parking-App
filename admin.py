from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, ParkingLot, ParkingSpot, User, Reservation
from datetime import datetime

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Admin Dashboard Landing Page
@admin_bp.route("/dashboard")
def admin_dashboard():
    return render_template("admin_dash.html")


# Parking Lot Management Page
@admin_bp.route("/lots")
def manage_lots():
    lots = ParkingLot.query.all()
    return render_template("admin_plm.html", lots=lots)

# Create a New Parking Lot
@admin_bp.route("/manage-lots/create/", methods=["POST"])
def create_lot():
    name = request.form["prime_location_name"]
    address = request.form["address"]
    pincode = request.form["pin_code"]
    price = float(request.form["price"])
    max_spots = int(request.form["maximum_number_of_spots"])

    lot = ParkingLot(
        prime_location_name=name,
        address=address,
        pin_code=pincode,
        price=price,
        maximum_number_of_spots=max_spots,
        available_spots=max_spots,
    )
    db.session.add(lot)
    db.session.commit()

    # Auto-generate parking spots
    for _ in range(max_spots):
        spot = ParkingSpot(lot_id=lot.id, status="A")
        db.session.add(spot)
    db.session.commit()

    return redirect(url_for("admin.manage_lots", lots=ParkingLot.query.all()))

# Edit Parking Lot
@admin_bp.route("/edit_lot/<int:lot_id>/", methods=["POST"])
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    old_max = lot.maximum_number_of_spots

    lot.prime_location_name = request.form["prime_location_name"]
    lot.address = request.form["address"]
    lot.pin_code = request.form["pin_code"]
    lot.price = float(request.form["price"])
    lot.maximum_number_of_spots = int(request.form["maximum_number_of_spots"])
    db.session.commit()

    # Auto-generate new spots if increasing and delete if decreasing
    new_max = lot.maximum_number_of_spots
    if new_max > old_max:
        for _ in range(new_max - old_max):
            spot = ParkingSpot(lot_id=lot.id, status="A")
            db.session.add(spot)
        lot.available_spots += (new_max - old_max)

    else:
        lot.available_spots -= (old_max - new_max)
        for _ in range(old_max - new_max):
            spot = ParkingSpot.query.filter_by(lot_id=lot.id, status="A").first()
            db.session.delete(spot)
    
    db.session.commit()

    return redirect(url_for("admin.manage_lots", lots=ParkingLot.query.all()))

# Delete Parking Lot
@admin_bp.route("/delete_lot/<int:lot_id>/", methods=["POST"])
def delete_lot(lot_id):
    
    # Delete related spots first
    ParkingLot.query.filter_by(id=lot_id).delete()
    db.session.commit()
    return redirect(url_for("admin.manage_lots", lots=ParkingLot.query.all()))

# Live Status Overview
@admin_bp.route("/status")
def lot_status():
    lots = ParkingLot.query.all()
    return render_template("admin_status.html", lots=lots)

# User Management Page
@admin_bp.route("/users")
def manage_users():
    users = User.query.all()
    user_data = []

    for user in users:
        reservations = Reservation.query.filter_by(user_id=user.id).all()
        total = len(reservations)
        user_data.append({
            "id": user.id,
            "username": user.username,
            "reservations": total
        })

    return render_template("admin_usermanage.html", users=user_data)






