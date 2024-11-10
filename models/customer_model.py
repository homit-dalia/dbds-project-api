from sqlalchemy import Column, String
from app import session, Base
from common import object_as_dict

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
            return ({'success': False, 'message': str(e)}, 500)
    
class Customer(Base):
    __tablename__ = 'customer'
    email = Column(String(100), primary_key=True)
    firstname = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    username = Column(String(50))  # Optional for now
    password = Column(String(255), nullable=False)