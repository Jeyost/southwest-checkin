#!/usr/bin/env python3
import time

__version__ = "v1.1"

import sys
from typing import List

from lib.config import Config
from lib.notification_handler import NotificationHandler
from multiprocessing import Process

from lib.flight_retriever import AccountFlightRetriever, FlightRetriever


def schedule_confirmation_number(config, flight):
    flight_retriever = FlightRetriever(config, flight['first_name'], flight['last_name'])
    flight_retriever.checkin_scheduler.refresh_headers()
    flight_retriever.schedule_reservations([{"confirmationNumber": flight['confirmation_number']}])


def schedule_user(config, user):
    flight_retriever = AccountFlightRetriever(config, user['username'], user['password'])
    flight_retriever.monitor_account()

def schedule_flights_from_config(config):
    processes = []
    if config.user_login:
        for user in config.user_login:
            process = Process(target=schedule_user, args=(config,user))
            process.start()
            processes.append(process)
    if config.flights:
        for flight in config.flights:
            process = Process(target=schedule_confirmation_number, args=(config, flight))
            process.start()
            processes.append(process)
    return processes


def run_auto_checkin():
    notification_handler = NotificationHandler(None, Config())
    pre_config = None
    processes = []
    while True:
        new_config = Config()
        if pre_config is None or pre_config != new_config:
            if pre_config is not None:
                notification_handler.send_notification("Received Updated Config... Rescheduling")
            for p in processes:
                p.terminate()
            processes = schedule_flights_from_config(new_config)
            time.sleep(new_config.config_update_interval*60*60)
            pre_config = new_config
        else:
            time.sleep(new_config.config_update_interval*60*60)


def set_up(arguments: List[str]):
    if len(arguments) > 0 and arguments[0] in ("-v", "--version"):
        print("Auto-Southwest Check-In " + __version__)
    elif len(arguments) > 0 and arguments[0] == "--test-notifications":
        flight_retriever = FlightRetriever(config=Config())

        print("Sending test notifications...")
        flight_retriever.notification_handler.send_notification("This is a test message")
    elif len(arguments) > 0:
        print("Invalid arguments")
        sys.exit()
    else:
        run_auto_checkin()
    # elif len(arguments) == 2:
    #     username = arguments[0]
    #     password = arguments[1]
    #
    #     flight_retriever = AccountFlightRetriever(username, password)
    #     flight_retriever.monitor_account()
    # elif len(arguments) == 3:
    #     confirmation_number = arguments[0]
    #     first_name = arguments[1]
    #     last_name = arguments[2]
    #
    #     flight_retriever = FlightRetriever(first_name, last_name)
    #     flight_retriever.checkin_scheduler.refresh_headers()
    #     flight_retriever.schedule_reservations([{"confirmationNumber": confirmation_number}])


if __name__ == "__main__":
    arguments = sys.argv[1:]

    try:
        set_up(arguments)
    except KeyboardInterrupt:
        print("\nCtrl+C pressed. Stopping all checkins")
        sys.exit()
