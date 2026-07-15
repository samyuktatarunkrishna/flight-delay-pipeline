import os
import sys
import time
import random
import threading
import duckdb
import pandas as pd
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Flight Delay and Traffic Analytics API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "aviation_dw.db"))

app.state_live_appended = 0

def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Analytics database not found at {DB_PATH}. Run the pipeline first.")
    return duckdb.connect(DB_PATH)

def refresh_marts(con):
    """
    Direct SQL updates in DuckDB to incrementally update the marts
    with new live arrivals, joining with airlines seed.
    """
    # 1. Update fct_delays joining with airlines
    con.execute("""
        CREATE OR REPLACE TABLE fct_delays AS
        WITH aggregated AS (
            SELECT
                cast(flight_date as date) as flight_date,
                cast(carrier as varchar) as carrier_code,
                count(*) as total_flights,
                sum(case when cancelled = 1 then 1 else 0 end) as cancelled_flights,
                sum(case when diverted = 1 then 1 else 0 end) as diverted_flights,
                sum(case when dep_delay > 15 then 1 else 0 end) as delayed_dep_flights_count,
                sum(case when arr_delay > 15 then 1 else 0 end) as delayed_arr_flights_count,
                avg(dep_delay) as avg_dep_delay_mins,
                avg(arr_delay) as avg_arr_delay_mins,
                sum(case when arr_delay > 15 then carrier_delay else 0 end) as total_carrier_delay_mins,
                sum(case when arr_delay > 15 then weather_delay else 0 end) as total_weather_delay_mins,
                sum(case when arr_delay > 15 then nas_delay else 0 end) as total_nas_delay_mins,
                sum(case when arr_delay > 15 then security_delay else 0 end) as total_security_delay_mins,
                sum(case when arr_delay > 15 then late_aircraft_delay else 0 end) as total_late_aircraft_delay_mins,
                avg(case when arr_delay > 15 then carrier_delay else null end) as avg_carrier_delay_mins,
                avg(case when arr_delay > 15 then weather_delay else null end) as avg_weather_delay_mins,
                avg(case when arr_delay > 15 then nas_delay else null end) as avg_nas_delay_mins,
                avg(case when arr_delay > 15 then security_delay else null end) as avg_security_delay_mins,
                avg(case when arr_delay > 15 then late_aircraft_delay else null end) as avg_late_aircraft_delay_mins
            FROM raw_flights
            GROUP BY 1, 2
        )
        SELECT
            a.*,
            coalesce(al.airline_name, a.carrier_code) as airline_name
        FROM aggregated a
        LEFT JOIN airlines al on a.carrier_code = al.carrier_code
    """)
    
    # 2. Update mart_route_performance (joining with airports seed table)
    con.execute("""
        CREATE OR REPLACE TABLE mart_route_performance AS
        WITH routes_base AS (
            SELECT
                origin as origin_airport,
                dest as dest_airport,
                count(*) as total_flights,
                sum(case when cancelled = 1 then 1 else 0 end) as cancelled_flights,
                sum(case when diverted = 1 then 1 else 0 end) as diverted_flights,
                avg(dep_delay) as avg_dep_delay,
                avg(arr_delay) as avg_arr_delay,
                round(
                    sum(case when cancelled = 0 and diverted = 0 and arr_delay <= 15 then 1 else 0 end) * 100.0 / 
                    nullif(sum(case when cancelled = 0 then 1 else 0 end), 0),
                    2
                ) as on_time_arrival_pct,
                round(
                    sum(case when cancelled = 1 then 1 else 0 end) * 100.0 / count(*),
                    2
                ) as cancellation_rate_pct
            FROM raw_flights
            GROUP BY 1, 2
        )
        SELECT
            r.origin_airport,
            orig.airport_name as origin_airport_name,
            orig.city as origin_city,
            orig.state as origin_state,
            orig.latitude as origin_latitude,
            orig.longitude as origin_longitude,
            r.dest_airport,
            dest.airport_name as dest_airport_name,
            dest.city as dest_city,
            dest.state as dest_state,
            dest.latitude as dest_latitude,
            dest.longitude as dest_longitude,
            r.total_flights,
            r.cancelled_flights,
            r.diverted_flights,
            r.avg_dep_delay,
            r.avg_arr_delay,
            r.on_time_arrival_pct,
            r.cancellation_rate_pct
        FROM routes_base r
        LEFT JOIN airports orig on r.origin_airport = orig.iata_code
        LEFT JOIN airports dest on r.dest_airport = dest.iata_code
    """)
    
    # 3. Update mart_congestion
    con.execute("""
        CREATE OR REPLACE TABLE mart_congestion AS
        WITH flight_hours as (
            SELECT
                *,
                cast(substr(coalesce(dep_time, '0000'), 1, 2) as integer) as dep_hour,
                strftime(flight_date::date, '%A') as day_of_week,
                cast(strftime(flight_date::date, '%w') as integer) as day_of_week_num
            FROM raw_flights
        )
        SELECT
            dep_hour,
            day_of_week,
            day_of_week_num,
            count(*) as total_scheduled_flights,
            sum(case when dep_delay > 15 then 1 else 0 end) as delayed_flights,
            avg(dep_delay) as avg_dep_delay_mins,
            round(
                sum(case when dep_delay > 15 then 1 else 0 end) * 100.0 / count(*), 
                2
            ) as dep_delay_rate_pct
        FROM flight_hours
        WHERE cancelled = 0
        GROUP BY 1, 2, 3
    """)

def live_stream_generator_loop():
    """
    Background daemon loop that appends new simulated global flights 
    every 10 seconds.
    """
    print("[Live Stream Worker] Initialized and waiting for database...", flush=True)
    while True:
        time.sleep(10)
        try:
            if not os.path.exists(DB_PATH):
                continue
            
            con = duckdb.connect(DB_PATH)
            table_check = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'raw_flights'").fetchone()[0]
            if table_check == 0:
                con.close()
                continue
                
            num_new = random.randint(3, 8)
            airports = ["ATL", "ORD", "DFW", "DEN", "LAX", "JFK", "SFO", "SEA", "LAS", "MCO", "LHR", "CDG", "FRA", "DXB", "SIN", "HND", "SYD"]
            carriers = ["AA", "DL", "UA", "WN", "B6", "LH", "EK", "BA", "SQ", "QF"]
            
            for _ in range(num_new):
                origin = random.choice(airports)
                dest = random.choice([a for a in airports if a != origin])
                carrier = random.choice(carriers)
                flight_num = str(random.randint(100, 9999))
                
                now_time = datetime.now()
                flight_date = now_time.strftime("%Y-%m-%d")
                dep_time = now_time.strftime("%H%M")
                
                has_delay = random.random() < 0.24
                dep_delay = random.randint(15, 120) if has_delay else 0
                arr_delay = dep_delay + random.randint(-10, 10) if has_delay else random.randint(-5, 5)
                
                arr_time = (now_time + timedelta(hours=random.randint(1, 3))).strftime("%H%M")
                cancelled = 1 if random.random() < 0.01 else 0
                diverted = 1 if random.random() < 0.005 else 0
                
                carrier_delay = 0
                weather_delay = 0
                nas_delay = 0
                security_delay = 0
                late_aircraft = 0
                
                if arr_delay > 15:
                    carrier_delay = int(arr_delay * 0.3)
                    weather_delay = int(arr_delay * 0.1)
                    nas_delay = int(arr_delay * 0.25)
                    late_aircraft = arr_delay - (carrier_delay + weather_delay + nas_delay)
                    
                dep_timestamp = now_time.strftime("%Y-%m-%d %H:%M:00")
                arr_timestamp = (now_time + timedelta(hours=random.randint(1, 3))).strftime("%Y-%m-%d %H:%M:00")
                
                con.execute("""
                    INSERT INTO raw_flights VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    flight_date, carrier, flight_num, origin, "Live Hub", dest, "Live Dest",
                    dep_time, dep_delay, arr_time, arr_delay, cancelled, diverted,
                    carrier_delay, weather_delay, nas_delay, security_delay, late_aircraft,
                    dep_timestamp, arr_timestamp
                ))
            
            refresh_marts(con)
            con.close()
            
            app.state_live_appended += num_new
            print(f"[Live Stream Worker] Ingested {num_new} new real-time flights. Total live appended: {app.state_live_appended}", flush=True)
            
        except Exception as e:
            print(f"[Live Stream Worker] Error occurred: {e}", flush=True)

threading.Thread(target=live_stream_generator_loop, daemon=True).start()


@app.get("/api/summary")
def get_summary():
    try:
        con = get_db_connection()
        res = con.execute("""
            SELECT 
                SUM(total_flights) as total_flights,
                SUM(cancelled_flights) as total_cancelled,
                SUM(diverted_flights) as total_diverted,
                AVG(avg_dep_delay_mins) as avg_dep_delay,
                AVG(avg_arr_delay_mins) as avg_arr_delay,
                SUM(delayed_dep_flights_count) as total_delayed
            FROM fct_delays
        """).fetchone()
        
        total_flights = res[0] or 0
        cancelled = res[1] or 0
        diverted = res[2] or 0
        avg_dep_delay = round(res[3] or 0, 2)
        avg_arr_delay = round(res[4] or 0, 2)
        delayed = res[5] or 0
        
        cancellation_rate = round((cancelled / total_flights * 100) if total_flights > 0 else 0, 2)
        delay_rate = round((delayed / total_flights * 100) if total_flights > 0 else 0, 2)
        
        con.close()
        
        return {
            "total_flights": total_flights,
            "cancellation_rate": cancellation_rate,
            "delay_rate": delay_rate,
            "avg_dep_delay": avg_dep_delay,
            "avg_arr_delay": avg_arr_delay,
            "live_streamed_count": app.state_live_appended
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/delays_by_carrier")
def get_delays_by_carrier():
    try:
        con = get_db_connection()
        df = con.execute("""
            SELECT 
                coalesce(airline_name, 'Unknown Airline') as airline_name,
                coalesce(SUM(total_flights), 0) as flights,
                coalesce(AVG(avg_arr_delay_mins), 0.0) as avg_delay,
                coalesce(SUM(total_carrier_delay_mins), 0.0) as carrier,
                coalesce(SUM(total_weather_delay_mins), 0.0) as weather,
                coalesce(SUM(total_nas_delay_mins), 0.0) as nas,
                coalesce(SUM(total_security_delay_mins), 0.0) as security,
                coalesce(SUM(total_late_aircraft_delay_mins), 0.0) as late_aircraft
            FROM fct_delays
            GROUP BY 1
            ORDER BY flights DESC
        """).df()
        
        con.close()
        
        result = []
        for _, row in df.iterrows():
            c_val = float(row['carrier']) if not pd.isna(row['carrier']) else 0.0
            w_val = float(row['weather']) if not pd.isna(row['weather']) else 0.0
            n_val = float(row['nas']) if not pd.isna(row['nas']) else 0.0
            s_val = float(row['security']) if not pd.isna(row['security']) else 0.0
            l_val = float(row['late_aircraft']) if not pd.isna(row['late_aircraft']) else 0.0
            
            total_delay_mins = c_val + w_val + n_val + s_val + l_val
            
            if total_delay_mins == 0:
                breakdown = {
                    "Carrier": 0.0, "Weather": 0.0, "NAS (Air Traffic)": 0.0, "Security": 0.0, "Late Aircraft": 0.0
                }
            else:
                breakdown = {
                    "Carrier": round((c_val / total_delay_mins) * 100, 1),
                    "Weather": round((w_val / total_delay_mins) * 100, 1),
                    "NAS (Air Traffic)": round((n_val / total_delay_mins) * 100, 1),
                    "Security": round((s_val / total_delay_mins) * 100, 1),
                    "Late Aircraft": round((l_val / total_delay_mins) * 100, 1)
                }
            
            result.append({
                "carrier": str(row['airline_name']),
                "flights": int(row['flights']),
                "avg_delay": round(float(row['avg_delay']), 2) if not pd.isna(row['avg_delay']) else 0.0,
                "delay_breakdown": breakdown
            })
        return result
    except Exception as e:
        print(f"Error in delays_by_carrier API: {e}", flush=True)
        return {"error": str(e)}

@app.get("/api/route_performance")
def get_route_performance():
    try:
        con = get_db_connection()
        df = con.execute("""
            SELECT 
                origin_airport || ' ➔ ' || dest_airport as route,
                origin_airport,
                coalesce(origin_airport_name, origin_airport) as origin_airport_name,
                origin_city,
                coalesce(origin_latitude, 0.0) as origin_latitude,
                coalesce(origin_longitude, 0.0) as origin_longitude,
                dest_airport,
                coalesce(dest_airport_name, dest_airport) as dest_airport_name,
                dest_city,
                coalesce(dest_latitude, 0.0) as dest_latitude,
                coalesce(dest_longitude, 0.0) as dest_longitude,
                coalesce(total_flights, 0) as total_flights,
                coalesce(on_time_arrival_pct, 100.0) as on_time_arrival_pct,
                coalesce(avg_arr_delay, 0.0) as avg_arr_delay
            FROM mart_route_performance
            ORDER BY total_flights DESC
            LIMIT 25
        """).df()
        con.close()
        
        # Safe JSON-compatible conversions
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/congestion")
def get_congestion():
    try:
        con = get_db_connection()
        df = con.execute("""
            SELECT 
                dep_hour,
                day_of_week,
                coalesce(dep_delay_rate_pct, 0.0) as dep_delay_rate_pct,
                coalesce(avg_dep_delay_mins, 0.0) as avg_dep_delay_mins
            FROM mart_congestion
            ORDER BY day_of_week_num, dep_hour
        """).df()
        con.close()
        
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/sync")
def sync_pipeline():
    try:
        import sys
        import subprocess
        orch_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "orchestrator.py"))
        python_exec = sys.executable
        
        print(f"Triggering pipeline sync subprocess: {python_exec} {orch_path}")
        result = subprocess.run(
            [python_exec, orch_path],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(orch_path))
        )
        
        full_log = result.stdout
        if result.stderr:
            full_log += "\n=== STDERR ===\n" + result.stderr
            
        if result.returncode == 0:
            return {"status": "success", "log": full_log}
        else:
            return {"status": "error", "error": f"Orchestrator failed with exit code {result.returncode}", "log": full_log}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Serve static dashboard frontend
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard"))
app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(frontend_dir, "templates", "index.html"))
