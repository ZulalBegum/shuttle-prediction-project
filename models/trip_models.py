from typing import List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Stop:                         #Stop Information
    stop_id: int
    name: str
    lat: float
    lon: float

@dataclass
class Route:                        #Route Information
    route_id: int
    name: str
    stops_sequence: List[int]                    # Stored as a string in FalkorDB
    distance_km: float
    direction: str

                                
@dataclass                             # Simple classes used in FalkorDB but only hold data
class Trip:
    trip_id: str
    route_id: int
    scheduled_start: datetime
    
@dataclass
class LiveLocation:
    trip_id: str
    lat: float
    lon: float
    timestamp: datetime