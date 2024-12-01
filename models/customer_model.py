from sqlalchemy import Column, String
from app import session, Base
from common import object_as_dict
from sqlalchemy.orm import relationship
class customer_model():
    def __init__(self) -> None:
        pass

    def login(self, data: dict) -> dict:
        try:
            print("Inside login method")
            email = data["email"]
            password = data["password"]
            
            # Query the customer by email (will add username later)
            customer = session.query(Customer).filter_by(email=email).first()

            # Validate customer
            if not customer:
                return ({'success': False, 'message': 'Customer not found.'}, 404)
            
            # Validate password
            if not password == customer.password:
                return ({'success': False, 'message': 'Invalid password.'}, 401)
            
            # remove password from user object before returning response to frontend
            user = object_as_dict(customer)
            del user['password']
            
            return ({'success': True, 'message': 'Customer validated successfully.', 'user': user}, 200)
        
        except Exception as e:
            session.rollback()
            print(e)
            return ({'success': False, 'message': str(e)}, 500)
    
    def register(self, data: dict) -> dict:
        try:
            print("Inside register method")
            email = data["email"]
            firstname = data["firstname"]
            lastname = data["lastname"]
            password = data["password"]
            username = data["username"]
            
            # Check if customer already exists
            customer_email = session.query(Customer).filter_by(email=email).first()
            customer_username = session.query(Customer).filter_by(username=username).first()
            if customer_email or customer_username:
                return ({'success': False, 'message': 'An account with the same email or username already exists, please try using different credentials.'}, 409)
            
            # Create new customer
            new_customer = Customer(email=email, firstname=firstname, lastname=lastname, username= username, password=password)
            session.add(new_customer)
            session.commit()
            
            return ({'success': True, 'message': 'Customer created successfully.'}, 201)
        
        except Exception as e:
            return ({'success': False, 'message': str(e)}, 500)
    
class Customer(Base):
    __tablename__ = 'customer'
    email = Column(String(100), primary_key=True)
    firstname = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    username = Column(String(50))  # Optional for now
    password = Column(String(255), nullable=False)

    # Define the relationship with Reservation
    reservations = relationship('Reservation', back_populates='customer', cascade='all, delete-orphan')
    queries = relationship('Queries', back_populates='customer', cascade='all, delete-orphan')