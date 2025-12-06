from typing import Tuple, Dict

def get_passenger_and_time_delay(hour: int, simulated_passenger_count: int) -> float:
                                                          
    total_extra_delay = 0                        #Calculates additional delay minutes based on the time of day and passenger density.
    
    # a) Time of Day Coefficient (Peak Hours)
    if (8 <= hour < 10) or (16 <= hour < 19):
        total_extra_delay += 10
    # Less busy hours
    elif 10 <= hour < 13 or 19 <= hour < 21:
        total_extra_delay += 3
        
    # b) Passenger Density Coefficient
    MAX_CAPACITY = 50 
    # If more than 150% of capacity
    if simulated_passenger_count > (MAX_CAPACITY * 1.5):
        total_extra_delay += 5
    # If capacity is exceeded
    elif simulated_passenger_count > MAX_CAPACITY:
        total_extra_delay += 2

    return float(total_extra_delay)