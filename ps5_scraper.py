# TODOs:
# 1.) DONE: SNS notifier instead of IFTTT. IFTTT notifications are not reliable (many don't seem to pop up until phone is unlocked).
# 2.) TODO: Figure out how to bypass Walmart captcha verification page
# 3.) DONE: Add a consecutive crash counter to kill scraper if it crashes enough times consecutively (so as to not accidentally spam myself with notifications if I don't catch it right away)
# 4.) TODO: Add image verification for Walmart captcha since click and hold has variable length needed to hold.
# 5.) TODO: Add proper HTTP headers to Selenium driver gets to look more human
# 6.) TODO: Change Target scraper to save page source and not last API response
# 7.) DONE: Change Target scraper to handle known permutations to API response instead of crashing
# 8.) TODO: Automate selecting Cedar Rapids as Best Buy site location
# 9.) TODO: Handle Target API key expiring
# 10.) TODO: Fix Target scraping to select correct store in API results


# ---------------------
# Imports
# ---------------------

import boto3
from datetime import datetime
import json
import math
import pdb
import random
from retailers import *
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchWindowException
import sys
import time
import traceback


# ---------------------
# Global Variables
# ---------------------

# Extract input parameters
if len(sys.argv) < 2:
    print("ERROR: Missing retailer to scrape. Options are %s." % (list(retailer_info.keys())))
    quit()
retailer = sys.argv[1].lower()
if retailer not in retailer_info:
    print("ERROR: Not a valid retailer. Options are %s." % (list(retailer_info.keys())))
    quit()
max_iterations = math.inf if len(sys.argv) < 3 else int(sys.argv[2])

# Initialize variables
print_is_on = True
notifications_are_on = False
divider = "-" * 50
delay = retailer_info[retailer]["properties"]["delay"]
delay_delta = retailer_info[retailer]["properties"]["delay_delta"]
found_ps5_delay = 60 * 5 # seconds
iteration_num = 1
stop_on_crash = False
webscraper_crashed_delay = 60 * 5 # seconds
consecutive_crash_counter = 0
max_consecutive_crashes = 3 # Stop scraper if reach this many consecutive crashes


# ---------------------
# Helper functions
# ---------------------

# Send push notification through IFTTT
def send_push_notification(message):
    ifttt_key = "XXXXXXXXXXXXXXXXXXXXXX" # Todo: Locally add back for testing
    ifttt_webhook_url = "https://maker.ifttt.com/trigger/send_notification/with/key/" + ifttt_key
    json_data = {"value1": message}
    requests.post(ifttt_webhook_url, json=json_data) # Send push notification

# Send SMS through AWS SNS topic
def send_sms(message):
    ps5_notifier_arn = "arn:aws:sns:XXXXXXXXX:XXXXXXXXXXXX:PS5_Notifier" # Todo: Locally add back for testing
    aws_access_key_id = "XXXXXXXXXXXXXXXXXXXX" # Todo: Locally add back for testing
    aws_secret_key = "XXXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXX" # Todo: Locally add back for testing
    sns_client = boto3.client("sns",
        region_name="XXXXXXXXX", # Todo: Locally add back for testing
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_key)
    sns_response = sns_client.publish(TopicArn=ps5_notifier_arn, Message=message)
    
    # Can print out response for debugging
    # print(json.dumps(sns_response, indent=4))

# Initialize Chrome driver
def init_driver():
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    options = webdriver.ChromeOptions()
    options.headless = retailer_info[retailer]["properties"]["headless"]
    # options.add_argument("--disable-web-security") # TODO: Is this needed for Walmart scraping?
    # options.add_argument("--allow-running-insecure-content")
    options.add_argument("user-agent=%s" % user_agent)
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(30) # Wait this long (in seconds) when searching for desired objects on page
    return driver



# ---------------------
# Webscraper
# ---------------------

# Initialize webdriver
driver = init_driver()

# Initialize retailer scraper
retailer_info[retailer]["initializer"](driver)

# Continue scraping until manually terminated
while True:
    # Handle crashes gracefully
    try:
    
        # Get whether PS5s are in stock at the selected store
        if "add_to_cart_wait" in retailer_info[retailer]:
            in_stock_dict = retailer_info[retailer]["scraper"](driver, retailer_info[retailer]["add_to_cart_wait"])
        else:
            in_stock_dict = retailer_info[retailer]["scraper"](driver)
        in_stock = in_stock_dict["in_stock"]
        quantity = in_stock_dict["quantity"]

        # If PS5 is in stock, send notification
        if in_stock:
            # Set notification message
            if quantity > 0:
                if quantity == 1:
                    notification_message = "%s has 1 PS5 currently available" % retailer_info[retailer]["name"]
                else:
                    notification_message = "%s has %s PS5s currently available" % (retailer_info[retailer]["name"], quantity)
            else:
                notification_message = "%s has PS5s currently available" % retailer_info[retailer]["name"]

            # Send notification
            if notifications_are_on:
                send_sms(notification_message)
            if print_is_on:
                print(divider + "\n" + notification_message + "\n" + divider)

            # Update delay to amount to wait when find PS5s
            delay = found_ps5_delay
        
        # Otherwise restore initial delay for scraping
        else:
            delay = retailer_info[retailer]["properties"]["delay"]

        # Check to see if reached max amount of iterations
        if iteration_num >= max_iterations:
            break
        else:
            iteration_num += 1

        # Todo: Comment out. For testing exception-handling.
        # if iteration_num % 5 == 0:
        #     x = 1 / 0

        # Wait before querying API again
        random_delay = random.uniform(delay - delay_delta, delay + delay_delta)
        if print_is_on:
            print("Waiting %s seconds..." % random_delay)
        time.sleep(random_delay)

        # Reset consecutive crash counter
        consecutive_crash_counter = 0
            
    # Catch all exceptions
    except Exception as e:
        # Initialize exception variables
        notification_message = "%s PS5 webscraper crashed:\n" % retailer_info[retailer]["name"]
        error_lines = traceback.format_exception(type(e), e, sys.exc_info()[2])
        for line in error_lines:
            notification_message += line

        # Send notification of the exception
        if notifications_are_on:
            send_sms(notification_message)

        # TODO: Remove after debug/fix Best Buy NoSuchWindowException's
        # if type(e) == NoSuchWindowException:
        #     pdb.set_trace()
        # else:
        #     print("type(e): %s" % type(e))

        # Call retailer exception handler
        retailer_info[retailer]["exception_handler"](notification_message)

        # Increment consecutive crash counter and check whether reached max consecutive crashes
        consecutive_crash_counter += 1
        if consecutive_crash_counter >= max_consecutive_crashes:
            consecutive_crash_error_message = "Reached max number of consecutive of crashes (%s). Stopping %s scraper..." % (max_consecutive_crashes, retailer_info[retailer]["name"])
            if notifications_are_on:
                send_sms(consecutive_crash_error_message)
            print((divider * 2) + "\n" + consecutive_crash_error_message + "\n" + (divider * 2))
            stop_on_crash = True

        # Either crash or print out error and continue scraping
        if stop_on_crash:
            raise
        else:
            print(divider + "\n" + notification_message + divider)
            if print_is_on:
                print("Waiting %s seconds..." % webscraper_crashed_delay)
            time.sleep(webscraper_crashed_delay)
