from app import app
from flask import make_response, request
from models.employee_model import employee_model

obj = employee_model()

@app.route('/employee/login', methods=["POST"])
def employee_login():
    return make_response(obj.login(data=request.get_json()))

@app.route('/employee/fetch/reps', methods=["POST"])
def employee_fetch_reps():
    return make_response(obj.fetch_reps(data=request.get_json()))

@app.route('/employee/create/rep', methods=["POST"])
def employee_create_rep():
    return make_response(obj.create_rep(data=request.get_json()))

@app.route('/employee/update/rep', methods=["POST"])
def employee_update_rep():
    return make_response(obj.update_rep(data=request.get_json()))

@app.route('/employee/delete/rep', methods=["POST"])
def employee_delete_rep():
    return make_response(obj.delete_rep(data=request.get_json()))

@app.route('/sales/report', methods=["POST"])
def sales_report():
    return make_response(obj.get_sales_report(data=request.get_json()))

@app.route('/employee/search/reservations', methods=["POST"])
def employee_search_reservations():
    return make_response(obj.search_reservation(data=request.get_json()))

@app.route('/employee/revenue', methods=["POST"])
def employee_revenue():
    return make_response(obj.calculate_revenue(data=request.get_json()))

@app.route('/employee/metadata', methods=["POST"])
def employee_metadata():
    return make_response(obj.get_metadata(data=request.get_json()))