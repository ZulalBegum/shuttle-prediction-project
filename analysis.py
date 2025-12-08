from datetime import datetime, timedelta
from typing import Tuple, Dict, List
from data_source.db_manager import get_traffic_delay_minutes 

#Simulated data from scrapy
ROUTE_BASELINE_DELAY: Dict[int, float] = {}

def get_passenger_and_time_delay(hour: int, simulated_passenger_count: int) -> float:
    total_extra_delay = 0                        #Calculates additional delay minutes based on the time of day and passenger density.
    
    # Peak Hours (Morning and Evening)
    if (8 <= hour < 10) or (16 <= hour < 19):
        total_extra_delay += 10 # 10 minutes additional delay
    
    # Passenger Density
    MAX_CAPACITY = 50 
    if simulated_passenger_count > (MAX_CAPACITY * 1.5): # More than 150%
        total_extra_delay += 5
    elif simulated_passenger_count > MAX_CAPACITY:
        total_extra_delay += 2

    return float(total_extra_delay)


def predict_delay(
    current_time: datetime,
    scheduled_arrival: datetime,
    current_location: Tuple[float, float],
    next_stop_location: Tuple[float, float],
    route_id: int, 
    simulated_passenger_count: int
) -> Dict:
    #Calculates Live Service Delay Prediction.
    
    # 1. Live Traffic Analysis (Google Maps API)
    traffic_data = get_traffic_delay_minutes(current_location, next_stop_location)
    
    # 2. Base Delay (Scrapy Simulation)
    # Uses default 3.0 minutes
    scrapy_base_delay = ROUTE_BASELINE_DELAY.get(route_id, 3.0) 
    
    # 3. Model Delay (Hour and Passenger Density)
    hour = current_time.hour
    model_delay = get_passenger_and_time_delay(hour, simulated_passenger_count) 
    
    # 4. Total Delay
    live_traffic_delay = traffic_data['traffic_delay']
    total_predicted_delay = live_traffic_delay + scrapy_base_delay + model_delay
    
    # 5. Net Delay Calculation
    time_remaining_scheduled = (scheduled_arrival - current_time).total_seconds() / 60.0
    
    # Actual travel time (Traffic+Structural+Model)
    predicted_travel_time = traffic_data.get('baseline_time', time_remaining_scheduled) + total_predicted_delay
    
    # Net delay (Predicted Time - Remaining Scheduled Time)
    net_delay = max(0, predicted_travel_time - time_remaining_scheduled)
    predicted_arrival = current_time + timedelta(minutes=predicted_travel_time)

    # (Message creation logic remains the same)
    if net_delay <= 1:
        message = "Shuttle is on time."
    else:
        # (Detailed message creation)
        message = f"Shuttle {round(net_delay)} minutes late." # Simplified message

    return {
        "net_delay_minutes": round(net_delay, 1),
        "message": message,
        "details": {
            "live_traffic_delay": round(live_traffic_delay, 1),
            "scrapy_base_delay": round(scrapy_base_delay, 1),
            "model_delay": round(model_delay, 1),
            "predicted_arrival": predicted_arrival
        }
    }