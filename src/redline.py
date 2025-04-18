from pymbta3 import Predictions
import datetime
import math
from tkinter import messagebox
import time as t
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def new_func():
    # Get API key from environment variables
    mbta_api_key = os.environ.get('MBTA_API_KEY', 'demo')
    at = Predictions(key=mbta_api_key)

    predictions = at.get(stop=70079, direction_id=0,
                         route='Red', route_pattern='Red-3-0')
    #print(predictions)

    leadTimes = []

    for prediction in predictions['data']:
        time = '%Y-%m-%dT%H:%M:%S%z'
        op = (datetime.datetime.strptime(prediction['attributes']['departure_time'], time).astimezone(
            datetime.timezone.utc) - datetime.datetime.now(datetime.timezone.utc)).seconds/60
        leadTimes.append(math.floor(op))

    print(leadTimes)

    if leadTimes[0] > leadTimes[1]:
        print("Weirdo, should not be possible")
        leadTimes.pop(0)

    diff = [x - leadTimes[i - 1] for i, x in enumerate(leadTimes)][1:]

    print(diff)

    loopTime = np.mean(diff) - 5

    print(loopTime)

    time = leadTimes[0]
    if time > 5 and time < 11:
        messagebox.showinfo(
            "Red Line in " + str(leadTimes) + ' mins', "Start now")
    else:
        if time > 60:
            messagebox.showinfo(
                "Red Line in " + str(leadTimes) + ' mins', "Severe Delays")
        print("sleeping for " + str(loopTime) + " mins")
        t.sleep(60)
        new_func()  # recur


while True:
    new_func()
