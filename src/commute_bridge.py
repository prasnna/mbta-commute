from pymbta3 import Predictions
import datetime
import math
from tkinter import messagebox
import time as t
import numpy as np


def get_train_times():
    """Get Red Line train departure times in minutes from now"""
    # Get API key from environment variables
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    mbta_api_key = os.environ.get('MBTA_API_KEY', 'demo')
    at = Predictions(key=mbta_api_key)

    predictions = at.get(stop=70079, direction_id=0,
                        route='Red', route_pattern='Red-3-0')

    train_times = []
    for prediction in predictions['data']:
        time_format = '%Y-%m-%dT%H:%M:%S%z'
        departure_time = prediction['attributes']['departure_time']
        if departure_time:
            minutes_until = (datetime.datetime.strptime(departure_time, time_format).astimezone(
                datetime.timezone.utc) - datetime.datetime.now(datetime.timezone.utc)).seconds/60
            train_times.append(math.floor(minutes_until))

    # Sort times in ascending order
    train_times.sort()
    return train_times


def get_bus_times():
    """Get 226 bus departure times from Braintree Station in minutes from now"""
    # Get API key from environment variables
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    mbta_api_key = os.environ.get('MBTA_API_KEY', 'demo')
    at = Predictions(key=mbta_api_key)

    # Get predictions for the 226 bus from Braintree Station to Columbian Square
    braintree_stop_id = "place-brntn"  # Braintree Station
    predictions = at.get(route='226', direction_id=0, stop=braintree_stop_id, route_pattern='226-_-0')

    bus_times = []
    for prediction in predictions['data']:
        time_format = '%Y-%m-%dT%H:%M:%S%z'
        time_attribute = prediction['attributes'].get('departure_time') or prediction['attributes'].get('arrival_time')
        if time_attribute:
            minutes_until = (datetime.datetime.strptime(time_attribute, time_format).astimezone(
                datetime.timezone.utc) - datetime.datetime.now(datetime.timezone.utc)).seconds/60
            bus_times.append(math.floor(minutes_until))

    # Sort times in ascending order
    bus_times.sort()
    return bus_times


def find_connections(train_times, bus_times, min_travel_time=30):
    """Find viable train-bus connections with minimum travel time"""
    connections = []

    for train_time in train_times:
        viable_buses = []
        for bus_time in bus_times:
            # Check if there's enough time between train departure and bus departure
            if bus_time >= (train_time + min_travel_time):
                wait_at_braintree = bus_time - (train_time + min_travel_time)
                viable_buses.append({
                    "bus_time": bus_time,
                    "wait_time": wait_at_braintree
                })

        if viable_buses:
            # Find the bus with minimum wait time
            best_bus = min(viable_buses, key=lambda x: x["wait_time"])
            connections.append({
                "train_time": train_time,
                "bus_time": best_bus["bus_time"],
                "wait_time": best_bus["wait_time"],
                "total_journey": best_bus["bus_time"] - train_time
            })

    return connections


def commute_bridge():
    """Main function to bridge the commute between Red Line and 226 bus"""
    print("\n=== MBTA Commute Bridge: Red Line to 226 Bus ===")
    print("Fetching train schedules...")
    train_times = get_train_times()

    if not train_times:
        print("No upcoming Red Line trains found. Checking again in 3 minutes...")
        t.sleep(3 * 60)
        commute_bridge()
        return

    print(f"Upcoming Red Line trains in: {train_times} minutes")

    print("Fetching bus schedules...")
    bus_times = get_bus_times()

    if not bus_times:
        print("No upcoming 226 buses found. Checking again in 3 minutes...")
        t.sleep(3 * 60)
        commute_bridge()
        return

    print(f"Upcoming 226 buses from Braintree in: {bus_times} minutes")

    # Find viable connections with 30-minute minimum travel time
    connections = find_connections(train_times, bus_times, min_travel_time=30)

    if not connections:
        print("No viable train-bus connections found. Checking again in 5 minutes...")
        t.sleep(5 * 60)
        commute_bridge()
        return

    # Find the optimal connection (minimum total journey time)
    optimal = min(connections, key=lambda x: x["total_journey"])

    print("\n=== Viable Connections ===")
    for i, conn in enumerate(connections):
        optimal_marker = " [OPTIMAL]" if conn == optimal else ""
        print(f"Connection {i+1}{optimal_marker}:")
        print(f"  Train departs in: {conn['train_time']} minutes")
        print(f"  Bus departs in: {conn['bus_time']} minutes")
        print(f"  Wait at Braintree: {conn['wait_time']} minutes")
        print(f"  Total journey time: {conn['total_journey']} minutes\n")

    # Determine if user should leave soon for the optimal train
    if 5 <= optimal["train_time"] <= 10:
        messagebox.showinfo(
            "Commute Bridge Alert",
            f"Time to leave! Catch the train in {optimal['train_time']} mins to connect with "
            f"bus in {optimal['bus_time']} mins. Wait time at Braintree: {optimal['wait_time']} mins."
        )
    elif optimal["train_time"] > 60:
        messagebox.showinfo(
            "Commute Bridge Alert",
            f"Severe train delays detected. Next train in {optimal['train_time']} mins."
        )

    # Calculate time to sleep before checking again
    next_check_time = min(5, max(1, optimal["train_time"] - 10))  # Check at least 10 mins before optimal train
    print(f"Checking again in {next_check_time} minutes...")
    t.sleep(next_check_time * 60)
    commute_bridge()


if __name__ == "__main__":
    try:
        commute_bridge()
    except KeyboardInterrupt:
        print("\nExiting commute bridge. Have a safe trip!")
    except Exception as e:
        print(f"Error in commute bridge: {str(e)}")
        print("Restarting in 5 minutes...")
        t.sleep(5 * 60)
        commute_bridge()
