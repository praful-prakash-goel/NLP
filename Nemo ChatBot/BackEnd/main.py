from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn
import random
import db_helper
import generic_helper

app = FastAPI()
inprogress_order = {}

# Define a Pydantic model for webhook request
class WebhookRequest(BaseModel):
    queryResult: dict
    session: str

# Define individual intent handlers

def handle_new_order(parameters: dict, session_id: str):
    if session_id in inprogress_order:
        del inprogress_order[session_id]
    else:
        pass

def handle_order_add(parameters: dict, session_id: str):
    # Process order.add intent
    items = parameters.get("food-items", [])
    quantities = parameters.get("number", [])

    # Ensure items and quantities are non-empty lists
    if not items or not quantities:
        return {"fulfillmentText": "Could not process your order. Please specify the item and quantity."}

    # Ensure that the number of items matches the number of quantities
    if len(items) != len(quantities):
        return {"fulfillmentText": "The number of items and quantities do not match."}
    
    response_templates = [
        "Added {order_summary} to your order. Anything else?",
        "You have successfully added {order_summary} to your cart. Anything else?",
        "Great choice! {order_summary} has been added to your order. Anything else?",
        "Your order now includes {order_summary}. Anything else?",
        "Thank you for adding {order_summary} to your cart. Anything else?"
    ]

    # Add new order to corresponding session id
    new_order_dict = dict(zip(items, quantities))
    if session_id in inprogress_order:
        current_dict = inprogress_order[session_id]
        for item, quantity in new_order_dict.items():
            if item not in current_dict:
                current_dict[item] = quantity
            else:
                current_dict[item] += quantity
        inprogress_order[session_id] = current_dict
    else:
        inprogress_order[session_id] = new_order_dict
        
    # Prepare the order summary
    order_summary = generic_helper.get_order_summary(inprogress_order[session_id])
    
    # Return the order summary
    response = random.choice(response_templates)
    return {
        "fulfillmentText": response.format(order_summary=order_summary)
    }


# Process order.remove intent
def handle_order_remove(parameters: dict, session_id: str):
    # Process order.remove intent
    items = parameters.get("food-items", [])
    quantities = parameters.get("number", [])

    # Ensure items and quantities are non-empty lists
    if not items or not quantities:
        return {"fulfillmentText": "Could not process your order. Please specify the item and quantity."}

    # Ensure that the number of items matches the number of quantities
    if len(items) != len(quantities):
        return {"fulfillmentText": "The number of items and quantities do not match."}
    
    if session_id not in inprogress_order:
        return {"fulfillmentText": "No active order found for this session"}

    removal_dict = dict(zip(items, quantities))
    current_dict = inprogress_order[session_id]
    for item,quantity in removal_dict.items():
        if(current_dict[item] and current_dict[item] >= quantity):
            current_dict[item] -= quantity
            if current_dict[item] <= 0:
                del current_dict[item]
            inprogress_order[session_id] = current_dict
        else:
            return {
                "fulfillmentText": f"{int(quantity)} {item} is not present in your current order."
            }
    
    order_summary = generic_helper.get_order_summary(inprogress_order[session_id])
    itemList = generic_helper.get_order_summary(removal_dict)
    if items:
        return {
            "fulfillmentText": f"Removed {itemList} from your order. Now your order includes {order_summary}"
        }
    
def handle_track_order(parameters: dict, session_id: str):
    # Process track.order intent
    order_id = int(parameters.get("number"))
    status = db_helper.get_order_status(order_id)

    if not order_id:
        return {
            "fulfillmentText": "Please provide an order ID to track."
        }
    
    if status:
        return {
            "fulfillmentText": status
        }
    else:
        return {
            "fulfillmentText": f"No order found with order ID {order_id}."
        }
    
def handle_order_complete(parameters: dict, session_id: str):
    if session_id not in inprogress_order:
        return {"fulfillmentText": "No active order found for current session"}
    else:
        order = inprogress_order[session_id]
        order_id = save_to_db(order)
        
        random_response = [
            "Awesome! Your order is placed successfully! Here is your order id # {order_id}.",
            "Great! Order placed! Here is your order id # {order_id}.",
            "Ok! Order is placed! Here is your order id # {order_id}.",
            "Awesome! Order placed! Here is your order id # {order_id}."
        ]
        if order_id == -1:
            return {"fulfillmentText": "Sorry! I could not place your order. Please try again."}
        else:
            response = random.choice(random_response)
            response = response.format(order_id=order_id)
            order_total = db_helper.get_order_total(order_id)
            del inprogress_order[session_id]
            return {"fulfillmentText": f"{response} Your order total is {order_total} which you can pay at the time of delivery"}

def save_to_db(order: dict):
    next_order_id = db_helper.get_next_order_id()

    for item, quantity in order.items():
        rcode = db_helper.insert_order_item(item, quantity, next_order_id)

        if rcode == -1:
            return -1
    
    db_helper.insert_order_tracking(next_order_id, "in progress")
    return next_order_id

def handle_store_hours(parameters: dict, session_id: str):
    str = """Sure! The store hours are as follows:

    1. Monday: 10 A.M to 10 P.M
    2. Tuesday: 10 A.M to 10 P.M
    3. Wednesday: 10 A.M to 10 P.M
    4. Thursday: 10 A.M to 10 P.M
    5. Friday: 10 A.M to 10 P.M
    6. Saturday: 11 A.M to 11 P.M
    7. Sunday: 11 A.M to 11 P.M

    Let us know if you need further details!"""

    return {
        "fulfillmentText": str
    }



@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        # Parse the incoming JSON payload
        body = await request.json()

        # Extract intent name, parameters, and session ID
        intent = body["queryResult"]["intent"]["displayName"]
        parameters = body["queryResult"]["parameters"]
        session_id = generic_helper.extract_session_id(str(body["session"]))

        # Route the request to the appropriate handler
        intent_handler_dict = {
            "new.order": handle_new_order,
            "order.add - context: ongoing order": handle_order_add,
            "order.remove - context: ongoing order": handle_order_remove,
            "order.complete - context: ongoing-order": handle_order_complete,
            "track.order - context: ongoing-tracking": handle_track_order,
            "store.hours": handle_store_hours
        }
        return intent_handler_dict[intent](parameters=parameters, session_id=session_id)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
