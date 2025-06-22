import datetime
import math
from tkinter import messagebox
import time as t
import os
from dotenv import load_dotenv

# Import the SSL-fixed version of Predictions
try:
    # Try to use our SSL fix first
    from mbta_ssl_fix import PredictionsSSL as Predictions
    print("Using SSL-fixed version of MBTA API client")
except ImportError:
    # Fall back to original if not available
    from pymbta3 import Predictions
    print("Using standard pymbta3 library")

# Load environment variables at module level
load_dotenv()

# --- Configuration Variables with Defaults ---
# Alerting (Shared)
ALERT_LEAVE_NOW_WINDOW_MIN = int(os.environ.get('MBTA_ALERT_LEAVE_NOW_WINDOW_MIN_MINUTES', '5'))
ALERT_LEAVE_NOW_WINDOW_MAX = int(os.environ.get('MBTA_ALERT_LEAVE_NOW_WINDOW_MAX_MINUTES', '10'))
ALERT_SEVERE_DELAY_THRESHOLD = int(os.environ.get('MBTA_ALERT_SEVERE_DELAY_THRESHOLD_MINUTES', '60'))

# Retry/Sleep Durations (Shared)
RETRY_NO_DATA_MINUTES = int(os.environ.get('MBTA_RETRY_NO_DATA_MINUTES', '3'))
RETRY_ERROR_MINUTES = int(os.environ.get('MBTA_RETRY_ERROR_MINUTES', '5'))

# Monitor Specific Loop Time Calculation (Shared with red_line.py)
MONITOR_MIN_LOOP_MINUTES = int(os.environ.get('MBTA_MONITOR_MIN_LOOP_MINUTES', '2'))
MONITOR_MAX_LOOP_MINUTES = int(os.environ.get('MBTA_MONITOR_MAX_LOOP_MINUTES', '10'))
MONITOR_CHECK_EARLY_BUFFER_MINUTES = int(os.environ.get('MBTA_MONITOR_CHECK_EARLY_BUFFER_MINUTES', '2'))
MONITOR_SINGLE_PREDICTION_LOOP_MINUTES = int(os.environ.get('MBTA_MONITOR_SINGLE_PREDICTION_LOOP_MINUTES', '5'))
# --- End Configuration Variables ---


def check_bus_226():
    """Check Bus 226 arrivals at Braintree Station and notify when it's time to leave"""
    # Print header with timestamp
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 60)
    print(f"BUS 226 MONITOR - {current_time}")
    print("=" * 60)

    print("Fetching Bus 226 predictions from MBTA API...")

    # Get API key from environment variables
    mbta_api_key = os.environ.get('MBTA_API_KEY', 'demo')
    if mbta_api_key == 'demo':
        print("WARNING: Using demo API key. Set your MBTA_API_KEY in .env file for better results.")

    at = Predictions(key=mbta_api_key)

    try:
        # Get predictions for the 226 bus from Braintree Station to Columbian Square
        # Using route 226, direction 0 (Outbound to Columbian Square)
        braintree_stop_id = "place-brntn"  # Braintree Station
        predictions = at.get(route='226', direction_id=0, stop=braintree_stop_id, route_pattern='226-_-0')

        if not predictions.get('data'):
            print(f"No predictions available. Checking again in {RETRY_NO_DATA_MINUTES} minutes...")
            t.sleep(RETRY_NO_DATA_MINUTES * 60)
            check_bus_226()  # recur
            return

        # Extract arrival times in minutes
        bus_times = []
        time_format = '%Y-%m-%dT%H:%M:%S%z'

        print("\nProcessing bus departure predictions...")
        for prediction in predictions['data']:
            # Use departure_time or arrival_time based on availability
            time_attribute = prediction['attributes'].get('departure_time') or prediction['attributes'].get('arrival_time')
            if time_attribute:
                minutes_until = (datetime.datetime.strptime(time_attribute, time_format).astimezone(
                    datetime.timezone.utc) - datetime.datetime.now(datetime.timezone.utc)).seconds/60
                bus_times.append(math.floor(minutes_until))

        # Check if we have any predictions
        if not bus_times:
            print(f"No upcoming buses found. Checking again in {RETRY_NO_DATA_MINUTES} minutes...")
            t.sleep(RETRY_NO_DATA_MINUTES * 60)
            check_bus_226()  # recur
            return

        # Sort times in ascending order
        bus_times.sort()

        # Print upcoming bus times
        print("\nUPCOMING BUS 226 DEPARTURES FROM BRAINTREE STATION:")
        for i, minutes in enumerate(bus_times):
            # Format time as HH:MM
            departure_time = (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).strftime("%I:%M %p")
            print(f"  Bus {i+1}: Departing in {minutes} minutes (at {departure_time})")

        # --- New loop_time calculation ---
        next_bus_minutes = bus_times[0]
        loop_time_calculated = 0

        if len(bus_times) == 1:
           loop_time_calculated = MONITOR_SINGLE_PREDICTION_LOOP_MINUTES
        else:
           if next_bus_minutes <= ALERT_LEAVE_NOW_WINDOW_MAX:
               loop_time_calculated = MONITOR_MIN_LOOP_MINUTES
           else:
               target_check_point = next_bus_minutes - (ALERT_LEAVE_NOW_WINDOW_MAX + MONITOR_CHECK_EARLY_BUFFER_MINUTES)

               if target_check_point < MONITOR_MIN_LOOP_MINUTES:
                   loop_time_calculated = MONITOR_MIN_LOOP_MINUTES
               else:
                   loop_time_calculated = min(MONITOR_MAX_LOOP_MINUTES, target_check_point)

        loop_time = math.floor(loop_time_calculated)
        loop_time = max(1, loop_time)
        print(f"Calculated check interval: {loop_time} minutes")
        # --- End new loop_time calculation ---

        # Get the next bus time (already have as next_bus_minutes)
        # Determine if user should leave soon
        if ALERT_LEAVE_NOW_WINDOW_MIN <= next_bus_minutes <= ALERT_LEAVE_NOW_WINDOW_MAX:
            print("\n*** TIME TO LEAVE NOW! ***")
            messagebox.showinfo(
                f"Bus 226 Alert", f"Time to leave now! Bus departing in {next_bus_minutes} minutes.")
        elif next_bus_minutes > ALERT_SEVERE_DELAY_THRESHOLD:
            print("\n!!! SEVERE DELAYS DETECTED !!!")
            messagebox.showinfo(
                f"Bus 226 Alert", f"Severe delays detected. Next bus in {next_bus_minutes} minutes.")

        # Print next check time
        print(f"\nNext bus in {next_bus_minutes} minutes. Checking again in {loop_time} minutes...")
        print("=" * 60)

        # Sleep before checking again
        t.sleep(loop_time * 60) # loop_time is already int
        check_bus_226()  # recur

    except Exception as e:
        print(f"Error fetching Bus 226 predictions: {str(e)}")
        print(f"Retrying in {RETRY_ERROR_MINUTES} minutes...")
        t.sleep(RETRY_ERROR_MINUTES * 60)
        check_bus_226()  # recur


if __name__ == "__main__":
    try:
        print("Starting Bus 226 Monitor...")
        print("Press Ctrl+C to exit")
        check_bus_226()
    except KeyboardInterrupt:
        print("\nExiting Bus 226 Monitor. Have a safe trip!")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print(f"Restarting in {RETRY_ERROR_MINUTES} minutes...")
        t.sleep(RETRY_ERROR_MINUTES * 60)
        check_bus_226()
