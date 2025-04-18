from pymbta3 import Predictions
import datetime
import math
from tkinter import messagebox
import time as t
import os
from dotenv import load_dotenv

# Load environment variables at module level
load_dotenv()


def get_train_times():
    """Get Red Line train departure times in minutes from now"""
    print("Fetching Red Line train predictions...")

    # Get API key from environment variables
    mbta_api_key = os.environ.get('MBTA_API_KEY', 'demo')
    if mbta_api_key == 'demo':
        print("WARNING: Using demo API key. Set your MBTA_API_KEY in .env file for better results.")

    at = Predictions(key=mbta_api_key)

    predictions = at.get(stop=70079, direction_id=0,
                        route='Red', route_pattern='Red-3-0')

    train_times = []
    time_format = '%Y-%m-%dT%H:%M:%S%z'

    for prediction in predictions.get('data', []):
        departure_time = prediction['attributes'].get('departure_time')
        if departure_time:
            minutes_until = (datetime.datetime.strptime(departure_time, time_format).astimezone(
                datetime.timezone.utc) - datetime.datetime.now(datetime.timezone.utc)).seconds/60
            train_times.append(math.floor(minutes_until))

    # Sort times in ascending order
    train_times.sort()
    return train_times


def get_bus_times():
    """Get 226 bus departure times from Braintree Station in minutes from now"""
    print("Fetching Bus 226 predictions...")

    # Get API key from environment variables
    mbta_api_key = os.environ.get('MBTA_API_KEY', 'demo')
    at = Predictions(key=mbta_api_key)

    # Get predictions for the 226 bus from Braintree Station to Columbian Square
    braintree_stop_id = "place-brntn"  # Braintree Station
    predictions = at.get(route='226', direction_id=0, stop=braintree_stop_id, route_pattern='226-_-0')

    bus_times = []
    time_format = '%Y-%m-%dT%H:%M:%S%z'

    for prediction in predictions.get('data', []):
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
    print(f"Finding optimal connections (minimum travel time: {min_travel_time} minutes)...")
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


def format_time(minutes_from_now):
    """Format minutes from now as HH:MM AM/PM"""
    future_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes_from_now)
    return future_time.strftime("%I:%M %p")


def commute_bridge():
    """Main function to bridge the commute between Red Line and 226 bus"""
    # Print header with timestamp
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 70)
    print(f"MBTA COMMUTE BRIDGE: RED LINE TO BUS 226 - {current_time}")
    print("=" * 70)

    try:
        # Get Red Line train times
        train_times = get_train_times()

        if not train_times:
            print("\nNo upcoming Red Line trains found. Checking again in 3 minutes...")
            t.sleep(3 * 60)
            commute_bridge()
            return

        # Print upcoming train times
        print("\nUPCOMING RED LINE TRAINS:")
        for i, minutes in enumerate(train_times):
            arrival_time = format_time(minutes)
            print(f"  Train {i+1}: Departing in {minutes} minutes (at {arrival_time})")

        # Get Bus 226 times
        bus_times = get_bus_times()

        if not bus_times:
            print("\nNo upcoming 226 buses found. Checking again in 3 minutes...")
            t.sleep(3 * 60)
            commute_bridge()
            return

        # Print upcoming bus times
        print("\nUPCOMING BUS 226 DEPARTURES FROM BRAINTREE:")
        for i, minutes in enumerate(bus_times):
            departure_time = format_time(minutes)
            print(f"  Bus {i+1}: Departing in {minutes} minutes (at {departure_time})")

        # Find viable connections with 30-minute minimum travel time
        connections = find_connections(train_times, bus_times, min_travel_time=30)

        if not connections:
            print("\nNo viable train-bus connections found. Checking again in 5 minutes...")
            t.sleep(5 * 60)
            commute_bridge()
            return

        # Find the optimal connection (minimum total journey time)
        optimal = min(connections, key=lambda x: x["total_journey"])

        # Print connections in a table format
        print("\n" + "=" * 70)
        print("VIABLE CONNECTIONS (TRAIN → BUS):")
        print("-" * 70)
        print(f"{'#':<3} {'Train':<20} {'Bus':<20} {'Wait':<15} {'Total':<10}")
        print(f"{'':3} {'Departure':<20} {'Departure':<20} {'at Braintree':<15} {'Journey':<10}")
        print("-" * 70)

        for i, conn in enumerate(connections):
            train_time_str = f"{conn['train_time']} min ({format_time(conn['train_time'])})"
            bus_time_str = f"{conn['bus_time']} min ({format_time(conn['bus_time'])})"
            wait_time_str = f"{conn['wait_time']} min"
            total_str = f"{conn['total_journey']} min"

            # Mark optimal connection
            marker = "→" if conn == optimal else " "

            print(f"{marker} {i+1:<2} {train_time_str:<20} {bus_time_str:<20} {wait_time_str:<15} {total_str:<10}")

        print("-" * 70)
        print(f"Optimal connection: Train in {optimal['train_time']} min → Bus in {optimal['bus_time']} min")
        print("=" * 70)

        # Determine if user should leave soon for the optimal train
        if 5 <= optimal["train_time"] <= 10:
            alert_message = (f"Time to leave! Catch the train in {optimal['train_time']} mins "
                            f"to connect with bus in {optimal['bus_time']} mins. \n"
                            f"Wait time at Braintree: {optimal['wait_time']} mins.")
            print(f"\n*** TIME TO LEAVE NOW! ***\n{alert_message}")
            messagebox.showinfo("Commute Bridge Alert", alert_message)
        elif optimal["train_time"] > 60:
            alert_message = f"Severe train delays detected. Next train in {optimal['train_time']} mins."
            print(f"\n!!! SEVERE DELAYS DETECTED !!!\n{alert_message}")
            messagebox.showinfo("Commute Bridge Alert", alert_message)

        # Calculate time to sleep before checking again
        next_check_time = min(5, max(1, optimal["train_time"] - 10))  # Check at least 10 mins before optimal train
        print(f"\nChecking again in {next_check_time} minutes...")
        print("=" * 70)
        t.sleep(next_check_time * 60)
        commute_bridge()

    except Exception as e:
        print(f"\nError in commute bridge: {str(e)}")
        print("Retrying in 5 minutes...")
        t.sleep(5 * 60)
        commute_bridge()


if __name__ == "__main__":
    try:
        print("Starting MBTA Commute Bridge...")
        print("Press Ctrl+C to exit")
        commute_bridge()
    except KeyboardInterrupt:
        print("\nExiting commute bridge. Have a safe trip!")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print("Restarting in 5 minutes...")
        t.sleep(5 * 60)
        commute_bridge()
