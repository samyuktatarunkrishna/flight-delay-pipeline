import os
import duckdb
import pandas as pd

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "aviation_dw.db"))
EXPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tableau_exports"))

def export_to_tableau():
    print("=" * 60)
    print("EXPORTING DB TABLES FOR TABLEAU INTERFACE")
    print("=" * 60)
    
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Run pipeline first.")
        
    os.makedirs(EXPORT_DIR, exist_ok=True)
    con = duckdb.connect(DB_PATH, read_only=True)
    
    # Adding 'stg_flights' to export the complete 1M+ detailed raw-level records dataset
    tables = ["stg_flights", "fct_delays", "mart_route_performance", "mart_congestion", "airports", "airlines"]
    
    for table in tables:
        try:
            print(f"Exporting table: {table}...")
            df = con.execute(f"SELECT * FROM {table}").df()
            
            output_file = os.path.join(EXPORT_DIR, f"{table}.csv")
            df.to_csv(output_file, index=False)
            print(f"Successfully saved {len(df):,} rows to {output_file}")
        except Exception as e:
            print(f"Failed to export {table}: {e}")
            
    con.close()
    print("\n" + "=" * 60)
    print(f"TABLEAU EXPORTS COMPLETED. Files saved to: {EXPORT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    export_to_tableau()
