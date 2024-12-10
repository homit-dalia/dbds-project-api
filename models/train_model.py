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
            origin_city_original = source_name
            
            destination_name = data["destination"]
            destination_city_original = destination_name
            
            travel_date = data.get("date")
            
            if source_name == destination_name:
                return {'success': False, 'message': 'Source and destination cannot be the same.'}, 400

            # Create aliases for the station table
            source_station = aliased(Station)
            destination_station = aliased(Station)

            schedules = []

            # Query 1: Source -> Destination (direct)
            direct_query = (
                session.query(Schedule, source_station.name.label("origin_name"), destination_station.name.label("destination_name"))
                .join(source_station, Schedule.origin == source_station.station_id)
                .filter(source_station.city == source_name)
                .join(destination_station, Schedule.destination == destination_station.station_id)
                .filter(destination_station.city == destination_name)
            )
            if travel_date:
                direct_query = direct_query.filter(func.date(Schedule.departure) == travel_date)
            direct_results = direct_query.all()

            for schedule, origin_name, destination_name in direct_results:
                schedules.append({
                    **object_as_dict(schedule),
                    "origin_name": origin_name,
                    "origin_id": schedule.origin,
                    "destination_id": schedule.destination,
                    "destination_name": destination_name,
                    "via_stop": False,
                    "departure_time_final": schedule.departure,
                    "arrival_time_final": schedule.arrival
                })

            # Query 2: Source -> Stop
            source_to_stop_query = (
                session.query(Schedule, Stops, source_station.name.label("origin_name"), destination_station.station_id, destination_station.name.label("stop_name"), destination_station.city.label("stop_city"))
                .join(Stops, Schedule.transit_line == Stops.transit_line)
                .join(source_station, Schedule.origin == source_station.station_id)
                .filter(source_station.city == source_name)
                .join(destination_station, Stops.station_id == destination_station.station_id)
            )
            if travel_date:
                source_to_stop_query = source_to_stop_query.filter(func.date(Schedule.departure) == travel_date)
            source_to_stop_results = source_to_stop_query.all()
            # print("Source to stop results: ", source_to_stop_results)
            for schedule, stop, origin_name, destination_id, stop_name, stop_city in source_to_stop_results:
                if stop_city == destination_name:
                    schedules.append({
                        **object_as_dict(schedule),
                        "origin_name": origin_name,
                        "destination_name": stop_name,
                        "origin_id": schedule.origin,
                        "destination_id": destination_id,
                        "via_stop": True,
                        "stop_details": {
                            "stop_station_id": stop.station_id,
                            "stop_arrival": stop.arrival,
                            "stop_departure": stop.departure
                        },
                        "departure_time_final": schedule.departure,
                        "arrival_time_final": stop.arrival,
                        "via_source": True
                    })

            # Query 3: Stop -> Destination
            stop_to_destination_query = (
                session.query(Schedule, Stops, source_station.station_id, source_station.name.label("stop_name"), destination_station.name.label("destination_name"))
                .join(Stops, Schedule.transit_line == Stops.transit_line)
                .join(source_station, Stops.station_id == source_station.station_id)
                .filter(source_station.city == source_name)
                .join(destination_station, Schedule.destination == destination_station.station_id)
                .filter(destination_station.city == destination_name)
            )
            if travel_date:
                stop_to_destination_query = stop_to_destination_query.filter(func.date(Schedule.departure) == travel_date)
            stop_to_destination_results = stop_to_destination_query.all()

            for schedule, stop, source_id, stop_name, destination_name in stop_to_destination_results:
                schedules.append({
                    **object_as_dict(schedule),
                    "origin_name": stop_name,
                    "origin_id": source_id,
                    "destination_name": destination_name,
                    "destination_id": schedule.destination,
                    "via_stop": True,
                    "stop_details": {
                        "stop_station_id": stop.station_id,
                        "stop_arrival": stop.arrival,
                        "stop_departure": stop.departure
                    },
                    "departure_time_final": stop.departure,
                    "arrival_time_final": schedule.arrival,
                })

            # Query 4: Stop -> Stop
            stops_query = (
                session.query(
                    Stops.transit_line,
                    Stops.station_id,
                    Station.name.label('station_name'),
                    Station.city.label('station_city'),
                    Station.state.label('station_state'),
                    Stops.arrival,
                    Stops.departure
                )
                .join(Station, Stops.station_id == Station.station_id)
                .filter(Station.city == source_name)  # Filter by source city
            )

            # Execute the query and fetch stops
            stops = stops_query.all()
            print("All stops: ", stops)
            for stop in stops:
                transit_line = stop.transit_line
                transit_stops_query = (
                    session.query(
                        Stops,
                        Station.name.label('station_name'),
                        Station.city.label('station_city'),
                        Station.state.label('station_state'),
                        Stops.arrival,
                        Stops.departure,
                        Stops.station_id
                    )
                    .join(Station, Stops.station_id == Station.station_id)
                    .filter(Stops.transit_line == transit_line)
                    .order_by(Stops.arrival)
                )

                transit_stops = transit_stops_query.all()
                print("\nTransit stops query: ", transit_stops)

                destination_stop = []
                origin_index = None
                destination_index = None
                for i, transit_stop in enumerate(transit_stops):
                    if transit_stop.station_city == origin_city_original:
                        print("Origin city found")
                        print("Transit stop: ", transit_stop.station_name)
                        origin_index = i
                    
                    if transit_stop.station_city == destination_city_original and origin_index is not None:
                        print("Destination city found")
                        print("Transit stop: ", transit_stop.station_name)
                        destination_stop.append(transit_stop)
                        break
                
                if destination_stop:
                    source_station_name = transit_stops[origin_index].station_name
                    destination_station_name = destination_stop[0].station_name
                    schedule = session.query(Schedule).filter_by(transit_line=transit_line).first()

                    response = {
                        **object_as_dict(schedule),
                        "origin_name": source_station_name,
                        "origin_id": transit_stops[origin_index].station_id,
                        "destination_name": destination_station_name,
                        "destination_id": destination_stop[0].station_id,
                        "via_stop": True,
                        "stop_details": {
                            "stop_station_id": stop.station_id,
                            "stop_arrival": stop.arrival,
                            "stop_departure": stop.departure
                        },
                        "departure_time_final": stop.departure,
                        "arrival_time_final": destination_stop[0].arrival
                    }
                    schedules.append(response)

            # Validate results
            if not schedules:
                return {'success': False, 'message': 'No schedules found.'}, 404

            # Further processing and finalizing schedules
            transit_lines = []
            final_schedules = []

            for schedule in schedules:
                if schedule["transit_line"] not in transit_lines:
                    try:
                        all_stops = self.fetch_stops({"transit_line": schedule["transit_line"]})[0]["stops"]
                    except:
                        all_stops = []
                    schedule["all_stops"] = all_stops

                    # Fetch the names of origin and destination stations
                    schedule["transit_origin_name"] = object_as_dict(
                        session.query(Station).filter_by(station_id=schedule["origin"]).first()
                    )["name"]
                    schedule["transit_destination_name"] = object_as_dict(
                        session.query(Station).filter_by(station_id=schedule["destination"]).first()
                    )["name"]

                    # Calculate fare per stop
                    total_fare = schedule["fare"]
                    fare_per_stop = total_fare / (len(all_stops) + 1)

                    # Calculate stops_travelled
                    stops_travelled = 0
                    start_counting = True if schedule.get("via_source", None) else False

                    if schedule["via_stop"]:
                        print("Via stop")
                        for stop in all_stops:
                            print(stop["station_name"])
                            print("Origin Name", schedule["origin_name"])
                            # Start counting after reaching the origin
                            if stop["station_name"] == schedule["origin_name"]:
                                print("Start counting")
                                start_counting = True
                                continue
                            # Stop counting when reaching the destination
                            if stop["station_name"] == schedule["destination_name"]:
                                print("Stop counting")
                                break
                            # Increment stops_travelled only if counting has started
                            if start_counting:
                                print("Incrementing stops_travelled")
                                stops_travelled += 1

                        # Calculate fare for the stops travelled
                        total_fare = fare_per_stop * (stops_travelled + 1)  # +1 to include the destination
                        schedule["final_fare"] = total_fare
                    else:
                        print("Not via stop")
                        schedule["final_fare"] = total_fare

                    # Append the schedule to the final list
                    final_schedules.append(schedule)

                transit_lines.append(schedule["transit_line"])

            return {'success': True, 'message': 'Schedules fetched successfully.', 'schedules': final_schedules}, 200

        except Exception as e:
            session.rollback()
            print(e)
            return {'success': False, 'message': f'Error fetching schedules: {str(e)}'}, 500


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
                source_station_id=data["source_station_id"],
                destination_station_id=data["destination_station_id"]
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
                    schedule = object_as_dict(schedule)
                    
                    # Fetch the names of origin and destination stations
                    schedule["origin_name"] = object_as_dict(session.query(Station).filter_by(station_id=reservation["source_station_id"]).first())["name"]
                    schedule["destination_name"] = object_as_dict(session.query(Station).filter_by(station_id=reservation["destination_station_id"]).first())["name"]
                    
                    transit_lines[transit_line] = schedule
            
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
    reservations = relationship(
        'Reservation', 
        back_populates='train_schedule', 
        cascade='all, delete-orphan'  # Enables cascading deletes
    )

class Train(Base):
    __tablename__ = 'train'
    train_id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)

class Stops(Base):
    __tablename__ = 'stops'
    transit_line = Column(
        String(30), 
        ForeignKey('train_schedule.transit_line', ondelete='CASCADE'),  # Cascade delete
        primary_key=True
    )
    station_id = Column(
        String(20), 
        ForeignKey('station.station_id'), 
        primary_key=True
    )
    arrival = Column(DateTime, nullable=False)
    departure = Column(DateTime, nullable=False)

    # Relationships
    station = relationship('Station', foreign_keys=[station_id])
    schedule = relationship('Schedule', foreign_keys=[transit_line])

class Reservation(Base):
    __tablename__ = 'reservations'

    reservation_id = Column(Integer, primary_key=True, autoincrement=True)
    transit_line = Column(
        String(30), 
        ForeignKey('train_schedule.transit_line', ondelete='CASCADE'),  # Cascade delete for train schedule
        nullable=False
    )
    customer_email = Column(
        String(100),
        ForeignKey('customer.email', ondelete='CASCADE'),  # Cascade delete for customer
        nullable=False
    )
    seat_number = Column(String(20), nullable=True)
    passenger_category = Column(
        Enum('regular', 'child', 'elderly', 'disabled', name='passenger_category_enum'),
        default='regular',
        nullable=False
    )
    price = Column(Numeric(10, 2), nullable=False)
    discounted_price = Column(Numeric(10, 2), nullable=False)
    status = Column(
        Enum('active', 'cancelled', name='reservation_status_enum'),
        default='active',
        nullable=False
    )
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # New Columns for Source and Destination Stations
    source_station_id = Column(
        String(20),
        ForeignKey('station.station_id', ondelete='CASCADE'),  # Cascade delete for source station
        nullable=False
    )
    destination_station_id = Column(
        String(20),
        ForeignKey('station.station_id', ondelete='CASCADE'),  # Cascade delete for destination station
        nullable=False
    )

    # Relationships
    customer = relationship('Customer', back_populates='reservations')
    train_schedule = relationship('Schedule', back_populates='reservations')
    source_station = relationship('Station', foreign_keys=[source_station_id])  # Source station relationship
    destination_station = relationship('Station', foreign_keys=[destination_station_id])  # Destination station relationship




