from app import session, Base
from common import object_as_dict
from sqlalchemy import Column, String, DateTime, Time, Float, ForeignKey, func
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
            print(e)
            return ({'success': False, 'message': f'Error fetching stops: {str(e)}'}, 500)

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
    