from flask import Blueprint, render_template, request, redirect, url_for, flash,session
from models import db, ParkingLot, ParkingSpot, User, Reservation
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ------------------------- Admin Dashboard Landing Page ----------------------------#
@admin_bp.route("/dashboard")
def admin_dashboard():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Access denied. Please log in as admin.", "danger")
        return redirect(url_for('signin'))
    return render_template("admin_dash.html")

#----------------------------------------------------------------------------#
#------------------- -------Parking Lot Management --------------------------#
#----------------------------------------------------------------------------#
@admin_bp.route("/lots")
def manage_lots():
    lots = ParkingLot.query.all()
    return render_template("admin_plm.html", lots=lots)

#------------- Create a New Parking Lot -------------------#
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

    #-------- Auto-generate parking spots for created lot----------#
    for _ in range(max_spots):
        spot = ParkingSpot(lot_id=lot.id, status="A")
        db.session.add(spot)
    db.session.commit()

    return redirect(url_for("admin.manage_lots", lots=ParkingLot.query.all()))

#----------------------- Edit Parking Lot Details ---------------------#
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

    #------- Auto-generate new spots if increasing and delete if decreasing--------#
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

#------------------- Completely Delete the Parking Lot------------------#
@admin_bp.route("/delete_lot/<int:lot_id>/", methods=["POST"])
def delete_lot(lot_id):
    ParkingLot.query.filter_by(id=lot_id).delete()
    delete_spots(lot_id)  # Delete all spots associated with the lot
    db.session.commit()
    return redirect(url_for("admin.manage_lots", lots=ParkingLot.query.all()))

def delete_spots(lot_id):
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    for spot in spots:
        db.session.delete(spot)
    db.session.commit()

#----------------------------------------------------------------------------#
#--------------------- Live Status Overview ---------------------------------#
#----------------------------------------------------------------------------#
@admin_bp.route("/status")
def lot_status():
    lots = ParkingLot.query.all()
    return render_template("admin_status.html", lots=lots)

#-----------------Live Status with Spot-Level Details-----------------------#
@admin_bp.route("/status/<int:lot_id>")
def view_spots(lot_id):
    lots = ParkingLot.query.all()
    selected_lot = ParkingLot.query.get_or_404(lot_id)

    #------ Filtering logic----------------#
    search_id = request.args.get("search_id", "")
    status_filter = request.args.get("status_filter", "")

    #---------Filter spots------------------#
    filtered_spots = selected_lot.spots
    if search_id:
        filtered_spots = [s for s in filtered_spots if str(s.id) == search_id]
    if status_filter:
        filtered_spots = [s for s in filtered_spots if s.status == status_filter]

    return render_template(
        "admin_status.html",
        lots=lots,
        selected_lot=selected_lot,
        filtered_spots=filtered_spots,
    )


#----------------------------------------------------------------------------#
#----------- User Management(all details available in data)------------------#
#----------------------------------------------------------------------------#
@admin_bp.route("/users")
def manage_users():
    users = User.query.all()
    user_data = []

    for user in users:
        if user.username == "admin":
            continue
        reservations = Reservation.query.filter_by(user_id=user.id).all()
        total = len(reservations)
        user_data.append({
            "id": user.id,
            "username": user.username,
            "reservations": total
        })

    return render_template("admin_usermanage.html", users=user_data)

#----------------------------------------------------------------------------#
# Analytics For Admin
#----------------------------------------------------------------------------#

STATIC_PATH = "static"  # My Flask static directory

@admin_bp.route("/charts")
def admin_chart():     #Making Charts for Admin Dashboard
    make_reservations_chart()
    make_spot_status_chart()
    make_revenue_chart()
    return render_template("adminchart.html")

#-----------------------Reservations per lot chart ------------------#
def make_reservations_chart():
    lots = ParkingLot.query.all()
    reservations = Reservation.query.all()
    spots = ParkingSpot.query.all()

    spot_to_lot = {spot.id: spot.lot_id for spot in spots}
    lot_id_to_name = {lot.id: lot.prime_location_name for lot in lots}
    lot_counts = {lot.id: 0 for lot in lots}

    for res in reservations:
        lot_id = spot_to_lot.get(res.spot_id)
        if lot_id in lot_counts:
            lot_counts[lot_id] += 1

    names = [lot_id_to_name[lot_id] for lot_id in lot_counts]
    counts = [lot_counts[lot_id] for lot_id in lot_counts]

    plt.figure(figsize=(6, 4))
    plt.bar(names, counts, color="royalblue")
    plt.title("Total Reservations per Lot")
    plt.ylabel("Reservations")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_PATH, "reservations.png"))
    plt.close()

#------------------ Spot Status Chart(available vs Occupied)------------------#
def make_spot_status_chart():
    available = ParkingSpot.query.filter_by(status='A').count()
    occupied = ParkingSpot.query.filter_by(status='O').count()

    plt.figure(figsize=(6, 4))
    plt.pie([available, occupied], labels=["Available", "Occupied"], colors=["green", "red"], autopct="%1.1f%%")
    plt.title("Overall Spot Status")
    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_PATH, "spot_status.png"))
    plt.close()

#----------------------- Revenue per Lot Chart - ------------------#   
def make_revenue_chart():
    lots = ParkingLot.query.all()
    reservations = Reservation.query.all()
    spots = ParkingSpot.query.all()

    spot_to_lot = {spot.id: spot.lot_id for spot in spots}
    lot_id_to_price = {lot.id: lot.price for lot in lots}
    lot_id_to_name = {lot.id: lot.prime_location_name for lot in lots}
    lot_revenue = {lot.id: 0 for lot in lots}

    for res in reservations:
        lot_id = spot_to_lot.get(res.spot_id)
        if lot_id in lot_revenue:
            lot_revenue[lot_id] += lot_id_to_price[lot_id]

    names = [lot_id_to_name[lot_id] for lot_id in lot_revenue]
    revenues = [lot_revenue[lot_id] for lot_id in lot_revenue]

    plt.figure(figsize=(6, 4))
    plt.barh(names, revenues, color="orange")
    plt.title("Revenue per Lot (₹)")
    plt.xlabel("Revenue")
    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_PATH, "chart_revenue.png"))
    plt.close()
