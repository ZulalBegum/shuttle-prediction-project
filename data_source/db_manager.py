import os
import googlemaps
from datetime import datetime
from typing import Tuple, Dict, List
import json
import falkordb 
from models.trip_models import Stop, Route

FALKORDB_URL = "redis://127.0.0.1:6379"                  #falkorDB 
graph = None 
try:
    falkor = falkordb.FalkorDB(FALKORDB_URL)
    graph = falkor.select_graph("shuttle_graph")
    print("✅ FalkorDB bağlantısı başarılı.")
except Exception as e:
    print(f"❌ FalkorDB bağlantı hatası: {e}")
    print("❗ Lütfen 'redis-stack-server' komutunu çalıştırdığınızdan emin olun.")


GOOGLE_MAPS_API_KEY = "AIzaSyD_QIsZIMtZX5Ph2lICBOhATH7VO9brWxg"       # Google Maps API Key

if not GOOGLE_MAPS_API_KEY:
    print("❌ Google Maps API Key yok. Trafik verisi alınamaz.")
    gmaps = None
else:
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)


def get_traffic_delay_minutes(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    departure_time: str = "now"
) -> Dict:
                                                                       #It receives live traffic data via the Google Maps API.
    if not gmaps:
        return {"live_time": 0.0, "baseline_time": 0.0, "traffic_delay": 0.0}

    try:
        directions = gmaps.directions(
            origin,
            destination,
            mode="driving",
            departure_time=departure_time
        )
        if not directions or not directions[0]["legs"]:
             return {"live_time": 0.0, "baseline_time": 0.0, "traffic_delay": 0.0}

        leg = directions[0]["legs"][0]

        live = leg.get("duration_in_traffic", leg["duration"])["value"]
        baseline = leg["duration"]["value"]

        live_min = live / 60
        baseline_min = baseline / 60
        delay = max(0, live_min - baseline_min)

        return {
            "live_time": live_min,
            "baseline_time": baseline_min,
            "traffic_delay": delay
        }

    except Exception as e:
                                                         # Returning 0 in case of an error prevents the program from crashing.
        # print(f"⚠️ Google Maps API Hatası: {e}") 
        return {"live_time": 0.0, "baseline_time": 0.0, "traffic_delay": 0.0}


class DBManager:

    def __init__(self):
        pass

    def initialize_static_data(self, stops: List[Stop], routes: List[Route]):
        if not graph: return

        # STOP kontrolü ve eklenmesi
        stop_count = graph.query("MATCH (s:Stop) RETURN COUNT(s)").result_set[0][0]

        if stop_count == 0:
            print("Adding stops...")
            for stop in stops:
                graph.query(
                    "CREATE (:Stop {stop_id: $stop_id, name: $name, lat: $lat, lon: $lon})",
                    {"stop_id": stop.stop_id, "name": stop.name, "lat": stop.lat, "lon": stop.lon}
                )
            print(f"✅ {len(stops)} durak eklendi.")

        # ROUTE kontrolü ve eklenmesi
        route_count = graph.query("MATCH (r:Route) RETURN COUNT(r)").result_set[0][0]

        if route_count == 0:
            print("Adding routes...")
            for route in routes:
                # stops_sequence listesini FalkorDB'ye kaydetmek için JSON string'e çeviriyoruz
                seq_str = json.dumps(route.stops_sequence) 
                
                graph.query(
                    """
                    CREATE (:Route {
                        route_id: $route_id,
                        name: $name,
                        stops_sequence: $seq, 
                        distance_km: $dist, 
                        direction: $direction
                    })
                    """,
                    {
                        "route_id": route.route_id, "name": route.name, 
                        "seq": seq_str, # JSON string
                        "dist": route.distance_km, "direction": route.direction
                    }
                )
            print(f"✅ {len(routes)} rota eklendi.")

    def get_stops(self) -> Dict[int, Stop]:
        if not graph: return {}
        results = graph.query("MATCH (s:Stop) RETURN s.stop_id, s.name, s.lat, s.lon").result_set
        stops = {}
        for stop_id, name, lat, lon in results:
            stops[int(stop_id)] = Stop(stop_id=int(stop_id), name=name, lat=float(lat), lon=float(lon))
        return stops

    def get_routes(self) -> List[Route]:
        if not graph: return []
        results = graph.query("MATCH (r:Route) RETURN r.route_id, r.name, r.stops_sequence, r.distance_km, r.direction").result_set
        routes = []
        for route_id, name, seq_str, dist, direction in results:
             # Veriyi FalkorDB'den çekerken JSON string'i listeye geri çeviriyoruz
            seq_list = json.loads(seq_str) 
            routes.append(
                Route(
                    route_id=int(route_id), name=name, stops_sequence=seq_list, 
                    distance_km=float(dist), direction=direction
                )
            )
        return routes