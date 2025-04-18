from pymbta3 import Predictions
import datetime
import math
from tkinter import messagebox
import time as t
import numpy as np


def new_func():
    # Get API key from environment variables
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    mbta_api_key = os.environ.get('MBTA_API_KEY', 'demo')
    at = Predictions(key=mbta_api_key)

    # Get predictions for the 226 bus from Braintree Station to Columbian Square
    # Using route 226, direction 0 (Outbound to Columbian Square)
    braintree_stop_id = "place-brntn"  # Braintree Station
    predictions = at.get(route='226', direction_id=0, stop=braintree_stop_id, route_pattern='226-_-0')
    print("Checking for 226 bus departures from Braintree Station...")

    leadTimes = []

    for prediction in predictions['data']:
        time_format = '%Y-%m-%dT%H:%M:%S%z'
        # Use departure_time or arrival_time based on availability
        time_attribute = prediction['attributes'].get('departure_time') or prediction['attributes'].get('arrival_time')
        if time_attribute:
            op = (datetime.datetime.strptime(time_attribute, time_format).astimezone(
                datetime.timezone.utc) - datetime.datetime.now(datetime.timezone.utc)).seconds/60
            leadTimes.append(math.floor(op))

    print(f"Upcoming bus times in minutes: {leadTimes}")

    # Check if we have any predictions
    if not leadTimes:
        print("No upcoming buses found. Checking again in 3 minutes...")
        t.sleep(3 * 60)
        new_func()  # recur
        return

    # Handle the case where predicted times are out of order
    if len(leadTimes) > 1 and leadTimes[0] > leadTimes[1]:
        print("Warning: Lead times out of order")
        leadTimes.sort()

    # Calculate differences between consecutive predictions
    if len(leadTimes) > 1:
        diff = [leadTimes[i] - leadTimes[i-1] for i in range(1, len(leadTimes))]
        print(f"Time gaps between buses: {diff}")

        # Calculate average time between buses, minus a buffer
        raw_loop_time = np.mean(diff) - 5 if diff else 10
        loopTime = max(3, raw_loop_time)  # Ensure minimum loop time of 3 minutes
        print(f"Calculated loop time: {raw_loop_time:.2f}, Using: {loopTime:.2f} minutes")
    else:
        # If only one prediction, check again in a few minutes
        loopTime = 5
        print("Only one prediction, using default loop time of " + str(loopTime) + " minutes")

    time = leadTimes[0]
    if time > 5 and time < 11:
        messagebox.showinfo(
            "226 Bus in " + str(leadTimes) + ' mins', "Start now")
    else:
        if time > 60:
            messagebox.showinfo(
                "226 Bus in " + str(leadTimes) + ' mins', "Severe Delays")
        print(f"Next bus in {time} minutes. Sleeping for {loopTime:.2f} minutes before checking again...")
        t.sleep(loopTime * 60)
        new_func()  # recur


while True:
    new_func()
