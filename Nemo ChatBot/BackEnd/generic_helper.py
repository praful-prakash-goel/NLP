import re

def extract_session_id(session_str : str):
    match = re.search(pattern=r'sessions/(.*)', string=session_str)
    if match:
        session_id = match.group(1)
        return session_id
    return ""

def get_order_summary(myDict : dict):
    order_summary = []
    for item, quantity in myDict.items():
        try:
            quantity = int(quantity)  # Ensure quantity is an integer
            order_summary.append(f"{quantity} {item}")
        except ValueError:
            return {"fulfillmentText": "Invalid quantity provided. Please provide a valid number."}

    order_summary = ', '.join(order_summary)
    return order_summary