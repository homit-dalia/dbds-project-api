from app import app
from flask import make_response, request
from models.train_model import train_model

obj = train_model()

@app.route('/train/fetch/schedule', methods=["POST"])
def fetch_schedules():
    return make_response(obj.fetch_schedules(data=request.get_json()))

@app.route('/train/fetch/stops', methods=["POST"])
def fetch_stops():
    return make_response(obj.fetch_stops(data=request.get_json()))

@app.route('/train/reserve', methods=["POST"])
def reserve():
    return make_response(obj.reserve_ticket(data=request.get_json()))

@app.route('/train/fetch/reservations', methods=["POST"])
def fetch_reservations():
    return make_response(obj.fetch_reservations(data=request.get_json()))

@app.route('/train/reserve/cancel', methods=["POST"])
def cancel_reservation():
    return make_response(obj.cancel_reservation(data=request.get_json()))