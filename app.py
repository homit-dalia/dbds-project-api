from flask import Flask
from flask import make_response
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS on all routes
Base = declarative_base()

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:homitdalia@localhost:3306/railway_booking'
engine = create_engine(
    app.config['SQLALCHEMY_DATABASE_URI'],
    pool_size=10,  # Number of connections in the pool
    max_overflow=20,  # Additional connections allowed beyond pool_size
    pool_timeout=30,  # Timeout in seconds for getting a connection
    pool_recycle=1800,  # Recycle connections every 30 minutes
    echo=True,  # Enable SQL query logging
)
SessionLocal = sessionmaker(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()

@app.route('/')
def hello_world():
    return make_response({"status" : "success", "message": "This is the home page of Online Reservation API."}, 200)

@app.errorhandler(404)
def page_not_found(error):
    return make_response({"status" : "error", "message": "Page/URL not found. Check URL spelling"}, 404)

# @app.after_request
# def set_default_response_type(response):
#     response.headers['Content-Type'] = 'application/json'
    
#     #remove this when deploying to production. This was added to allow localhost (react frontend) to access the api for rent pay link
#     response.headers.add('Access-Control-Allow-Origin', '*') 
#     response.headers.add('Access-Control-Allow-Methods', '*')
#     response.headers.add('Access-Control-Allow-Headers', '*')

from controllers import *