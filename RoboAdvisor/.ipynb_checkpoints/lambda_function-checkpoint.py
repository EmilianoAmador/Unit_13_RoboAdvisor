### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta
#from botocore.vendored import requests
#! pip install requests
#import requests
import json
import urllib3
http = urllib3.PoolManager()





### Helper Functions For Functionality  ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }
    
def validate_data(age, investment_Amount, intent_request):
    """
    Validates the data (age, investment amount, or intent request) provided by the user. 
    """

    # Validate that the user is older than zero and less than 65
    if age is not None:
        age = parse_int(age)
        if age < 0:
            return build_validation_result(
                False,
                "age",
                "You should be at least born to use this service. "
                "please come back at a later date.",
            )
    if age is not None:
        age = parse_int(age)
        if age > 64:
            return build_validation_result(
                False,
                "age",
                "Sorry! Must be less than 65 to use this service.",
            )
    
        # Validate the investment amount, it should be >= 5000
    if investment_Amount is not None:
        investment_Amount = parse_int(investment_Amount) 
        # Since parameters are strings it's important to cast values
        if investment_Amount < 5000:
            return build_validation_result(
                False,
                "investmentAmount",
                "A $5000 minimum amount is required to invest. "
                "please provide a correct amount in USD to continue.",
            )

    # If age or amount are valid. A True results is returned 
    return build_validation_result(True, None, None)

investment_Recommendation = {"None": "100% bonds (AGG), 0% equities (SPY)",
                              "Very Low": "80% bonds (AGG), 20% equities (SPY)",
                              "Low": "60% bonds (AGG), 40% equities (SPY)",
                              "Medium": "40% bonds (AGG), 60% equities (SPY)",
                              "High": "20% bonds (AGG), 80% equities (SPY)",
                              "Very High": "0% bonds (AGG), 100% equities (SPY)",}
                                 
def recommendation_Function(risk_level):
    return investment_Recommendation[risk_level]






### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response









### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_Amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]

    if source == "DialogCodeHook":
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt
        # for the first violation detected.

        slots = get_slots(intent_request)
         # Validates user's input using the validate_data function
        validation_result = validate_data(age, investment_Amount, intent_request)
        
                # If the data provided by the user is not valid,
        # the elicitSlot dialog action is used to re-prompt for the first violation detected.
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None  # Cleans invalid slot

                    # Returns an elicitSlot dialog to request new data for the invalid slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )

        # Fetch current session attibutes
        output_session_attributes = intent_request["sessionAttributes"]

        return delegate(output_session_attributes, get_slots(intent_request))

    # Get the initial investment recommendation
    
    initial_recommendation = recommendation_Function(risk_level)


    # Return a message with the initial recommendation based on the risk level.
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """{}, thank you for your information;
            based on the risk level you defined, my recommendation is to choose an investment portfolio with {}
            """.format(
                first_name, initial_recommendation
            ),
        },
    )








### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "RecommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)