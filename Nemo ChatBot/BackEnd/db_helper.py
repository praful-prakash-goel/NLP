import mysql.connector
global db_config

# Database connection configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '10200709',
    'database': 'pandeyji_eatery'
}

def get_order_status(order_id: int):
    try:
        # Establish the connection to the database
        connection = mysql.connector.connect(**db_config)

        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        # Define the SQL query to fetch the status for the given order_id
        query = "SELECT status FROM order_tracking WHERE order_id = %s"

        # Execute the query with the provided order_id
        cursor.execute(query, (order_id,))

        # Fetch the result
        result = cursor.fetchone()

        # Check if the order_id exists in the table
        if result:
            # Extract and return the status from the result
            status = result[0]
            return f"The status of order {order_id} is: {status}"
        else:
            return f"No order found with order_id: {order_id}"

    except mysql.connector.Error as err:
        return f"Error: {err}"

    finally:
        # Close the cursor and the connection
        if cursor:
            cursor.close()

def get_next_order_id():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "SELECT MAX(order_id) FROM orders"
        cursor.execute(query)

        result = cursor.fetchone()[0]

        if result is None:
            return 1
        else:
            return result+1
        
    except mysql.connector.Error as err:
        return f"Error: {err}"
    
    finally:
        if cursor:
            cursor.close()

def insert_order_item(item, quantity, order_id):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Calling the stored procedure
        cursor.callproc('insert_order_item', (item, quantity, order_id))

        connection.commit()
        print("Order inserted successfully!")
        return 1
    
    except mysql.connector.Error as err:
        print(f"Error in inserting order : {err}")
        connection.rollback()
        return -1
    
    except Exception as e:
        print(f"An error occured : {err}")
        connection.rollback()
        return -1
    
    finally:
        if cursor:
            cursor.close()

def get_order_total(order_id):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "SELECT get_total_order_price(%s)"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()[0]

        return result
    except mysql.connector.Error as err:
        return f"Error : {err}"
    finally:
        if cursor:
            cursor.close()

def insert_order_tracking(order_id, status):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
        cursor.execute(query, (order_id, status))
        connection.commit()
    except mysql.connector.Error as err:
        return f"Error : {err}"
    finally:
        if cursor:
            cursor.close()
