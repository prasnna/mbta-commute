import datetime
import math
import tkinter as tk
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

# Load environment variables
load_dotenv()

# --- Configuration Variables with Defaults ---
# Alerting (Shared)
ALERT_LEAVE_NOW_WINDOW_MIN = int(os.environ.get('MBTA_ALERT_LEAVE_NOW_WINDOW_MIN_MINUTES', '5'))
ALERT_LEAVE_NOW_WINDOW_MAX = int(os.environ.get('MBTA_ALERT_LEAVE_NOW_WINDOW_MAX_MINUTES', '10'))
ALERT_SEVERE_DELAY_THRESHOLD = int(os.environ.get('MBTA_ALERT_SEVERE_DELAY_THRESHOLD_MINUTES', '60'))

# Retry/Sleep Durations (Shared)
RETRY_NO_DATA_MINUTES = int(os.environ.get('MBTA_RETRY_NO_DATA_MINUTES', '3'))
RETRY_ERROR_MINUTES = int(os.environ.get('MBTA_RETRY_ERROR_MINUTES', '5'))

# Monitor Specific Loop Time Calculation
MONITOR_MIN_LOOP_MINUTES = int(os.environ.get('MBTA_MONITOR_MIN_LOOP_MINUTES', '2'))
MONITOR_MAX_LOOP_MINUTES = int(os.environ.get('MBTA_MONITOR_MAX_LOOP_MINUTES', '10'))
MONITOR_CHECK_EARLY_BUFFER_MINUTES = int(os.environ.get('MBTA_MONITOR_CHECK_EARLY_BUFFER_MINUTES', '2'))
MONITOR_SINGLE_PREDICTION_LOOP_MINUTES = int(os.environ.get('MBTA_MONITOR_SINGLE_PREDICTION_LOOP_MINUTES', '5'))
# --- End Configuration Variables ---


def show_alert(title, message):
    """Display an alert box that blocks until the user closes it."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showinfo(title, message)
    root.destroy()


def check_red_line():
    """Check Red Line train arrivals and notify when it's time to leave"""
    # Print header with timestamp
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 60)
    print(f"RED LINE MONITOR - {current_time}")
    print("=" * 60)

    print("Fetching Red Line predictions from MBTA API...")

    # Get API key from environment variables
    mbta_api_key = os.environ.get('MBTA_API_KEY', 'demo')
    if mbta_api_key == 'demo':
        print("WARNING: Using demo API key. Set your MBTA_API_KEY in .env file for better results.")

    at = Predictions(key=mbta_api_key)

    try:
        # Get predictions for Red Line trains (Braintree branch, northbound)
        predictions = at.get(stop=70079, direction_id=0,
                            route='Red', route_pattern='Red-3-0')

        if not predictions.get('data'):
            print(f"No predictions available. Checking again in {RETRY_NO_DATA_MINUTES} minutes...")
            t.sleep(RETRY_NO_DATA_MINUTES * 60)
            check_red_line()  # recur
            return

        # Extract arrival times in minutes
        lead_times = []
        time_format = '%Y-%m-%dT%H:%M:%S%z'

        for prediction in predictions['data']:
            departure_time = prediction['attributes'].get('departure_time')
            if departure_time:
                minutes_until = (datetime.datetime.strptime(departure_time, time_format).astimezone(
                    datetime.timezone.utc) - datetime.datetime.now(datetime.timezone.utc)).seconds/60
                lead_times.append(math.floor(minutes_until))

        if not lead_times:
            print(f"No upcoming trains found. Checking again in {RETRY_NO_DATA_MINUTES} minutes...")
            t.sleep(RETRY_NO_DATA_MINUTES * 60)
            check_red_line()  # recur
            return

        # Sort times in ascending order
        lead_times.sort()

        # Print upcoming train times
        print("\nUPCOMING RED LINE TRAINS:")
        for i, minutes in enumerate(lead_times):
            # Format time as HH:MM
            arrival_time = (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).strftime("%I:%M %p")
            print(f"  Train {i+1}: Arriving in {minutes} minutes (at {arrival_time})")

        # --- New loop_time calculation ---
        next_train_minutes = lead_times[0]
        loop_time_calculated = 0

        if len(lead_times) == 1:
           loop_time_calculated = MONITOR_SINGLE_PREDICTION_LOOP_MINUTES
        else:
           # If the next event is already within the "leave now" window (up to its max)
           # or even sooner, we should check frequently.
           if next_train_minutes <= ALERT_LEAVE_NOW_WINDOW_MAX:
               loop_time_calculated = MONITOR_MIN_LOOP_MINUTES
           else:
               # Schedule the check MONITOR_CHECK_EARLY_BUFFER_MINUTES minutes before the ALERT_LEAVE_NOW_WINDOW_MAX starts.
               # Example: next_event=20, ALERT_WINDOW_MAX=10, CHECK_EARLY_BUFFER=2.
               # We want to check when next_event is 12 mins away (10+2). So sleep for 20 - 12 = 8 mins.
               target_check_point = next_train_minutes - (ALERT_LEAVE_NOW_WINDOW_MAX + MONITOR_CHECK_EARLY_BUFFER_MINUTES)

               if target_check_point < MONITOR_MIN_LOOP_MINUTES:
                   loop_time_calculated = MONITOR_MIN_LOOP_MINUTES
               else:
                   loop_time_calculated = min(MONITOR_MAX_LOOP_MINUTES, target_check_point)

        loop_time = math.floor(loop_time_calculated) # Use floor for integer minutes
        loop_time = max(1, loop_time) # Ensure loop_time is at least 1 minute practically.
        print(f"Calculated check interval: {loop_time} minutes")
        # --- End new loop_time calculation ---

        # Get the next train time (already have as next_train_minutes)
        # Determine if user should leave soon
        if ALERT_LEAVE_NOW_WINDOW_MIN <= next_train_minutes <= ALERT_LEAVE_NOW_WINDOW_MAX:
            print("\n*** TIME TO LEAVE NOW! ***")
            show_alert(
                "Red Line Alert", f"Time to leave now! Train arriving in {next_train_minutes} minutes.")
        elif next_train_minutes > ALERT_SEVERE_DELAY_THRESHOLD:
            print("\n!!! SEVERE DELAYS DETECTED !!!")
            show_alert(
                "Red Line Alert", f"Severe delays detected. Next train in {next_train_minutes} minutes.")

        # Print next check time
        print(f"\nNext train in {next_train_minutes} minutes. Checking again in {loop_time} minutes...")
        print("=" * 60)

        # Sleep before checking again
        t.sleep(loop_time * 60) # loop_time is already an int due to math.floor
        check_red_line()  # recur

    except Exception as e:
        print(f"Error fetching Red Line predictions: {str(e)}")
        print(f"Retrying in {RETRY_ERROR_MINUTES} minutes...")
        t.sleep(RETRY_ERROR_MINUTES * 60)
        check_red_line()  # recur


if __name__ == "__main__":
    try:
        print("Starting Red Line Monitor...")
        print("Press Ctrl+C to exit")
        check_red_line()
    except KeyboardInterrupt:
        print("\nExiting Red Line Monitor. Have a safe trip!")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print(f"Restarting in {RETRY_ERROR_MINUTES} minutes...")
        t.sleep(RETRY_ERROR_MINUTES * 60)
        check_red_line()
