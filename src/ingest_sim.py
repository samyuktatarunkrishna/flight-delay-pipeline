import os
import csv
import random
import argparse
from datetime import datetime, timedelta

# Configuration / Constants
AIRPORTS = {
    "ATL": "Atlanta, GA",
    "ORD": "Chicago, IL",
    "DFW": "Dallas-Fort Worth, TX",
    "DEN": "Denver, CO",
    "LAX": "Los Angeles, CA",
    "JFK": "New York, NY",
    "SFO": "San Francisco, CA",
    "SEA": "Seattle, WA",
    "LAS": "Las Vegas, NV",
    "MCO": "Orlando, FL"
}

CARRIERS = {
    "AA": "American Airlines",
    "DL": "Delta Air Lines",
    "UA": "United Airlines",
    "WN": "Southwest Airlines",
    "B6": "JetBlue Airways"
}

def generate_flight_data(num_records, output_path):
    print(f"Generating {num_records} flight records...")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define start date (e.g., 30 days ago)
    start_date = datetime.now() - timedelta(days=30)
    
    headers = [
        "flight_date", "carrier", "flight_num", "origin", "origin_city", 
        "dest", "dest_city", "dep_time", "dep_delay", "arr_time", "arr_delay", 
        "cancelled", "diverted", "carrier_delay", "weather_delay", "nas_delay", 
        "security_delay", "late_aircraft_delay"
    ]
    
    with open(output_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        
        for i in range(num_records):
            # 1. Flight basics
            date_offset = random.randint(0, 30)
            flight_date = (start_date + timedelta(days=date_offset)).strftime("%Y-%m-%d")
            carrier = random.choice(list(CARRIERS.keys()))
            flight_num = random.randint(100, 9999)
            
            # Origin and dest cannot be the same
            origin = random.choice(list(AIRPORTS.keys()))
            dest = random.choice([a for a in AIRPORTS.keys() if a != origin])
            origin_city = AIRPORTS[origin]
            dest_city = AIRPORTS[dest]
            
            # Scheduled time
            scheduled_hour = random.randint(5, 23)
            scheduled_minute = random.randint(0, 59)
            dep_time_num = scheduled_hour * 100 + scheduled_minute
            dep_time = f"{dep_time_num:04d}"
            
            # 2. Delays and cancellations
            # Probability of cancellation: 1.5%
            # Probability of diversion: 0.5%
            # Probability of delay: 20%
            rand_event = random.random()
            
            cancelled = 0
            diverted = 0
            dep_delay = 0
            arr_delay = 0
            arr_time = ""
            
            carrier_delay = 0
            weather_delay = 0
            nas_delay = 0
            security_delay = 0
            late_aircraft_delay = 0
            
            if rand_event < 0.015:
                # Cancelled
                cancelled = 1
                dep_time = ""
            elif rand_event < 0.020:
                # Diverted
                diverted = 1
                dep_delay = random.randint(-5, 15)
                # Arr time is empty or NA because it diverted
            else:
                # Normal flight (possibly delayed)
                is_delayed = random.random() < 0.20
                if is_delayed:
                    # Delay in minutes
                    # Long-tail delay distribution using power or exponential simulation
                    dep_delay = int(random.expovariate(1/35)) + 1
                    
                    # Randomize arrival delay slightly relative to departure delay
                    # Flights can make up time in the air
                    arr_delay = max(-15, dep_delay - random.randint(0, 15))
                else:
                    dep_delay = random.randint(-10, 5)
                    arr_delay = dep_delay - random.randint(0, 10)
                
                # Calculate arrival time
                # Scheduled flight duration: 1 to 5 hours
                duration_mins = random.randint(60, 300)
                actual_dep_minutes = scheduled_hour * 60 + scheduled_minute + dep_delay
                actual_arr_minutes = (actual_dep_minutes + duration_mins) % 1440
                
                arr_hour = actual_arr_minutes // 60
                arr_minute = actual_arr_minutes % 60
                arr_time = f"{arr_hour * 100 + arr_minute:04d}"
                
                # Breakdown of delays (only if arr_delay > 15 minutes)
                if arr_delay > 15:
                    # Allocate arrival delay across categories
                    remaining_delay = arr_delay
                    
                    # Distribute delay randomly among active factors
                    factors = ["carrier", "weather", "nas", "security", "late_aircraft"]
                    random.shuffle(factors)
                    
                    delay_alloc = {}
                    for f in factors[:-1]:
                        if remaining_delay > 0:
                            alloc = random.randint(0, remaining_delay)
                            delay_alloc[f] = alloc
                            remaining_delay -= alloc
                        else:
                            delay_alloc[f] = 0
                    delay_alloc[factors[-1]] = remaining_delay # Put the remainder in the last factor
                    
                    carrier_delay = delay_alloc.get("carrier", 0)
                    weather_delay = delay_alloc.get("weather", 0)
                    nas_delay = delay_alloc.get("nas", 0)
                    security_delay = delay_alloc.get("security", 0)
                    late_aircraft_delay = delay_alloc.get("late_aircraft", 0)
            
            writer.writerow([
                flight_date, carrier, flight_num, origin, origin_city,
                dest, dest_city, dep_time, dep_delay, arr_time, arr_delay,
                cancelled, diverted, carrier_delay, weather_delay, nas_delay,
                security_delay, late_aircraft_delay
            ])
            
            if (i + 1) % 50000 == 0:
                print(f"Generated {i + 1} records...")

    print(f"Successfully generated dataset and saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate Flight Data Ingestion")
    parser.add_argument("--records", type=int, default=100000, help="Number of records to generate")
    parser.add_argument("--output", type=str, default="data/raw/flights_raw.csv", help="Path to save the CSV file")
    
    args = parser.parse_args()
    generate_flight_data(args.records, args.output)
