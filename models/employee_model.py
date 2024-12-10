from app import session, Base
from datetime import datetime, timedelta
from common import object_as_dict
from sqlalchemy import Column, String, Integer, ForeignKey, Date, Enum, Numeric, DateTime, func, DateTime, Time, Float, Text
from sqlalchemy.orm import relationship, aliased
from models.train_model import Schedule, Station, Stops, Reservation, Train

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
                    func.DATE_FORMAT(Reservation.created_at, '%Y-%m').label('month'),  # Format date to 'YYYY-MM'
                    func.sum(Reservation.discounted_price).label('total_sales')       # Sum discounted prices
                )
                .filter(Reservation.created_at >= six_months_ago)  # Only include the last 6 months
                .filter(Reservation.status == 'active')            # Include only active reservations
                .group_by(func.DATE_FORMAT(Reservation.created_at, '%Y-%m'))  # Group by formatted month
                .order_by(func.DATE_FORMAT(Reservation.created_at, '%Y-%m'))  # Order by month
                .all()
            )

            # Transform query results into a list of dictionaries
            sales_data = [
                {'month': month, 'total_sales': float(total_sales)}
                for month, total_sales in sales_report
            ]

            return {'success': True, 'message': 'Sales report fetched successfully.', 'data': sales_data}, 200

        except Exception as e:
            # Safely rollback session
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
            revenue_type = data.get("type", "transit_line")  # "transit_line", "customer_email", or "month"
            
            if not revenue_type or revenue_type not in ["transit_line", "customer_email", "month"]:
                return {'success': False,'message': 'Invalid or missing type. Must be "transit_line", "customer_email", or "month".'}, 400

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

    def get_trains_for_station(self, data: dict) -> dict:
        try:
            # Extract station name from the input data
            station_name = data.get("station_name")

            if not station_name:
                return {"success": False, "message": "Station name is required."}, 400

            # Query the station ID based on the station name
            station = session.query(Station).filter(Station.name == station_name).first()

            if not station:
                return {"success": False, "message": "Station not found."}, 404

            station_id = station.station_id

            # Fetch train schedules where the station is either the origin or destination
            results = (
                session.query(
                    Train.train_id,
                    Train.name.label("train_name"),
                    Train.type.label("train_type"),
                    Schedule.transit_line,
                    Schedule.origin,
                    Schedule.destination,
                    Schedule.departure,
                    Schedule.arrival,
                    Schedule.fare,  # Include fare
                )
                .join(Schedule, Train.train_id == Schedule.train_id)
                .filter(
                    (Schedule.origin == station_id) | (Schedule.destination == station_id)
                )
                .order_by(Schedule.departure)  # Sort by departure time
                .all()
            )

            # Convert results to a list of dictionaries
            trains = [
                {
                    "train_id": row.train_id,
                    "train_name": row.train_name,
                    "train_type": row.train_type,
                    "transit_line": row.transit_line,
                    "origin": row.origin,
                    "destination": row.destination,
                    "departure": row.departure.strftime("%Y-%m-%d %H:%M:%S"),
                    "arrival": row.arrival.strftime("%Y-%m-%d %H:%M:%S"),
                    "fare": float(row.fare),  # Convert fare to float for JSON serialization
                }
                for row in results
            ]

            if not trains:
                return {"success": False, "message": "No trains found for the given station."}, 404

            return {"success": True, "message": "Trains fetched successfully.", "trains": trains}, 200

        except Exception as e:
            session.rollback()
            print(f"Error fetching trains for station: {e}")
            return {"success": False, "message": str(e)}, 500

    def get_customers_by_transit_line_and_date(self, data: dict) -> dict:
        try:
            # Extract input data
            transit_line = data.get("transit_line")
            travel_date = data.get("travel_date")

            # Validate input
            if not transit_line or not travel_date:
                return {'success': False, 'message': 'Transit line and travel date are required.'}, 400

            # Parse travel date
            try:
                travel_date = datetime.strptime(travel_date, "%Y-%m-%d")
            except ValueError:
                return {'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'}, 400

            # Query to find customers with reservations for the specified transit line and date
            results = (
                session.query(
                    Reservation.customer_email,
                    Reservation.passenger_category,
                    Reservation.seat_number,
                    Reservation.price,
                    Reservation.discounted_price,
                    Reservation.status
                )
                .join(Schedule, Schedule.transit_line == Reservation.transit_line)
                .filter(Reservation.transit_line == transit_line)
                .filter(func.date(Schedule.departure) == travel_date.date())
                .filter(Reservation.status == 'active')  # Only include active reservations
                .all()
            )

            # Transform results into a list of dictionaries
            customers = [
                {
                    "customer_email": row.customer_email,
                    "passenger_category": row.passenger_category,
                    "seat_number": row.seat_number or "N/A",
                    "price": float(row.price),
                    "discounted_price": float(row.discounted_price),
                    "status": row.status
                }
                for row in results
            ]

            if not customers:
                return {'success': False, 'message': 'No customers found for the given transit line and date.'}, 404

            return {'success': True, 'message': 'Customers fetched successfully.', 'customers': customers}, 200

        except Exception as e:
            session.rollback()
            print(f"Error fetching customers for transit line and date: {e}")
            return {'success': False, 'message': str(e)}, 500

    def update_train_data(self, data: dict) -> dict:
        try:
            # Extract train_id and updated fields from the input data
            train_id = data.get("train_id")

            if not train_id:
                return {"success": False, "message": "Train ID is required."}, 400

            # Query the train record by train_id
            train = session.query(Train).filter(Train.train_id == train_id).first()

            if not train:
                return {"success": False, "message": "Train not found."}, 404

            # Validate and update the train fields
            if "train_name" in data:
                train.name = data["train_name"]
            if "type" in data:
                train.type = data["type"]
                
            # Validate and update the schedule fields if provided
            if "origin" in data or "destination" in data:
                origin = data.get("origin")
                destination = data.get("destination")

                # Validate origin and destination station IDs
                if origin:
                    origin_station = session.query(Station).filter(Station.station_id == origin).first()
                    if not origin_station:
                        return {"success": False, "message": "Invalid origin station ID."}, 400
                if destination:
                    destination_station = session.query(Station).filter(Station.station_id == destination).first()
                    if not destination_station:
                        return {"success": False, "message": "Invalid destination station ID."}, 400

                # Update the schedule
                schedule = session.query(Schedule).filter(Schedule.train_id == train_id).first()
                if not schedule:
                    return {"success": False, "message": "Schedule not found for the train."}, 404

                if origin:
                    schedule.origin = origin
                if destination:
                    schedule.destination = destination

            # Update other schedule fields
            if "departure" in data:
                schedule.departure = data["departure"]
            if "arrival" in data:
                schedule.arrival = data["arrival"]
            if "fare" in data:
                schedule.fare = data["fare"]

            # Commit the changes
            session.commit()

            return { "success": True, "message": "Train data updated successfully."}, 200

        except Exception as e:
            session.rollback()
            print(f"Error updating train data: {e}")
            return {"success": False, "message": str(e)}, 500

    def fetch_queries(self, data: dict) -> dict:
        try:
            keyword = data.get("keyword", "").strip()

            # Base query
            query = session.query(Queries)

            # Apply filtering if keyword is provided
            if keyword:
                query = query.filter(Queries.question.like(f"%{keyword}%"))

            # Limit results to 5 for default fetch
            query = query.order_by(Queries.created_time.desc())
            
            if (data.get("limit")):
                query = query.limit(data.get("limit"))

            # Execute query
            results = query.all()

            if not results:
                return {"success": False, "message": "No queries found."}, 404

            # Convert results to dictionaries
            queries = [
                {
                    "query_id": q.query_id,
                    "customer_id": q.customer_id,
                    "question": q.question,
                    "answer": q.answer,
                    "employee_id": q.employee_id,
                    "created_time": q.created_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "answered_time": q.answered_time.strftime("%Y-%m-%d %H:%M:%S")
                    if q.answered_time
                    else None,
                }
                for q in results
            ]

            return {"success": True, "message": "Queries fetched successfully.", "queries": queries}, 200

        except Exception as e:
            session.rollback()
            print(f"Error fetching queries: {e}")
            return {"success": False, "message": str(e)}, 500

    
    def create_query(self, data: dict) -> dict:
        try:
            print(data)
            # Extract required data from the request
            customer_id = data.get("customer_id")
            question = data.get("question")

            if not customer_id or not question:
                return {"success": False, "message": "Customer ID and question are required."}, 400

            # Create a new query
            new_query = Queries(
                customer_id=customer_id,
                question=question,
                created_time=datetime.now()
            )

            # Add and commit to the database
            session.add(new_query)
            session.commit()

            return { "success": True, "message": "Query created successfully.", "query": { "query_id": new_query.query_id, "customer_id": new_query.customer_id, "question": new_query.question, "created_time": new_query.created_time.strftime("%Y-%m-%d %H:%M:%S") } }, 200

        except Exception as e:
            session.rollback()
            print(f"Error creating query: {e}")
            return {"success": False, "message": str(e)}, 500

    def answer_query(self, data: dict) -> dict:
        try:
            # Extract required data from the request
            query_id = data.get("query_id")
            employee_id = data.get("employee_id")
            answer = data.get("answer")

            if not query_id or not answer:
                return {"success": False, "message": "Query ID and answer are required."}, 400

            # Retrieve the query from the database
            query = session.query(Queries).filter(Queries.query_id == query_id).first()

            if not query:
                return {"success": False, "message": "Query not found."}, 404

            # Update the query with the answer and employee ID
            query.answer = answer
            query.employee_id = employee_id
            query.answered_time = datetime.now()

            # Commit the changes to the database
            session.commit()

            return { "success": True, "message": "Query answered successfully.", "query": { "query_id": query.query_id, "customer_id": query.customer_id, "question": query.question, "answer": query.answer, "employee_id": query.employee_id, "created_time": query.created_time.strftime("%Y-%m-%d %H:%M:%S"), "answered_time": query.answered_time.strftime("%Y-%m-%d %H:%M:%S"), } }, 200

        except Exception as e:
            session.rollback()
            print(f"Error answering query: {e}")
            return {"success": False, "message": str(e)}, 500

    def delete_train_schedule(self, data: dict) -> dict:
        try:
            # Extract transit_line from the input data
            transit_line = data.get("transit_line")

            if not transit_line:
                return {"success": False, "message": "Transit Line is required."}, 400

            # Query the train schedule based on the transit_line
            schedule = session.query(Schedule).filter(Schedule.transit_line == transit_line).first()

            if not schedule:
                return {"success": False, "message": "Train schedule not found."}, 404

            # Delete the schedule
            session.delete(schedule)
            session.commit()

            return {"success": True, "message": "Train schedule deleted successfully."}, 200

        except Exception as e:
            # Rollback the transaction in case of an error
            session.rollback()
            print(f"Error deleting train schedule: {e}")
            return {"success": False, "message": "An error occurred while deleting the train schedule."}, 500

    
class Employee(Base):
    __tablename__ = 'employee'

    ssn = Column(String(11), primary_key=True)  # Social Security Number (Primary Key)
    type = Column(Enum('admin', 'customer_rep', name='employee_type_enum'), nullable=False)
    firstname = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Store hashed passwords
    
    queries = relationship('Queries', back_populates='employee')

    
class Queries(Base):
    __tablename__ = 'queries'

    query_id = Column(Integer, primary_key=True, autoincrement=True)  # Unique query ID
    customer_id = Column(String(100), ForeignKey('customer.email', ondelete='CASCADE'), nullable=False)  # Customer ID (required)
    question = Column(Text, nullable=False)  # The query/question (required)
    employee_id = Column(String(100), ForeignKey('employee.email', ondelete='SET NULL'))  # Employee ID (optional)
    answer = Column(Text, nullable=True)  # Answer to the query (optional)
    created_time = Column(DateTime, nullable=False)  # Time the query was created
    answered_time = Column(DateTime, nullable=True)  # Time the query was answered (optional)

    # Relationships (optional, depending on how you handle relationships in your ORM setup)
    customer = relationship('Customer', back_populates='queries')
    employee = relationship('Employee', back_populates='queries')
