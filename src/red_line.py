import datetime
import math
import tkinter as tk
from tkinter import messagebox
import time as t
import numpy as np
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
            print("No predictions available. Checking again in 3 minutes...")
            t.sleep(3 * 60)
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
            print("No upcoming trains found. Checking again in 3 minutes...")
            t.sleep(3 * 60)
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

        # Calculate time gaps between trains
        if len(lead_times) > 1:
            diff = [lead_times[i] - lead_times[i-1] for i in range(1, len(lead_times))]
            print("\nTime gaps between trains (minutes):", diff)

            # Calculate average time between trains, minus a buffer
            raw_loop_time = np.mean(diff) - 5 if diff else 10
            loop_time = max(3, raw_loop_time)  # Ensure minimum loop time of 3 minutes
            print(f"Calculated check interval: {loop_time:.1f} minutes")
        else:
            # If only one prediction, check again in a few minutes
            loop_time = 5
            print("Only one train prediction available. Using default check interval of 5 minutes.")

        # Get the next train time
        next_train = lead_times[0]

        # Determine if user should leave soon
        if 5 <= next_train <= 10:
            print("\n*** TIME TO LEAVE NOW! ***")
            show_alert(
                "Red Line Alert", f"Time to leave now! Train arriving in {next_train} minutes.")
        elif next_train > 60:
            print("\n!!! SEVERE DELAYS DETECTED !!!")
            show_alert(
                "Red Line Alert", f"Severe delays detected. Next train in {next_train} minutes.")

        # Print next check time
        print(f"\nNext train in {next_train} minutes. Checking again in {loop_time:.1f} minutes...")
        print("=" * 60)

        # Sleep before checking again
        t.sleep(int(loop_time * 60))
        check_red_line()  # recur

    except Exception as e:
        print(f"Error fetching Red Line predictions: {str(e)}")
        print("Retrying in 5 minutes...")
        t.sleep(5 * 60)
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
        print("Restarting in 5 minutes...")
        t.sleep(5 * 60)
        check_red_line()
