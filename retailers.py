# ---------------------
# Imports
# ---------------------

import json
import os
import pdb
import re
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions




# ---------------------
# Global Variables
# ---------------------

target_api_responses_filepath = "misc/Target/api_responses"
target_latest_api_response = None
target_consecutive_api_response_error_count = 0
target_max_consecutive_api_response_errors = 3
best_buy_crashed_page_sources_filepath = "misc/Best_Buy/crashed_page_sources"
best_buy_latest_page_source = None
walmart_filepath = "misc/Walmart"
walmart_crashed_page_sources_filepath = "misc/Walmart/crashed_page_sources"
walmart_latest_page_source = None
walmart_verify_editor_filename = "walmart_verify_editor.js"
walmart_max_wait_time_for_solved_captcha = 30 # seconds




# ---------------------
# Helper functions
# ---------------------

# A user exception that can be thrown manually if need to raise exception
class User_Exception(Exception):
    pass



# ---------------------
# Target functions
# ---------------------

# Initializes driver for Target
def init_target_driver(driver):
    # API fulfillment URLs
    fulfillment_api_url = "https://redsky.target.com/redsky_aggregations/v1/web/pdp_fulfillment_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=81114595&store_id=1768&store_positions_store_id=1768&has_store_positions_store_id=true&zip=52403&state=IA&latitude=41.980&longitude=-91.630&scheduled_delivery_store_id=1768&pricing_store_id=1768&has_pricing_store_id=true&is_bot=false"
    example_in_stock_fulfillment_api_url_1 = "https://redsky.target.com/redsky_aggregations/v1/web/pdp_fulfillment_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=83374957&store_id=1768&store_positions_store_id=1768&has_store_positions_store_id=true&zip=52403&state=IA&latitude=41.980&longitude=-91.630&scheduled_delivery_store_id=1768&pricing_store_id=1768&has_pricing_store_id=true&is_bot=false"
    example_in_stock_fulfillment_api_url_2 = "https://redsky.target.com/redsky_aggregations/v1/web/pdp_fulfillment_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=81114476&store_id=1768&store_positions_store_id=1768&has_store_positions_store_id=true&zip=52403&state=IA&latitude=41.980&longitude=-91.630&scheduled_delivery_store_id=1768&pricing_store_id=1768&has_pricing_store_id=true&is_bot=false"

    # Get API page to begin
    driver.get(fulfillment_api_url)
    # driver.get(example_in_stock_fulfillment_api_url_1)
    # driver.get(example_in_stock_fulfillment_api_url_2)

# Returns whether PS5s are in stock at Target
def in_stock_at_target(driver):
    # Import global variables
    global target_latest_api_response
    global target_consecutive_api_response_error_count
    global target_max_consecutive_api_response_errors

    # Query API whether PS5 is in stock
    driver.refresh()
    api_response = eval(driver.find_element_by_xpath("/html/body/pre").text.replace("true,", "True,").replace("false,", "False,"))
    target_latest_api_response = api_response
    if "errors" in api_response:
        target_consecutive_api_response_error_count += 1
        if target_consecutive_api_response_error_count >= target_max_consecutive_api_response_errors:
            raise User_Exception("Target API returned errors %s times in a row" % target_consecutive_api_response_error_count)
        availability_status = False
        quantity = 0
    else:
        target_consecutive_api_response_error_count = 0
        availability_status = api_response["data"]["product"]["fulfillment"]["shipping_options"]["availability_status"] != "OUT_OF_STOCK"
        quantity = int(api_response["data"]["product"]["fulfillment"]["shipping_options"]["available_to_promise_quantity"])

    # Return whether in stock at Target
    return {"in_stock": availability_status, "quantity": quantity}

# Handle exception when scraping Target
def handle_target_exception(error_message):
    # Todo: Comment out to debug
    # pdb.set_trace()

    # Import global variables
    global target_api_responses_filepath
    global target_latest_api_response

    # Store latest API response to look at later
    if target_latest_api_response:
        if not os.path.exists(target_api_responses_filepath):
            os.makedirs(target_api_responses_filepath)
        crash_api_response_filenames = [filename for filename in os.listdir(target_api_responses_filepath) if len(re.split("\.", filename)) > 1 and re.split("\.", filename)[-2][0:19] == "crash_api_response_"]
        crash_api_response_filenames.sort()
        if len(crash_api_response_filenames) > 0:
            # last_crash_num = int(re.split("\.", crash_api_response_filenames[-1])[0][-1]) # TODO: Fix. This should only work with single digit crash numbers.
            last_crash_num = int(re.split("_", re.split("\.", crash_api_response_filenames[-1])[0])[-1])
        else:
            last_crash_num = 0
        api_response_file = open("%s/crash_api_response_%s.json" % (target_api_responses_filepath, str(last_crash_num + 1).zfill(3)), "w+")
        for line in re.split("\n", error_message[:-1]):
            api_response_file.write("// %s\n" % line)
        api_response_file.write("\n")
        api_response_file.write(json.dumps(target_latest_api_response, indent=4))
        api_response_file.close()



# ---------------------
# Best Buy functions
# ---------------------

# Initializes driver for Best Buy
def init_best_buy_driver(driver):
    # Todo: Comment out to debug
    # pdb.set_trace()

    # PS5 page
    url = "https://www.bestbuy.com/site/sony-playstation-5-console/6426149.p?skuId=6426149"
    example_in_stock_url = "https://www.bestbuy.com/site/sony-playstation-5-dualsense-wireless-controller-white/6430163.p?skuId=6430163" # PS5 controller

    # Remove implicit wait from driver for Best Buy since want to explicitly wait for In Stock text instead and can't use implicit and explicit waits together.
    driver.implicitly_wait(0)

    # Get PS5 page to begin
    driver.get(url)
    # driver.get(example_in_stock_url)

    # Wait for user to set Best Buy location for scraper. TODO: Update this to be automatic.
    _ = input("\nUSER INPUT NEEDED: Update Best Buy site location to Cedar Rapids. Press 'Enter' to begin scraping.\n")

# Returns whether PS5s are in stock at Best Buy
def in_stock_at_best_buy(driver, add_to_cart_wait=10):
    # Todo: Comment out to debug
    # pdb.set_trace()

    # Import global variables
    global best_buy_latest_page_source

    # Refresh PS5 page
    driver.refresh()
    best_buy_latest_page_source = driver.page_source

    # TODO: Handle potential verification
    if "PlayStation 5" not in driver.title:
        # Todo: Comment out to debug
        # pdb.set_trace()

        # Raise exception if redirected from PS5 page for some reason (likely for bot verification)
        best_buy_latest_page_source = driver.page_source
        raise User_Exception("Best Buy redirected scraper to another page other than the PS5 page")

    # Check whether add to cart button is live. Give it time to load in the background since JS might update the button text after the HTML document is "ready".
    try:
        in_stock = WebDriverWait(driver, add_to_cart_wait).until(expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, "add-to-cart-button"), "Add to Cart"))
    except TimeoutException as e:
        in_stock = False

    # Return whether in stock at Best Buy
    return {"in_stock": in_stock, "quantity": 0}

# Handle exception when scraping Best Buy
def handle_best_buy_exception(error_message):
    # Todo: Comment out to debug
    # pdb.set_trace()

    # Import global variables
    global best_buy_crashed_page_sources_filepath
    global best_buy_latest_page_source

    # Store latest source code for Best Buy scraper crash to look at later
    if best_buy_latest_page_source:
        if not os.path.exists(best_buy_crashed_page_sources_filepath):
            os.makedirs(best_buy_crashed_page_sources_filepath)
        crashed_page_source_filenames = [filename for filename in os.listdir(best_buy_crashed_page_sources_filepath) if len(re.split("\.", filename)) > 1 and re.split("\.", filename)[-2][0:20] == "crashed_page_source_"]
        crashed_page_source_filenames.sort()
        if len(crashed_page_source_filenames) > 0:
            last_crash_num = int(re.split("_", re.split("\.", crashed_page_source_filenames[-1])[0])[-1])
        else:
            last_crash_num = 0
        crashed_page_source_file = open("%s/crashed_page_source_%s.html" % (best_buy_crashed_page_sources_filepath, str(last_crash_num + 1).zfill(3)), "w+", encoding="utf-8")
        crashed_page_source_file.write("<!--\n")
        for line in re.split("\n", error_message[:-1]):
            crashed_page_source_file.write("%s\n" % line)
        crashed_page_source_file.write("-->\n\n")
        crashed_page_source_file.write(best_buy_latest_page_source)
        crashed_page_source_file.close()



# ---------------------
# Walmart functions
# ---------------------

# Initializes driver for Walmart
def init_walmart_driver(driver):
    # Todo: Comment out to debug
    # pdb.set_trace()

    # PS5 page
    url = "https://www.walmart.com/ip/Sony-PlayStation-5/363472942"
    example_in_stock_url = "https://www.walmart.com/ip/PS5-DualSense-Wireless-Controller/615549727" # PS5 controller
    example_out_of_stock_url = "???" # ???

    # Get PS5 page to begin
    driver.get(url)
    # driver.get(example_in_stock_url)
    # driver.get(example_out_of_stock_url)

# Return Walmart verify editor script
def get_walmart_verify_editor_script():
    global walmart_verify_editor_filename
    verify_page_editor_file = open(walmart_verify_editor_filename, "r")
    verify_page_editor_script = verify_page_editor_file.read()
    verify_page_editor_file.close()
    return verify_page_editor_script

# Returns whether PS5s are in stock at Walmart
def in_stock_at_walmart(driver):
    # Todo: Comment out to debug
    # pdb.set_trace()

    # Import global variables
    global walmart_max_wait_time_for_solved_captcha
    global walmart_latest_page_source

    # Refresh PS5 page
    driver.refresh()
    walmart_latest_page_source = driver.page_source

    # Handle potential verification
    if "PlayStation 5" not in driver.title:
        # Todo: Comment out to debug
        # pdb.set_trace()

        # CLICK AND HOLD CAPTCHA BUTTON BY SCREEN LOCATION
        # Initialize variables
        action_chains = ActionChains(driver)
        captcha_obj = driver.find_element_by_id("px-captcha")
        captcha_obj_div = captcha_obj.find_element_by_tag_name("div")

        # Navigate mouse to where center of captcha button should be
        # action_chains.move_by_offset(0, 0).perform() # Todo: Determine correct mouse position
        # Navigate to captcha button
        random_x_offset = random.uniform(0, 20)
        random_y_offset = random.uniform(0, 20)
        action_chains.move_to_element(captcha_obj_div).move_by_offset(random_x_offset, random_y_offset).perform()
        time.sleep(0.5)

        # Click and hold captcha button
        action_chains.click_and_hold().perform()

        # Wait for ??? seconds (roughly the amount of time it takes to solve the captcha)
        time.sleep(10) # Todo: Determine correct wait time

        # Release click
        action_chains.release().perform()


        # CLICK AND HOLD CAPTCHA BUTTON BY GETTING BUTTON IN HTML
        # # Modify source code to allow Selenium to be able to see iframe elements
        # stripped_iframes = driver.find_elements_by_tag_name("iframe")
        # correct_iframe_num = 0
        # for iframe in stripped_iframes:
        #     if iframe != {}:
        #         break
        #     correct_iframe_num += 1
        # driver.execute_script(get_walmart_verify_editor_script(), correct_iframe_num)

        # # Find iframe containing captcha button
        # iframes = driver.find_elements_by_tag_name("iframe")
        # for iframe in iframes:
        #     if len(iframe.get_attribute("style")) > 100:
        #         correct_iframe = iframe
        #         break
        # driver.switch_to.frame(correct_iframe)

        # # Click and hold captcha button
        # # ...

        # # Wait until width style reaches a certain amount
        # # ...

        # # Release click and reset current content
        # # ...
        # driver.switch_to.default_content()

        # Wait until page redirects to PS5 page
        time_waited = 0
        while "PlayStation 5" not in driver.title and time_waited < walmart_max_wait_time_for_solved_captcha:
            time.sleep(1)
            time_waited += 1

        # Try one last time to get to PS5 page
        if "PlayStation 5" not in driver.title:
            init_walmart_driver(driver)

        # If still on verify page, raise exception
        if "PlayStation 5" not in driver.title:
            walmart_latest_page_source = driver.page_source
            raise User_Exception("Failed to defeat verify page captcha")

    # Get price of PS5
    ps5_price_object = driver.find_element_by_class_name("price-characteristic")
    ps5_price_object_text = ps5_price_object.text.replace(",", "")
    if ps5_price_object_text.isnumeric():
        ps5_price = int(ps5_price_object_text)
    else:
        # Should only hit here if price object doesn't contain a number for whatever reason. Perhaps because the PS5 is out of stock.
        return {"in_stock": False, "quantity": 0}

    # Get add to cart button text
    add_to_cart_button = driver.find_element_by_id("add-on-atc-container").find_elements_by_class_name("button-wrapper")[0]
    add_to_cart_text = add_to_cart_button.text

    # Check whether price is the MSRP or the reseller price and also whether add to cart button is live
    if ps5_price < 550 and "add to cart" in add_to_cart_text.lower():
        in_stock = True
    else:
        in_stock = False

    # Return whether in stock at Walmart
    return {"in_stock": in_stock, "quantity": 0}

# Handle exception when scraping Walmart
def handle_walmart_exception(error_message):
    # Import global variables
    global walmart_crashed_page_sources_filepath
    global walmart_latest_page_source

    # Store latest page source for Walmart scraper crash to look at later
    if walmart_latest_page_source:
        if not os.path.exists(walmart_crashed_page_sources_filepath):
            os.makedirs(walmart_crashed_page_sources_filepath)
        crashed_page_source_filenames = [filename for filename in os.listdir(walmart_crashed_page_sources_filepath) if len(re.split("\.", filename)) > 1 and re.split("\.", filename)[-2][0:20] == "crashed_page_source_"]
        crashed_page_source_filenames.sort()
        if len(crashed_page_source_filenames) > 0:
            last_crash_num = int(re.split("_", re.split("\.", crashed_page_source_filenames[-1])[0])[-1])
        else:
            last_crash_num = 0
        crashed_page_source_file = open("%s/crashed_page_source_%s.html" % (walmart_crashed_page_sources_filepath, str(last_crash_num + 1).zfill(3)), "w+", encoding="utf-8")
        crashed_page_source_file.write("<!--\n")
        for line in re.split("\n", error_message[:-1]):
            crashed_page_source_file.write("// %s\n" % line)
        crashed_page_source_file.write("-->\n\n")
        crashed_page_source_file.write(walmart_latest_page_source)
        crashed_page_source_file.close()





# ---------------------
# Retailer info
# ---------------------

retailer_info = {"target":   {"name": "Target",
                              "initializer": init_target_driver,
                              "scraper": in_stock_at_target,
                              "exception_handler": handle_target_exception,
                              "properties": {"headless": True,
                                             "delay": 6,
                                             "delay_delta": 2},
                              },
                 "best_buy": {"name": "Best Buy",
                              "initializer": init_best_buy_driver,
                              "scraper": in_stock_at_best_buy,
                              "exception_handler": handle_best_buy_exception,
                              "properties": {"headless": False,
                                             "delay": 6,
                                             "delay_delta": 2},
                              "add_to_cart_wait": 10,
                              },
                 "walmart":  {"name": "Walmart",
                              "initializer": init_walmart_driver,
                              "scraper": in_stock_at_walmart,
                              "exception_handler": handle_walmart_exception,
                              "properties": {"headless": True,
                                             "delay": 7,
                                             "delay_delta": 3},
                              }
                }
