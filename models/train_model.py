from app import session, Base
from common import object_as_dict
from sqlalchemy import Column, String, Integer, ForeignKey, Date, Enum, Numeric, DateTime, func, DateTime, Time, Float
from sqlalchemy.orm import relationship, aliased

class train_model():
    def __init__(self) -> None:
        pass

    def fetch_schedules(self, data: dict) -> dict:
        try:
            source_name = data["source"]
            destination_name = data["destination"]
            travel_date = data.get("date")

            # Create aliases for the station table
            source_station = aliased(Station)
            destination_station = aliased(Station)

            # Join station and train_schedule to get schedules by source and destination city names
            query = (session.query(Schedule, source_station.name.label("origin_name"), destination_station.name.label("destination_name"))
                    .join(source_station, Schedule.origin == source_station.station_id)
                    .filter(source_station.city == source_name)
                    .join(destination_station, Schedule.destination == destination_station.station_id)
                    .filter(destination_station.city == destination_name))

            # Filter by date of travel if provided
            if travel_date:
                query = query.filter(func.date(Schedule.departure) == travel_date)

            results = query.all()

            # Validate results
            if not results:
                return ({'success': False, 'message': 'No schedules found.'}, 404)
            
            # Convert results to a dictionary
            schedules = []
            for schedule, origin_name, destination_name in results:
                schedule_dict = {
                    **object_as_dict(schedule),  # Convert Schedule object to dict
                    "origin_name": origin_name,
                    "destination_name": destination_name
                }
                schedules.append(schedule_dict)
            print(schedules)
            return ({'success': True, 'message': 'Schedules fetched successfully.', 'schedules': schedules}, 200)

        except Exception as e:
            session.rollback()
            print(e)    
            return ({'success': False, 'message': f'Error fetching schedules: {str(e)}'}, 500)

    def fetch_stops(self, data: dict) -> dict:
        try:
            transit_line = data["transit_line"]
            # Query the stops for the given transit line
            stops = (session.query(Stops, Station.name.label("station_name"), Station.city.label("city_name"))
                    .join(Station, Stops.station_id == Station.station_id)
                    .filter(Stops.transit_line == transit_line)
                    .order_by(Stops.arrival)
                    .all())

            # Validate stops
            if not stops:
                return ({'success': False, 'message': 'No stops found for the specified transit line.'}, 404)
            
            stops_list = []
            for stop, station_name, city_name in stops:
                stop_dict = object_as_dict(stop)
                stop_dict["station_name"] = station_name
                stop_dict["city_name"] = city_name
                stops_list.append(stop_dict)
            
            return ({'success': True, 'message': 'Stops fetched successfully.', 'stops': stops_list}, 200)
        
        except Exception as e:
            session.rollback()
            print(e)
            return ({'success': False, 'message': f'Error fetching stops: {str(e)}'}, 500)
    
    def reserve_ticket(self, data: dict) -> dict:
        try:
            discount_rates = {
                "child": 0.25,    # 25% discount
                "elderly": 0.35,  # 35% discount
                "disabled": 0.50, # 50% discount
                "regular": 0.0    # No discount for regular passengers
            }

            # Calculate the base discounted price
            discount_rate = discount_rates.get(data["passenger_category"], 0.0)
            discounted_price = data["price"] * (1 - discount_rate)

            reservation = Reservation(
                transit_line=data["transit_line"],
                customer_email=data["customer_email"],
                seat_number="A1",  # Hardcoded for now
                passenger_category=data.get("passenger_category", "regular"),
                price=data["price"],
                discounted_price=discounted_price,
                status="active",
            )

            session.add(reservation)
            session.commit()

            return ({'success': True, 'message': 'Ticket reserved successfully.'}, 200)

        except Exception as e:
            session.rollback()
            print(e)
            return ({'success': False,'message': 'Error reserving ticket. Please try again later.'}, 500)

    def fetch_reservations(self, data: dict) -> dict:
        try:
            email = data["email"]
            reservations = session.query(Reservation).filter_by(customer_email=email).all()

            # Validate reservations
            if not reservations:
                return {'success': False, 'message': 'No reservations found for the specified customer.'}, 404

            reservations_list = [object_as_dict(reservation) for reservation in reservations]
            
            transit_lines = {}
            for reservation in reservations_list:
                transit_line = reservation["transit_line"]
                if transit_line not in transit_lines:
                    schedule = session.query(Schedule).filter_by(transit_line=transit_line).first()
                    transit_lines[transit_line] = object_as_dict(schedule)
            
            for reservation in reservations_list:
                transit_line = reservation["transit_line"]
                reservation["schedule"] = transit_lines[transit_line]
            print(reservations_list)
            return {'success': True, 'message': 'Reservations fetched successfully.', 'reservations': reservations_list}, 200

        except Exception as e:
            session.rollback()
            print(e)
            return {'success': False, 'message': 'Error fetching reservations. Please try again later.'}, 500
        
    def cancel_reservation(self, data: dict) -> dict:
        try:
            reservation_id = data["reservation_id"]
            reservation = session.query(Reservation).filter_by(reservation_id=reservation_id).first()

            # Validate reservation
            if not reservation:
                return {'success': False, 'message': 'Reservation not found.'}, 404
            
            # Update reservation status
            reservation.status = 'cancelled'
            session.commit()

            return {'success': True, 'message': 'Reservation cancelled successfully.'}, 200

        except Exception as e:
            session.rollback()
            print(e)
            return {'success': False, 'message': 'Error cancelling reservation. Please try again later.'}, 500

class Station(Base):
    __tablename__ = 'station'
    station_id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    city = Column(String(20), nullable=False)
    state = Column(String(20), nullable=False)

class Schedule(Base):
    __tablename__ = 'train_schedule'
    transit_line = Column(String(30), primary_key=True)
    departure = Column(DateTime, nullable=False)
    arrival = Column(DateTime, nullable=False)
    origin = Column(String(20), ForeignKey('station.station_id'), nullable=False)
    destination = Column(String(20), ForeignKey('station.station_id'), nullable=False)
    travel_time = Column(Time, nullable=False)
    fare = Column(Float, nullable=False)
    train_id = Column(String(20), ForeignKey('train.train_id'), nullable=False)

    # Relationships
    origin_station = relationship('Station', foreign_keys=[origin])
    destination_station = relationship('Station', foreign_keys=[destination])
    train = relationship('Train', foreign_keys=[train_id])
    reservations = relationship('Reservation', back_populates='train_schedule')

class Train(Base):
    __tablename__ = 'train'
    train_id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)

class Stops(Base):
    __tablename__ = 'stops'
    transit_line = Column(String(30), ForeignKey('train_schedule.transit_line'), primary_key=True)
    station_id = Column(String(20), ForeignKey('station.station_id'), primary_key=True)
    arrival = Column(DateTime, nullable=False)
    departure = Column(DateTime, nullable=False)

    # Relationships
    station = relationship('Station', foreign_keys=[station_id])
    schedule = relationship('Schedule', foreign_keys=[transit_line])
    
class Reservation(Base):
    __tablename__ = 'reservations'

    reservation_id = Column(Integer, primary_key=True, autoincrement=True)  # Corrected column name
    transit_line = Column(String(30), ForeignKey('train_schedule.transit_line'), nullable=False)
    customer_email = Column(String(100), ForeignKey('customer.email'), nullable=False)
    seat_number = Column(String(20), nullable=True)
    passenger_category = Column(
        Enum('regular', 'child', 'elderly', 'disabled', name='passenger_category_enum'),
        default='regular',
        nullable=True
    )
    price = Column(Numeric(10, 2), nullable=False)
    discounted_price = Column(Numeric(10, 2), nullable=False)
    status = Column(
        Enum('active', 'cancelled', name='reservation_status_enum'),
        default='active',
        nullable=True
    )
    created_at = Column(DateTime, default=func.now(), nullable=True)

    # Relationships
    customer = relationship('Customer', back_populates='reservations')
    train_schedule = relationship('Schedule', back_populates='reservations')
