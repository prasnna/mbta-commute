from pymbta3 import Predictions
import datetime
import math
from tkinter import messagebox
import time as t
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables at module level
load_dotenv()


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
            print("No predictions available. Checking again in 3 minutes...")
            t.sleep(3 * 60)
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
            print("No upcoming buses found. Checking again in 3 minutes...")
            t.sleep(3 * 60)
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

        # Calculate time gaps between buses
        if len(bus_times) > 1:
            diff = [bus_times[i] - bus_times[i-1] for i in range(1, len(bus_times))]
            print("\nTime gaps between buses (minutes):", diff)

            # Calculate average time between buses, minus a buffer
            raw_loop_time = np.mean(diff) - 5 if diff else 10
            loop_time = max(3, raw_loop_time)  # Ensure minimum loop time of 3 minutes
            print(f"Calculated check interval: {loop_time:.1f} minutes")
        else:
            # If only one prediction, check again in a few minutes
            loop_time = 5
            print("Only one bus prediction available. Using default check interval of 5 minutes.")

        # Get the next bus time
        next_bus = bus_times[0]
        
        # Determine if user should leave soon
        if 5 <= next_bus <= 10:
            print("\n*** TIME TO LEAVE NOW! ***")
            messagebox.showinfo(
                f"Bus 226 Alert", f"Time to leave now! Bus departing in {next_bus} minutes.")
        elif next_bus > 60:
            print("\n!!! SEVERE DELAYS DETECTED !!!")
            messagebox.showinfo(
                f"Bus 226 Alert", f"Severe delays detected. Next bus in {next_bus} minutes.")
        
        # Print next check time
        print(f"\nNext bus in {next_bus} minutes. Checking again in {loop_time:.1f} minutes...")
        print("=" * 60)
        
        # Sleep before checking again
        t.sleep(int(loop_time * 60))
        check_bus_226()  # recur
        
    except Exception as e:
        print(f"Error fetching Bus 226 predictions: {str(e)}")
        print("Retrying in 5 minutes...")
        t.sleep(5 * 60)
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
        print("Restarting in 5 minutes...")
        t.sleep(5 * 60)
        check_bus_226()
