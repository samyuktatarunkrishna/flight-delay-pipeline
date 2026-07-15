import os
import json
import urllib.request
import urllib.error
import random
from datetime import datetime, timedelta

# Constants
AIRPORTS = ["ATL", "ORD", "DFW", "DEN", "LAX", "JFK", "SFO", "SEA", "LAS", "MCO", "LHR", "CDG", "FRA", "DXB", "SIN", "HND", "SYD"]
AIRLINES = ["American Airlines", "Delta Air Lines", "United Airlines", "Southwest Airlines", "JetBlue Airways", "Lufthansa", "Emirates", "British Airways", "Singapore Airlines", "Qantas Airways"]

def query_aviationstack_api(api_key, output_path, limit_pages=3):
    """
    Fetches real-time flight records from Aviationstack API.
    """
    all_flights = []
    base_url = "http://api.aviationstack.com/v1/flights"
    
    print(f"Contacting Aviationstack API (fetching up to {limit_pages} pages)...")
    
    for page in range(limit_pages):
        offset = page * 100
        url = f"{base_url}?access_key={api_key}&limit=100&offset={offset}"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if "error" in data:
                    print(f"API Error Response on page {page}: {data['error']['message']}")
                    return False
                    
                flights = data.get("data", [])
                if not flights:
                    print("No more flights returned by API.")
                    break
                    
                all_flights.extend(flights)
                print(f"Successfully retrieved page {page + 1} ({len(flights)} flights)")
                
        except urllib.error.URLError as e:
            print(f"HTTP Connection Error on page {page}: {e.reason}")
            return False
            
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(all_flights, f, indent=2)
        
    print(f"Successfully saved {len(all_flights)} API flight records to {output_path}")
    return True

def generate_offline_fallback(output_path, num_records=1000):
    """
    Generates high-fidelity flight records matching the exact schema of Aviationstack API response.
    Includes both US domestic and international routes and carriers.
    """
    print(f"Generating {num_records} offline Aviationstack fallback flight logs...")
    
    flights = []
    start_date = datetime.now() - timedelta(days=15)
    
    for i in range(num_records):
        date_offset = random.randint(0, 15)
        flight_date = (start_date + timedelta(days=date_offset)).strftime("%Y-%m-%d")
        
        airline_name = random.choice(AIRLINES)
        # Create carrier code mapping
        carrier_map = {
            "American Airlines": "AA",
            "Delta Air Lines": "DL",
            "United Airlines": "UA",
            "Southwest Airlines": "WN",
            "JetBlue Airways": "B6",
            "Lufthansa": "LH",
            "Emirates": "EK",
            "British Airways": "BA",
            "Singapore Airlines": "SQ",
            "Qantas Airways": "QF"
        }
        airline_iata = carrier_map.get(airline_name, "LH")
        
        origin = random.choice(AIRPORTS)
        dest = random.choice([a for a in AIRPORTS if a != origin])
        
        # Determine delay
        has_delay = random.random() < 0.23
        dep_delay = random.randint(15, 140) if has_delay else 0
        arr_delay = dep_delay + random.randint(-15, 12) if has_delay else random.randint(-10, 5)
        
        # Flight times
        sched_hour = random.randint(0, 23)
        sched_min = random.randint(0, 59)
        sched_dep_str = f"{flight_date}T{sched_hour:02d}:{sched_min:02d}:00+00:00"
        
        # Scheduled arrival (Long-haul flights can be 1 to 14 hours)
        dur_hrs = random.randint(1, 14)
        dur_mins = random.randint(0, 59)
        arr_time = datetime.strptime(flight_date, "%Y-%m-%d") + timedelta(hours=sched_hour + dur_hrs, minutes=sched_min + dur_mins)
        sched_arr_str = arr_time.strftime("%Y-%m-%dT%H:%M:00+00:00")
        
        status = "scheduled"
        if has_delay and random.random() < 0.05:
            status = "cancelled"
            dep_delay = None
            arr_delay = None
            
        flight_record = {
            "flight_date": flight_date,
            "flight_status": status,
            "departure": {
                "airport": f"{origin} Hub Airport",
                "iata": origin,
                "delay": dep_delay,
                "scheduled": sched_dep_str,
                "estimated": sched_dep_str,
                "actual": None
            },
            "arrival": {
                "airport": f"{dest} Destination Airport",
                "iata": dest,
                "delay": arr_delay,
                "scheduled": sched_arr_str,
                "estimated": sched_arr_str,
                "actual": None
            },
            "airline": {
                "name": airline_name,
                "iata": airline_iata
            },
            "flight": {
                "number": str(random.randint(100, 9999)),
                "iata": f"{airline_iata}{random.randint(100, 9999)}"
            }
        }
        flights.append(flight_record)
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(flights, f, indent=2)
        
    print(f"Saved fallback flight records to {output_path}")

def main():
    api_key = os.environ.get("AVIATIONSTACK_API_KEY")
    output_path = "data/raw/flights_aviationstack.json"
    
    success = False
    if api_key:
        print("Aviationstack API Key detected in environment.")
        success = query_aviationstack_api(api_key, output_path)
        
    if not success:
        if not api_key:
            print("AVIATIONSTACK_API_KEY environment variable not found.")
        else:
            print("API query failed, falling back to simulated API data.")
        generate_offline_fallback(output_path, num_records=5000)

if __name__ == "__main__":
    main()
