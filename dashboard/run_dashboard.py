import os
import sys
import time
import webbrowser
import threading
import uvicorn

# Add the project root to python path so we can import src.api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api import app

def open_browser():
    # Wait a moment for uvicorn to spin up
    time.sleep(1.5)
    print("Opening dashboard in browser...")
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("=" * 60)
    print("STARTING AEROFLOW ANALYTICS DASHBOARD")
    print("=" * 60)
    
    # Check if database exists, if not prompt
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "aviation_dw.db")
    if not os.path.exists(db_path):
        print("\n[NOTE] Database not found. You will need to trigger 'Sync Pipeline'")
        print("from the dashboard sidebar to run the initial ingestion & transformation.\n")
    
    # Start browser opening thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run uvicorn server
    uvicorn.run(app, host="127.0.0.1", port=8000)
