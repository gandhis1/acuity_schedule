import collections
import json
from datetime import date, timedelta

import requests
from dateutil.parser import parse

import smtplib

message = "\n"


def log(msg):
    global message
    message += (msg + "\n")
    print(msg)


def main():
    # Read in username and password
    config = json.load(open("config.json"))
    acuity_url = config["acuity"]["api_url"]
    acuity_user_id = config["acuity"]["user_id"]
    acuity_api_key = config["acuity"]["api_key"]
    pay_scale = config["pay_scale"]
    gmail_user = config["gmail"]["user"]
    gmail_app_password = config["gmail"]["app_password"]
    email_recipients = config["email"]["recipients"]
    email_subject = config["email"]["subject"]

    # Get the raw schedule from Acuity
    response = requests.get(acuity_url, auth=(acuity_user_id, acuity_api_key))
    if response.status_code != 200:
        raise RuntimeError("Acuity API request failed")
    appointment_list = response.json()

    # Upcoming appointments
    log("Upcoming Appointments:\n")
    upcoming_appts = [appt for appt in appointment_list
                      if parse(appt["datetime"]).date() >= date.today()]
    for appt in sorted(upcoming_appts, key=lambda x: parse(x["datetime"])):
        appt_start_datetime = parse(appt["datetime"]).strftime("%b %d %#I:%M")
        appt_end_time = parse(appt["endTime"]).strftime("%#I:%M %p")
        appt_name = "{0} {1}".format(appt["firstName"], appt["lastName"])
        appt_duration = appt["duration"]
        appt_reason = [x for x in appt["forms"][0]["values"]
                       if x["fieldID"] == 2451841][0]["value"]
        log("{0} - {1}: {2} ({3} min){4}"
            .format(appt_start_datetime, appt_end_time, appt_name,
                    appt_duration,
                    " [{}]".format(appt_reason)
                    if appt_reason.strip() != "" else ""))

    # Iterate through all pay period start dates
    log("\nIncome Calculations:\n")
    first_start_date = config["pay_period"]["first_start_date"]
    pay_period_start_date = parse(first_start_date).date()
    while(pay_period_start_date <= date.today()):
        pay_period_end_date = pay_period_start_date + timedelta(days=14)
        log("Pay Period {0}-{1}:"
            .format(pay_period_start_date.strftime("%#m/%#d/%Y"),
                    pay_period_end_date.strftime("%#m/%#d/%Y")))
        pay_period_appointment_list = [
            appt for appt in appointment_list
            if (parse(appt["datetime"]).date() >= pay_period_start_date) and
               (parse(appt["datetime"]).date() < pay_period_end_date)
        ]
        calculate_income(pay_period_appointment_list, pay_scale)
        pay_period_start_date = pay_period_end_date
        log("")

    # Send an email
    email_text = ("From: {0}\nTo: {1}\nSubject: {2}\n\n{3}"
                  .format(gmail_user,
                          ", ".join(email_recipients),
                          email_subject,
                          message))
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.ehlo()
    server.login(gmail_user, gmail_app_password)
    server.sendmail(gmail_user, email_recipients, email_text)


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
    log("  Total Income: $" + str(cumulative_payment))
    log("  Total Appointments: " + str(len(appointment_list)))
    for duration, pay in sorted(pay_scale.items(), key=lambda x: x[0]):
        num_appts = appointment_count[duration]
        if num_appts > 0:
            log("  {0}: {1} at ${2} each = ${3}"
                .format(duration, num_appts, pay, pay * num_appts))


if __name__ == '__main__':
    main()
