#!/usr/bin/env python

import csv
import json
import logging
import time
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta

# Fix broken driveclient dependency
time.clock = time.time

import driveclient
import requests

# Fix broken driveclient dependency
from oauth2client import file as _

from action_network import API_KEY as API_KEY_ACTIONNETWORK
from squarespace import API_KEY as API_KEY_SQUARESPACE


ORDERS_INTERVAL_HOURS = 2
ORDERS_COMPLETED = "ss_orders.json"
ORDERS_TAG = "Merch Buyers"

SIGN_UPS_FOOTER = "1MJ3d7Tp4lEm26d6LLiQY0iHapiI1xuX2UwYuLXp93Gk"
SIGN_UPS_POPUP = "1ZPrX5DifbrKkoIKI0xOpg10dWFkCc5xO15RQ-iHvqSs"
SIGN_UPS_COMPLETED = "sign_ups.json"
SIGN_UPS_TAG = "Sign Ups"

TRAINING_REQ = "1Nl7NbQ-x4VkisH4wTniv9GMP0F35r_1SFXlayhqixMo"
TRAINING_REQ_COMPLETED = "training_req.json"
TRAINING_REQ_TAG = "Training"

CREDENTIALS = "beautifultrouble-2093eac4dc47.json"
API_POLITENESS = 0.2


@contextmanager
def task(name):
    logging.info(f"Running task '{name}'")
    try:
        yield
    except:
        traceback.print_exc()
        logging.error(f"Failure during task '{name}'")


def post_person(data: dict) -> bool:
    r = requests.post(
        "https://actionnetwork.org/api/v2/people/",
        headers={
            "Content-Type": "application/json",
            "OSDI-API-Token": API_KEY_ACTIONNETWORK,
        },
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


# ------------------------------------------------------------------------------------------------


with task("Add squarespace order emails to AN"):
    with open(ORDERS_COMPLETED, "a+") as file:
        file.seek(0)
        try:
            completed = set(json.load(file))
        except json.JSONDecodeError:
            logging.warning("Completion cache is empty. Adding ALL entries...")
            completed = set()

        iso8601 = lambda t: f"{t.isoformat(timespec='seconds')}Z"
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=ORDERS_INTERVAL_HOURS)
        qs = f"?modifiedAfter={iso8601(start_time)}&modifiedBefore={iso8601(end_time)}"

        while True:
            j = requests.get(
                f"https://api.squarespace.com/1.0/commerce/orders{qs}",
                headers={
                    "User-Agent": "Friendly e-commerce data collection bot",
                    "Authorization": f"Bearer {API_KEY_SQUARESPACE}",
                },
            ).json()
            orders = j["result"]
            pagination = j["pagination"]

            for order in orders:
                email = order.get("customerEmail")
                firstname = order.get("billingAddress", {}).get("firstName", "")
                lastname = order.get("billingAddress", {}).get("lastName", "")
                if email and email not in completed:
                    data = {
                        "person": {
                            "family_name": lastname,
                            "given_name": firstname,
                            "email_addresses": [{"address": email}],
                        },
                        "add_tags": [SIGN_UPS_TAG, ORDERS_TAG],
                    }
                    if post_person(data):
                        completed.add(email)
                    time.sleep(API_POLITENESS)

            if not (cursor := pagination["nextPageCursor"]):
                break
            qs = f"?cursor={cursor}"

    with open(ORDERS_COMPLETED, "w") as file:
        json.dump(list(completed), file)

# ------------------------------------------------------------------------------------------------


with task("Add squarespace signups to AN"):
    for file in [SIGN_UPS_FOOTER, SIGN_UPS_POPUP]:
        reader = drive.get(file).csv
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


# ------------------------------------------------------------------------------------------------


with task("Add training request emails to AN"):
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

    with open(TRAINING_REQ_COMPLETED, "w") as file:
        json.dump(list(completed), file)
