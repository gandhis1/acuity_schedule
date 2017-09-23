import collections
import json
from configparser import ConfigParser

import requests


def main():
    # Read in username and password
    parser = ConfigParser()
    parser.read("credentials.ini")
    acuity_url = parser.get("acuity", "api_url")
    acuity_user_id = parser.get("acuity", "user_id")
    acuity_api_key = parser.get("acuity", "api_key")

    # Get the raw schedule from Acuity
    response = requests.get(acuity_url, auth=(acuity_user_id, acuity_api_key))
    if response.status_code != 200:
        raise RuntimeError("Acuity API request failed")
    appointment_list = response.json()

    # Calculate the pay
    pay_scale = json.load(open("pay_scale.json"))
    cumulative_payment = 0.0
    appointment_durations = []
    for appointment in appointment_list:
        duration = appointment["duration"] + "-minute"
        appointment_durations.append(duration)
        payment = float(pay_scale[duration])
        cumulative_payment += payment

    # Count number of each appointment
    appointment_count = collections.Counter(appointment_durations)

    # Print out the results
    print("Total Income: $" + str(cumulative_payment))
    for duration, pay in pay_scale.items():
        print("{0} appointments: {1} at ${2} each"
              .format(duration, appointment_count[duration], pay))


if __name__ == '__main__':
    main()
