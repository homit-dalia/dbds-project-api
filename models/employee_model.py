from app import session, Base
from datetime import datetime, timedelta
from common import object_as_dict
from sqlalchemy import Column, String, Integer, ForeignKey, Date, Enum, Numeric, DateTime, func, DateTime, Time, Float
from sqlalchemy.orm import relationship, aliased
from models.train_model import Schedule, Station, Stops, Reservation

class employee_model():
    def __init__(self) -> None:
        pass

    def login(self, data: dict) -> dict:
        try:
            email = data["email"]
            password = data["password"]
            
            # Query the employee
            employee = session.query(Employee).filter_by(email=email).first()

            # Validate employee
            if not employee:
                return ({'success': False, 'message': 'Employee not found.'}, 404)
            
            # Validate password
            if not password == employee.password:
                return ({'success': False, 'message': 'Invalid password.'}, 401)
            
            # remove password from user object before returning response to frontend
            user = object_as_dict(employee)
            del user['password']
            print(user)
            return ({'success': True, 'message': 'Employee validated successfully.', 'user': user}, 200)
        except Exception as e:
            session.rollback()
            return ({'success': False, 'message': str(e)}, 500)
        
    def fetch_reps(self, data: dict) -> dict:
        try:
            reps = session.query(Employee).filter_by(type='customer_rep').all()
            
            if not reps:
                return ({'success': False, 'message': 'No reps found.'}, 404)
            
            reps = [object_as_dict(rep) for rep in reps]
            print(reps)
            return ({'success': True, 'message': 'Reps fetched successfully.', 'reps': reps}, 200)
        except Exception as e:
            session.rollback()
            print(f"Error fetching reps: {e}")
            return ({'success': False, 'message': str(e)}, 500)
    
    def create_rep(self, data: dict) -> dict:
        try:
            # Check if an employee with the given SSN already exists
            existing_employee = session.query(Employee).filter_by(ssn=data["ssn"]).first()
            if existing_employee:
                return ({'success': False,'message': f"Employee with SSN {data['ssn']} already exists."}, 400)

            # Create new representative
            rep = Employee(
                ssn=data["ssn"],
                type='customer_rep',  # Default type for representative
                firstname=data["firstname"],
                lastname=data["lastname"],
                username=data["username"],
                email=data["email"],
                password=data["password"]  # Ensure password is hashed
            )

            # Add and commit the new representative
            session.add(rep)
            session.commit()

            print(rep)
            return ({ 'success': True, 'message': 'Representative created successfully.', 'rep': object_as_dict(rep) }, 200)

        except Exception as e:
            # Rollback the session in case of an error 
            session.rollback() 
            print(f"Error creating representative: {e}") 
            return ({ 'success': False, 'message': str(e) }, 500)
        
    def update_rep(self, data: dict) -> dict:
        try:
            # Query the representative
            rep = session.query(Employee).filter_by(ssn=data["ssn"]).first()
            if not rep:
                return ({'success': False, 'message': 'Representative not found.'}, 404)

            # Update the representative
            rep.firstname = data["firstname"]
            rep.lastname = data["lastname"]
            rep.username = data["username"]
            rep.ssn = data["ssn"]
            rep.email = data["email"]
            rep.password = data["password"]

            # Commit the changes
            session.commit()

            print(rep)
            return ({ 'success': True, 'message': 'Representative updated successfully.', 'rep': object_as_dict(rep) }, 200)

        except Exception as e:
            # Rollback the session in case of an error 
            session.rollback() 
            print(f"Error updating representative: {e}") 
            return ({ 'success': False, 'message': str(e) }, 500)
        
    def delete_rep(self, data: dict) -> dict:
        try:
            # Query the representative
            print(data)
            rep = session.query(Employee).filter_by(ssn=data["ssn"]).first()
            if not rep:
                return ({'success': False, 'message': 'Representative not found.'}, 404)

            # Delete the representative
            session.delete(rep)

            # Commit the changes
            session.commit()

            print(rep)
            return ({ 'success': True, 'message': 'Representative deleted successfully.', 'rep': object_as_dict(rep) }, 200)

        except Exception as e:
            # Rollback the session in case of an error 
            session.rollback() 
            print(f"Error deleting representative: {e}") 
            return ({ 'success': False, 'message': str(e) }, 500)

    def get_sales_report() -> dict:
        try:
            # Calculate the date 6 months ago from today
            six_months_ago = datetime.now() - timedelta(days=6 * 30)

            # Query the database to calculate total sales per month for the last 6 months
            sales_report = (
                session.query(
                    func.date_trunc('month', Reservation.created_at).label('month'),  # Truncate to month
                    func.sum(Reservation.discounted_price).label('total_sales')       # Sum discounted prices
                )
                .filter(Reservation.created_at >= six_months_ago)  # Only include the last 6 months
                .filter(Reservation.status == 'active')            # Include only active reservations
                .group_by(func.date_trunc('month', Reservation.created_at))  # Group by month
                .order_by(func.date_trunc('month', Reservation.created_at))  # Order by month
                .all()
            )

            # Transform query results into a list of dictionaries
            sales_data = [
                {'month': month.strftime('%Y-%m'), 'total_sales': float(total_sales)}
                for month, total_sales in sales_report
            ]

            return {'success': True, 'message': 'Sales report fetched successfully.', 'data': sales_data}, 200

        except Exception as e:
            session.rollback()
            print(f"Error fetching sales report: {e}")
            return {'success': False, 'message': str(e)}, 500    
        
    def search_reservation(self, data: dict) -> dict:
        try:
            search_type = data.get("search_type")
            value = data.get("value")
            
            if not search_type or not value:
                return {'success': False, 'message': 'Search type and value are required.'}, 400

            # Base query with filtering based on search type
            if search_type == "transit_line":
                query = session.query(Reservation).filter(Reservation.transit_line == value)
            elif search_type == "customer_email":
                query = session.query(Reservation).filter(Reservation.customer_email == value)
            else:
                return {'success': False, 'message': 'Invalid search type.'}, 400

            # Execute query
            results = query.all()

            if not results:
                return {'success': False, 'message': 'No reservations found.'}, 404

            # Format the results
            reservations = [object_as_dict(reservation) for reservation in results]

            return {'success': True,'message': 'Reservations fetched successfully.','reservations': reservations,}, 200

        except Exception as e:
            session.rollback()
            print(f"Error searching reservations: {e}")
            return {'success': False, 'message': str(e)}, 500

    def calculate_revenue(self, data: dict) -> dict:
        try:
            revenue_type = data.get("type")  # "transit_line", "customer_email", or "month"
            
            if not revenue_type or revenue_type not in ["transit_line", "customer_email", "month"]:
                return {
                    'success': False,
                    'message': 'Invalid or missing type. Must be "transit_line", "customer_email", or "month".'
                }, 400

            # Base query to calculate revenue
            query = session.query(
                func.sum(Reservation.discounted_price).label("total_revenue")
            ).filter(Reservation.status != 'cancelled')  # Exclude cancelled reservations

            if revenue_type == "month":
                # Add month/year grouping
                query = query.add_columns(
                    func.date_format(Reservation.created_at, '%M %Y').label("group_by_field")
                ).group_by("group_by_field").order_by(func.sum(Reservation.discounted_price).desc())
            else:
                # Group by transit_line or customer_email
                query = query.add_columns(
                    getattr(Reservation, revenue_type).label("group_by_field")
                ).group_by(getattr(Reservation, revenue_type)).order_by(func.sum(Reservation.discounted_price).desc())

            # Execute the query
            results = query.all()

            if not results:
                return {'success': False, 'message': 'No revenue data found.'}, 404

            # Format the results
            revenue_data = [
                {'group_by_field': result.group_by_field, 'total_revenue': float(result.total_revenue)}
                for result in results
            ]

            return {'success': True, 'message': 'Revenue data fetched successfully.', 'data': revenue_data}, 200

        except Exception as e:
            session.rollback()
            print(f"Error calculating revenue: {e}")
            return {'success': False, 'message': str(e)}, 500

    def get_metadata(self, data: dict) -> dict:
        try:
            # Best Customer (by total revenue)
            best_customer_query = (
                session.query(
                    Reservation.customer_email.label("customer_email"),
                    func.sum(Reservation.discounted_price).label("total_revenue")
                )
                .filter(Reservation.status != 'cancelled')  # Exclude cancelled reservations
                .group_by(Reservation.customer_email)
                .order_by(func.sum(Reservation.discounted_price).desc())
                .limit(1)
            )
            best_customer_result = best_customer_query.first()
            best_customer = {
                "email": best_customer_result.customer_email,
                "total_revenue": float(best_customer_result.total_revenue)
            } if best_customer_result else None

            # Top 5 Most Active Transit Lines (by number of reservations)
            top_transit_lines_query = (
                session.query(
                    Reservation.transit_line.label("transit_line"),
                    func.count(Reservation.transit_line).label("reservation_count")
                )
                .filter(Reservation.status != 'cancelled')  # Exclude cancelled reservations
                .group_by(Reservation.transit_line)
                .order_by(func.count(Reservation.transit_line).desc())
                .limit(5)
            )
            top_transit_lines_results = top_transit_lines_query.all()
            top_transit_lines = [
                {
                    "transit_line": result.transit_line,
                    "reservation_count": result.reservation_count
                }
                for result in top_transit_lines_results
            ]

            # Response
            return { 'success': True, 'message': 'Statistics fetched successfully.', 'best_customer': best_customer, 'top_transit_lines': top_transit_lines }, 200

        except Exception as e:
            session.rollback()
            print(f"Error fetching statistics: {e}")
            return {'success': False, 'message': str(e)}, 500


        
class Employee(Base):
    __tablename__ = 'employee'

    ssn = Column(String(11), primary_key=True)  # Social Security Number (Primary Key)
    type = Column(Enum('admin', 'customer_rep', name='employee_type_enum'), nullable=False)
    firstname = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Store hashed passwords