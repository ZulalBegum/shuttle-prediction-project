from data_source.db_manager import DBManager, get_traffic_delay_minutes
from datetime import datetime, timedelta
from models.trip_models import Stop, Route
from analysis import predict_delay, ROUTE_BASELINE_DELAY
import random
import os

# --- 1. Statik Veri Tanımları ---

STOPS = [
    Stop(stop_id=1, name="Vadi Campus", lat=41.0652, lon=29.0062),
    Stop(stop_id=2, name="ANK", lat=41.0884, lon=29.0441),
    Stop(stop_id=3, name="Trump AVM", lat=41.0664, lon=28.9858),
    Stop(stop_id=4, name="Kağıthane", lat=40.9904, lon=29.0201),
    Stop(stop_id=5, name="Topkapı Campus", lat=41.0423, lon=29.0051),
]
STOP_MAP = {stop.stop_id: stop for stop in STOPS}

ROUTES = [
    Route(route_id=101, name="Topkapı-ANK-Vadi",
          stops_sequence=[5, 2, 1], distance_km=20, direction="inbound"),
    Route(route_id=102, name="Trump-ANK-Vadi", 
          stops_sequence=[3, 2, 1], distance_km=12, direction="inbound"),
    Route(route_id=103, name="Kağıthane-ANK-Vadi", 
          stops_sequence=[4, 2, 1], distance_km=7, direction="inbound"),
    Route(route_id=201, name="Vadi-ANK-Topkapı", 
          stops_sequence=[1, 2, 5], distance_km=20, direction="outbound"),
    Route(route_id=202, name="Vadi-ANK-Trump", 
          stops_sequence=[1, 2, 3], distance_km=12, direction="outbound"),
    Route(route_id=203, name="Vadi-ANK-Kağıthane", 
          stops_sequence=[1, 2, 4], distance_km=7, direction="outbound"),
]

def generate_live_location(current_stop: Stop, next_stop: Stop) -> tuple[float, float]:
    """İki durak arasında rastgele bir canlı konum simüle eder."""
    # ... (kod aynı kalır) ...
    lat = (current_stop.lat + next_stop.lat) / 2 + random.uniform(-0.005, 0.005)
    lon = (current_stop.lon + next_stop.lon) / 2 + random.uniform(-0.005, 0.005)
    return (lat, lon)

def run_prediction_example(db_manager: DBManager):
    print("="*40)
    print("LIVE SHUTTLE DELAY PREDICTION:")
    print("="*40)

    route_to_simulate = ROUTES[2] # Route 103 (Kağıthane-ANK-Vadi)
    
    current_time = datetime.now()
    current_stop = STOP_MAP[route_to_simulate.stops_sequence[0]] 
    next_stop = STOP_MAP[route_to_simulate.stops_sequence[1]]     

    current_location = generate_live_location(current_stop, next_stop)
    scheduled_arrival_time = current_time + timedelta(minutes=15)
    simulated_passenger_count = random.randint(60, 80) # Density Simulation

    # --- RUN PREDICTION ---
    prediction = predict_delay(
        current_time,
        scheduled_arrival_time,
        current_location,
        (next_stop.lat, next_stop.lon),
        route_to_simulate.route_id, 
        simulated_passenger_count
    )
    
    # --- SHOW RESULTS ---
    print(f"\n--- ROUTE AND LOCATION INFORMATION ---")
    print(f"Route: {route_to_simulate.name} (ID: {route_to_simulate.route_id})")
    print(f"Shuttle CURRENTLY between: {current_stop.name} and {next_stop.name}.")
    print(f"Next stop: {next_stop.name} (Scheduled Arrival: {scheduled_arrival_time.strftime('%H:%M:%S')})")
    print(f"Current Passenger Count: {simulated_passenger_count}")
    
    print(f"\n--- LIVE PREDICTION ---")
    """print(f" Predicted Delay: {prediction['net_delay_minutes']} minutes")"""
    print(f"Predicted Delay: {prediction['message']}")
    print(f"Predicted Arrival Time: {prediction['details']['predicted_arrival'].strftime('%H:%M:%S')}")
    print(f" -> Live Traffic Delay (Google Maps): {prediction['details']['live_traffic_delay']} min")
    print(f" -> Structural Delay (Scrapy Simulation): {prediction['details']['scrapy_base_delay']} min")
    print(f" -> Density by time: {prediction['details']['model_delay']} min")


def main():
    # 1. Simulate Baseline Delay Data (Replaces Scrapy)
    global ROUTE_BASELINE_DELAY
    simulated_baseline_delay = {route.route_id: random.uniform(2.5, 4.5) for route in ROUTES}
    ROUTE_BASELINE_DELAY.update(simulated_baseline_delay)
    
    # 2. Initialize DB Manager and establish FalkorDB connections
    db_manager = DBManager()
    
    # 3. Save static data to FalkorDB
    db_manager.initialize_static_data(STOPS, ROUTES)
    
    # 4. Run prediction simulation
    run_prediction_example(db_manager)


if __name__ == "__main__":
    # Check for required libraries
    try:
        import falkordb
        import googlemaps
    except ImportError:
        print("\n❌ Missing required Python libraries: falkordb and googlemaps.")
        print("Please run the following command in your terminal: pip install falkordb googlemaps")
        exit()
        
    main()