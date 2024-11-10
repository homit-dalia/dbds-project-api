from app import app
from flask import make_response, request
from models.customer_model import customer_model

obj = customer_model()

@app.route('/customer/login', methods=["POST"])
def customer_login():
    return make_response(obj.login(data=request.get_json()))