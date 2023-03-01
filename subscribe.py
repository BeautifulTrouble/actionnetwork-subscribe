#!/usr/bin/env python

import csv
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


SIGN_UPS = "1ZWkAEca3GR7gwKazT3F_8iEK6fSgoSf8gEHCp5_B0Ug"
SIGN_UPS_COMPLETED = "sign_ups.json"
SIGN_UPS_TAG = "Sign Ups"

TRAINING_REQ = "1Nl7NbQ-x4VkisH4wTniv9GMP0F35r_1SFXlayhqixMo"
TRAINING_REQ_COMPLETED = "training_req.json"
TRAINING_REQ_TAG = "Training Req"

CREDENTIALS = "beautifultrouble-2093eac4dc47.json"
API_POLITENESS = 0.1


def post_person(data: dict) -> bool:
    r = requests.post(
        "https://actionnetwork.org/api/v2/people/",
        headers={"Content-Type": "application/json", "OSDI-API-Token": API_KEY},
        json=data,
    )
    if r.status_code != 200:
        logging.warning(f"Failed to add: {data}")
        return False
    logging.info(f"Added: {data}")
    return True


logging.basicConfig(level="INFO")

drive = driveclient.DriveClient(
    "actionnetwork",
    scopes="https://www.googleapis.com/auth/drive",
    service_account_json_filename=CREDENTIALS,
)


# Email list squarespace signups
reader = drive.get(SIGN_UPS).csv
next(reader)

with open(SIGN_UPS_COMPLETED, "a+") as file:
    file.seek(0)
    try:
        completed = set(json.load(file))
    except json.JSONDecodeError:
        logging.warning("Completion cache is empty. Adding ALL entries...")
        completed = set()
    for timestamp, email, *_ in reader:
        if email not in completed:
            if post_person(
                {
                    "person": {
                        "email_addresses": [{"address": email}],
                    },
                    "add_tags": [SIGN_UPS_TAG],
                }
            ):
                completed.add(email)
            time.sleep(API_POLITENESS)

with open(SIGN_UPS_COMPLETED, "w") as file:
    json.dump(list(completed), file)


# Training request form
file = drive.get(TRAINING_REQ)
lines = file.data_of_type("text/csv", "utf-8-sig").splitlines()[1:]
reader = csv.DictReader(lines)

with open(TRAINING_REQ_COMPLETED, "a+") as file:
    file.seek(0)
    try:
        completed = set(json.load(file))
    except json.JSONDecodeError:
        logging.warning("Completion cache is empty. Adding ALL entries...")
        completed = set()
    for row in reader:
        g = lambda k: row.get(k, "")
        timestamp = g("timestamp")
        firstname = g("firstname")
        lastname = g("lastname")
        email = g("email")
        organization = g("organization")
        if timestamp and timestamp not in completed:
            data = {
                "person": {
                    "family_name": lastname,
                    "given_name": firstname,
                    "email_addresses": [{"address": email}],
                },
                "add_tags": [TRAINING_REQ_TAG, SIGN_UPS_TAG],
            }
            if organization:
                data["person"]["custom_fields"] = {"organization": organization}
            if post_person(data):
                completed.add(timestamp)
            time.sleep(API_POLITENESS)
