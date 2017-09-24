import collections
import json
from datetime import date, timedelta

import requests
from dateutil.parser import parse


def main():
    # Read in username and password
    config = json.load(open("config.json"))
    acuity_url = config["acuity"]["api_url"]
    acuity_user_id = config["acuity"]["user_id"]
    acuity_api_key = config["acuity"]["api_key"]

    # Get the raw schedule from Acuity
    response = requests.get(acuity_url, auth=(acuity_user_id, acuity_api_key))
    if response.status_code != 200:
        raise RuntimeError("Acuity API request failed")
    appointment_list = response.json()

    # Calculate the pay
    pay_scale = config["pay_scale"]

    # Iterate through all pay period start dates
    first_start_date = config["pay_period"]["first_start_date"]
    pay_period_start_date = parse(first_start_date).date()
    while(pay_period_start_date <= date.today()):
        pay_period_end_date = pay_period_start_date + timedelta(days=14)
        print("Pay Period {0}-{1}:"
              .format(pay_period_start_date.strftime("%#m/%#d/%Y"),
                      pay_period_end_date.strftime("%#m/%#d/%Y")))
        pay_period_appointment_list = [
            appt for appt in appointment_list
            if (parse(appt["datetime"]).date() >= pay_period_start_date) and
               (parse(appt["datetime"]).date() < pay_period_end_date)
        ]
        calculate_income(pay_period_appointment_list, pay_scale)
        pay_period_start_date = pay_period_end_date
        print("")


def calculate_income(appointment_list, pay_scale):
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
    print("  Total Income: $" + str(cumulative_payment))
    print("  Total Appointments: " + str(len(appointment_list)))
    for duration, pay in pay_scale.items():
        print("  {0}: {1} at ${2} each = ${3}"
              .format(duration, appointment_count[duration], 
                      pay, pay * appointment_count[duration]))


if __name__ == '__main__':
    main()
