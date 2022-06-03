#!/usr/bin/env python

import json
import logging
import time

# Fix broken driveclient dependency
time.clock = time.time

import driveclient
import requests

# Fix broken driveclient dependency
from oauth2client import file as _

from action_network import API_KEY


SUBSCRIBER_LIST = "Beautiful Trouble BT Sign Ups Promotional PopUp"
SUBSCRIBER_CACHE = "subscribed.json"
CREDENTIALS = "beautifultrouble-2093eac4dc47.json"
API_POLITENESS = 0.1


def subscribe_user(email: str) -> bool:
    r = requests.post(
        "https://actionnetwork.org/api/v2/people/",
        headers={"Content-Type": "application/json", "OSDI-API-Token": API_KEY},
        json={"person": {"email_addresses": [{"address": email}]}},
    )
    if r.status_code != 200:
        logging.warning(f"Failed to add: {email}")
        return False
    logging.info(f"Added: {email}")
    return True


logging.basicConfig(level="INFO")

drive = driveclient.DriveClient(
    "actionnetwork",
    scopes="https://www.googleapis.com/auth/drive",
    service_account_json_filename=CREDENTIALS,
)
reader = drive.file(SUBSCRIBER_LIST).csv
next(reader)

with open(SUBSCRIBER_CACHE, "a+") as file:
    file.seek(0)
    try:
        subscribed = set(json.load(file))
    except json.JSONDecodeError:
        logging.warning("Subscriber cache is empty. Adding ALL email addresses.")
        subscribed = set()
    for timestamp, email, *_ in reader:
        if email not in subscribed:
            if subscribe_user(email):
                subscribed.add(email)
            time.sleep(API_POLITENESS)

with open(SUBSCRIBER_CACHE, "w") as file:
    json.dump(list(subscribed), file)
