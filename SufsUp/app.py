# Import the dependencies.

import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
from flask import Flask, jsonify, request
from datetime import datetime

#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///../Resources/hawaii.sqlite")

#################################################
# reflect an existing database into a new model
#################################################

Base = automap_base()

#################################################
# reflect the tables
#################################################

Base.prepare(autoload_with=engine)

#################################################
#print reflected table names
print(Base.classes.keys())
#################################################

#################################################
# Save references to each table
#################################################

Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Create our session (link) from Python to the DB
#################################################

session = Session(bind=engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"                  #I've included this on the landing page, but I don't think it will be intuitive for the user.
        f"/api/v1.0/<start>/<end>"                 #I've included this too on the landing page, but I don't think it will be intuitive for the user.
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all precipitation measurements from the last 12 months"""
  
    measurement_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    
    #parse out the day, month, year from the datetime object
    date_string = measurement_date[0]
   
    # Convert the date string to a datetime object
    date_object = datetime.strptime(date_string, '%Y-%m-%d')

    # Extract the month, day, and year from the datetime object
    my_month = int(date_object.strftime('%m'))
    my_day = int(date_object.strftime('%d'))
    my_year = int(date_object.strftime('%Y'))

    # Calculate the date one year from the last date in data set.
    recent_date = dt.date(my_year,my_month,my_day)
    year_ago = dt.date(my_year,my_month,my_day) - dt.timedelta(days=366)
    
    results = session.query(Measurement.date, Measurement.prcp).\
                        filter(Measurement.date >year_ago).filter(Measurement.date <= recent_date).\
                        order_by(Measurement.date).all()
    session.close()

    all_prcp =[]

    for date, prcp in results:
        precipitation_dict = {}
        precipitation_dict["Measurement Date"] = date
        precipitation_dict["Precipitation"] = prcp
        all_prcp.append(precipitation_dict)

    return jsonify(all_prcp)

@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all stations"""
    
    results= session.query(Station.station).all() 
    
    # Convert results to a list
    station_results = []
    for station, in results:
        #print(station)
        station_results.append(station)
    station_results

    return jsonify(station_results)

@app.route("/api/v1.0/tobs")
def tobs():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    measurement_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    

    #*********************************************************************************
    #**The code below is a repeat of the code above. I attempted to write functions **
    #**to avoid repetition, but I couldn't get them to work...                      ** 
    #*********************************************************************************

    #parse out the day, month, year from the datetime object
    date_string = measurement_date[0]
    # Convert the date string to a datetime object
    date_object = datetime.strptime(date_string, '%Y-%m-%d')

    # Extract the month, day, and year from the datetime object
    my_month = int(date_object.strftime('%m'))
    my_day = int(date_object.strftime('%d'))
    my_year = int(date_object.strftime('%Y'))

    # Calculate the date one year from the last date in data set.
    recent_date = dt.date(my_year,my_month,my_day)
    year_ago = dt.date(my_year,my_month,my_day) - dt.timedelta(days=366)

    most_active_station= session.query(Measurement.station,func.count(Measurement.tobs).label('count')).\
                                group_by(Measurement.station).\
                                order_by(func.count(Measurement.tobs).desc()).first()  
    station_id = most_active_station.station
    
    temperatures=session.query(Measurement.date, Measurement.tobs).\
                            filter(Measurement.date >year_ago).\
                            filter(Measurement.date <= recent_date).\
                            filter(Measurement.station == station_id).all()
    
    most_active_tobs =[]   #an empty list to hold the results of the query above

    for date, tobs in temperatures:
        temperature_dict = {}
        temperature_dict["Measurement Date"] = date
        temperature_dict["Temperature"] = tobs
        most_active_tobs.append(temperature_dict)


    return jsonify(most_active_tobs)

@app.route('/api/v1.0/<start_date>')
def start(start_date):
    
    # Create our session (link) from Python to the DB
    session = Session(engine)

    parsed_date = datetime.strptime(start_date, '%Y-%m-%d').date()  #convert input to date object

    #Perform calculations from start date to end of dataset
    tempresults = session.query(Measurement.date,
                    func.round(func.min(Measurement.tobs),2).label('tmin'),
                    func.round(func.avg(Measurement.tobs),2).label('tavg'),
                    func.round(func.max(Measurement.tobs),2).label('tmax')).\
                    filter(Measurement.date >= parsed_date).\
                    group_by(Measurement.date).\
                    all()
        
    # Convert results to a list of dictionaries
    temperature_stats = [] #an empty list to hold the results of the query above
    
    for date, tmin, tavg, tmax in tempresults:
        temp_stat_dict = {}  #an empty dictionary to hold the statitics for each day
        temp_stat_dict["Measurement Date"] = date
        temp_stat_dict["Min Temperature"] = tmin
        temp_stat_dict["Avg Temperature"] = tavg
        temp_stat_dict["Max Temperature"] = tmax
        temperature_stats.append(temp_stat_dict)
    
    return jsonify(temperature_stats)
    
   
@app.route('/api/v1.0/<start>/<end>')
def start_end(start_date, end_date):

    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    parsed_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()  #convert input to date object
    parsed_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()  #convert input to date object
    #Perform calculations from start date to end date
    tempresults_start_end = session.query(Measurement.date,
                            func.round(func.min(Measurement.tobs),2).label('tmin'),
                            func.round(func.avg(Measurement.tobs),2).label('tavg'),
                            func.round(func.max(Measurement.tobs),2).label('tmax')).\
                            filter(Measurement.date >= parsed_start_date).\
                            filter(Measurement.date <= parsed_end_date).\
                            group_by(Measurement.date).\
                            all()
        
    # Convert results to a list of dictionaries
    temperature_stats_start_end = [] #an empty list to hold the results of the query above
    
    for date, tmin, tavg, tmax in tempresults_start_end:
        temp_stat_start_end_dict = {}  #an empty dictionary to hold the statitics for each day
        temp_stat_start_end_dict["Measurement Date"] = date
        temp_stat_start_end_dict["Min Temperature"] = tmin
        temp_stat_start_end_dict["Avg Temperature"] = tavg
        temp_stat_start_end_dict["Max Temperature"] = tmax
        temperature_stats_start_end.append(temp_stat_start_end_dict)
    
    return jsonify(temperature_stats_start_end)

if __name__ == "__main__":
    app.run(debug=True)
