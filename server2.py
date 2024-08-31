import socket
import sqlite3
import time
from decimal import Decimal
import re
import os
import threading
import secrets

# Global variables
server_port = 8100
data_file = "stocks.db"
is_running = True
sessions = {}

def make_db():
    """Create initial database structure if it doesn't exist, and insert default users."""
    db_conn = sqlite3.connect(data_file)
    cursor = db_conn.cursor()

    # Create Users table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            user_name TEXT NOT NULL,
            password TEXT,
            usd_balance DOUBLE NOT NULL
        )
    """)

    # Create Stocks table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Stocks (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_symbol VARCHAR(4) NOT NULL,
            stock_name VARCHAR(20) NOT NULL,
            stock_balance DOUBLE,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES Users (ID)
        )
    """)
    
    # Insert default users if none exist
    cursor.execute("""
        INSERT INTO Users (first_name, last_name, user_name, password, usd_balance)
        VALUES ('John', 'Doe', 'John', 'John01', 100.0)
    """)
    cursor.execute("""
        INSERT INTO Users (first_name, last_name, user_name, password, usd_balance)
        VALUES ('Root', 'User', 'Root', 'Root01', 100.0)
    """)
    
    db_conn.commit()
    db_conn.close()

def check_db():
    """Check if the database has any users, if not, adds a default user."""
    db_conn = sqlite3.connect(data_file)
    cursor = db_conn.cursor()

    # Check if any users exist in the database
    cursor.execute("SELECT COUNT (*) FROM Users")
    user_count = cursor.fetchone()[0]

    # Insert a default user if no users found
    if user_count == 0:
        cursor.execute("""
            INSERT INTO Users (first_name, last_name, user_name, password, usd_balance)
            VALUES ('user', 'one, 'username', 'password', 100.0)
        """)
        db_conn.commit()
    db_conn.close()

def list_command(user_id):
    """Handle the LIST command, retrieve stocks for a user."""
    db_conn = sqlite3.connect(data_file)
    cursor = db_conn.cursor()

    if user_id == 2:
        # Retrieve all records when user_id is 2, including user_name
        cursor.execute("""
            SELECT Stocks.ID, Stocks.stock_symbol, Stocks.stock_name, Stocks.stock_balance, Users.user_name
            FROM Stocks
            JOIN Users ON Stocks.user_id = Users.ID
            """)
    else:
        # Retrieve records only for the specified user_id
        cursor.execute("""
            SELECT Stocks.ID, Stocks.stock_symbol, Stocks.stock_name, Stocks.stock_balance
            FROM Stocks
            WHERE Stocks.user_id = ?
            """, (user_id,))

    data = cursor.fetchall()

    # Prepare response with fetched data
    response = ""
    if data:
        if user_id == 2:
            response += f"   The list of all records in the Stocks database:\n"
        else:
            response += f"   The list of records in the Stocks database for user {user_id}\n"
        for idx, stock in enumerate(data, 1):
            if user_id == 2:
                response += f"   {idx} {stock[1]} {stock[3]} {stock[4]}\n"
            else:
                response += f"   {idx} {stock[1]} {stock[2]} {stock[3]}\n"
    else:
        response = "Err"
    
    db_conn.close()
    return response

def buy_command(command, user_id):
    """Handle the BUY command, buy stocks for a user."""
    db_conn = sqlite3.connect(data_file)
    cursor = db_conn.cursor()

    # Split the command into respective parts
    elements = command.split(" ")
    symbol = elements[1]
    quantity = int(elements[2])
    price = float(elements[3])

    # Select the user specified
    cursor.execute("SELECT usd_balance FROM Users WHERE ID = ?", (user_id,))
    balance = cursor.fetchone()[0]

    balance = float(balance)

    # Check if the user has sufficient balance to make the purchase
    if balance >= (price * quantity):
        balance -= (price * quantity)
        # Update the user's balance
        cursor.execute("UPDATE Users SET usd_balance = ? WHERE ID = ?", (balance, user_id))
        db_conn.commit()
    else: # Return the error message
        db_conn.close()
        return "   403 Insufficient Balance"
   
    cursor.execute("SELECT * FROM Stocks WHERE user_id = ? AND stock_symbol = ?", (user_id, symbol))
    existing = cursor.fetchone()

    # Update the stock balance if the user already owns this stock, otherwise insert a new record
    if existing:
        new_stock_balance = existing[3] + quantity
        cursor.execute("UPDATE Stocks SET stock_balance = ? WHERE user_id = ? AND stock_symbol = ?",
                       (new_stock_balance, user_id, symbol))
    else:
        cursor.execute("INSERT INTO Stocks (stock_symbol, stock_balance, stock_name, user_id) VALUES (?, ?, 'Default', ?)",
                       (symbol, quantity, user_id))
    db_conn.commit()
    db_conn.close()

    response = f"   BOUGHT: New Balance: {quantity} {symbol}. USD balance ${balance}"
    return response

def sell_command(command, user_id):
    """Handle the SELL command, sell stocks for a user."""
    db_conn = sqlite3.connect(data_file)
    cursor = db_conn.cursor()

    # Split command into parts
    elements = command.split(" ")
    symbol = elements[1]
    quantity = int(elements[2])
    price = float(elements[3])

    # Make sure the user has enough stock
    cursor.execute("SELECT stock_balance FROM Stocks WHERE user_id = ? AND stock_symbol = ?", (user_id, symbol))
    stock_balance = cursor.fetchone()
    if not stock_balance or stock_balance[0] < quantity:
        db_conn.close()
        return "   403 Insufficient Stock"
    
    # Update the amount of stocks
    new_stock_balance = stock_balance[0] - quantity
    cursor.execute("UPDATE Stocks SET stock_balance = ? WHERE user_id = ? AND stock_symbol = ?",
                   (new_stock_balance, user_id, symbol))

    # Update the user's balance
    cursor.execute("SELECT usd_balance FROM Users WHERE ID = ?", (user_id,))
    balance = cursor.fetchone()[0]
    balance += price * quantity
    cursor.execute("UPDATE Users SET usd_balance = ? WHERE ID = ?", (balance, user_id))

    db_conn.commit()
    db_conn.close()

    # Return the successful purchase message
    response = f"   SOLD: New Balance: {quantity} {symbol}. USD balance ${balance}"
    return response

def shutdown_command():
    """Handle the SHUTDOWN command, break the server loop."""
    global is_running
    is_running = False
    return

def quit_command(client_connection):
    """Handle the QUIT command, close the client connection."""
    client_connection.close()

def balance_command(user_id):
    """Retrieve the balance of a user."""
    db_conn = sqlite3.connect(data_file)
    cursor = db_conn.cursor()

    # Select the user specified and their balance
    cursor.execute("SELECT usd_balance,first_name,last_name FROM Users WHERE ID = ?",(user_id,))
    user_data = cursor.fetchone()
    if user_data:
        usd_balance,first_name,last_name = user_data
        return f"   Balance for user {first_name} {last_name} is ${usd_balance:.2f}"
    
    db_conn.close()
    return 

def who_command():
    """List all active user sessions."""
    global sessions
    response = ''
    response += "   The list of active users:\n"
    for username, user_ip in sessions.items():
        response += f"   {username}   {user_ip}\n"
    return response

def lookup_command(command, user_id):
    """Handle the LOOKUP command, search for stocks."""
    db_conn = sqlite3.connect(data_file)
    cursor = db_conn.cursor()

    # Extract the stock name from the command
    parts = command.split(" ")
    if len(parts) != 2:
        return "400 Invalid command"

    stock_symbol = parts[1]

    # Query the database for the stock records
    cursor.execute("SELECT stock_balance FROM Stocks WHERE user_id = ? AND stock_symbol LIKE ?",
                   (user_id, f'%{stock_symbol}%'))
    data = cursor.fetchall()

    if not data:
        return "404 Your search did not match any records."

    response = "s: 200 OK\n"
    response += f"   Found {len(data)} match(es)\n"
    for stock in data:
        response += f"   {stock_symbol} {stock[0]}\n"

    db_conn.close()
    return response
  
def logout_command(user_id):
    """Handle the LOGOUT command, remove user session."""
    global sessions
    
    db_conn = sqlite3.connect(data_file)
    cursor = db_conn.cursor()
    cursor.execute(f"SELECT user_name FROM Users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    del sessions[result[0]]
    db_conn.close()
    return  

def deposit_command(command, user_id):
    """Handle the DEPOSIT command, deposit funds into user's balance."""
    db_conn = sqlite3.connect(data_file)
    cursor = db_conn.cursor()

    # Extract the amount from the command
    parts = command.split(" ")
    if len(parts) != 2:
        return "400 Invalid command"

    try:
        amount = float(parts[1])
        if amount <= 0:
            return "400 Invalid amount"
    except ValueError:
        return "400 Invalid amount"

    # Update the user's balance
    cursor.execute("SELECT usd_balance FROM Users WHERE ID = ?", (user_id,))
    current_balance = cursor.fetchone()[0]
    new_balance = current_balance + amount
    cursor.execute("UPDATE Users SET usd_balance = ? WHERE ID = ?", (new_balance, user_id))
    db_conn.commit()

    db_conn.close()
    return f"s: DEPOSIT successfully. New balance ${new_balance:.2f}"

# Define a dictionary for error codes and messages
error_messages = {
    "400": "Invalid command",
    "403_insufficient_balance": "Insufficient Balance",
    "403_insufficient_stock": "Insufficient Stock",
    "403_format_error": "Message format error",
    "403_user_not_found": "User not found"
}

def interpret(data, conn, user_id):
    """Interpret incoming commands and execute corresponding functions."""
    global is_running

    db_conn = sqlite3.connect(data_file)
    cursor = db_conn.cursor()

    response = ""

    # Handle different commands based on the incoming data
    if data == 'LIST':
        response += "s: Received: LIST\0"
        commandResponse = list_command(user_id)
        if commandResponse == "Err":
            response += f"   No stocks found for user {user_id}"
        else:
            response += "200 OK\0"
            response += commandResponse
        conn.send(response.encode())
    elif data == "LOGOUT":
        conn.send("200 OK\0".encode())
        logout_command(user_id=user_id)
    elif data == "WHO":
        if user_id == 2:
            response += "200 OK\0"
            command_response = who_command()
            response += command_response
        else:
            response = "Err, you are not permitted to use this command\0"
        conn.send(response.encode())
    
    elif data.startswith("DEPOSIT"):
        # Handle DEPOSIT command
        response = deposit_command(data, user_id)
        conn.send(response.encode())
    
    elif data == "BALANCE":
        response += "s: Received: BALANCE\0"
        command_response = balance_command(user_id)
        if command_response:
            response += "200 OK\0"
            response += command_response
        else:
            response += "403 User not found\0"
        conn.send(response.encode())

    elif data == "SHUTDOWN":
        if user_id ==2:
            response += "s: Received: SHUTDOWN\0"
            response += "200 OK"
            conn.send(response.encode())
            shutdown_command()
        else:
            response = "Err, you are not permitted to use this command\0"
            conn.send(response.encode())    
    elif data.startswith("LOOKUP"):
        # Handle LOOKUP command
        response = lookup_command(data, user_id)
        conn.send(response.encode())
    
    elif data == "QUIT":
        response += "200 OK\0"
        conn.send(response.encode())
        quit_command(conn)

    # Regex handles the formatting here, as well as Sell Command
    elif "BUY" in data:
        pattern = re.compile(r'^BUY [A-Z]+ \d+ (\d+(\.\d{1,2})?) \d')
        if pattern.match(data):
            response += f"s: Received: {str(data)}\0"
            commandResponse = buy_command(data, user_id)
            if "403" in commandResponse:
                response += commandResponse
            else:
                response += "200 OK\0"
                response += commandResponse
            conn.send(response.encode())
        else:
            response += f"s: {error_messages['403_format_error']}\0"
            response += "   Format is: BUY <stock_symbol> <amount> <price per stock> <user_id>"
            conn.send(response.encode())

    elif "SELL" in data:
        pattern = re.compile(r'^SELL [A-Z]+ \d+ (\d+(\.\d{1,2})?) \d')
        if pattern.match(data):
            response += f"s: Received: {str(data)}\0"
            commandResponse = sell_command(data, user_id)
            if "403" in commandResponse:
                response += commandResponse
            else:
                response += "200 OK\0"
                response += commandResponse
            conn.send(response.encode())
        else:
            response += f"s: {error_messages['403_format_error']}\0"
            response += "   Format is: SELL <stock_symbol> <amount> <price per stock> <user_id>"
            conn.send(response.encode())
    else:
        response += f"s: {error_messages['400']}\0"
        conn.send(response.encode())

    db_conn.close()

def process_login(user_input, conn):
    """Process user login and return user ID if successful."""
    global sessions
    parts = user_input.split()

    if len(parts) == 3 and parts[0] == "LOGIN":
        username = parts[1]
        password = parts[2]

        db_conn = sqlite3.connect(data_file)
        cursor = db_conn.cursor()

        # Query the Users table for the provided username and password
        cursor.execute("SELECT ID FROM Users WHERE user_name=? AND password=?", (username, password))
        user_id = cursor.fetchone()  # Fetch the user's ID

        if user_id:
            sessions[username] = conn.getpeername()[0]
            db_conn.close()
            return (user_id[0], username)  # Return the user's ID if login is successful
        else:
            db_conn.close()
            return "403"  # Return an error code for wrong credentials
    else:
        return "400"  # Return an error code for wrong format


def handle_client(client_socket, address):
    """Handle client connections, including login and command execution."""
    global sessions
    print(f"Accepted connection from {address}")

    is_logged_in = False  # Track login status
    user_id = None  # Initialize user ID

    while not is_logged_in:
        try:
            data = client_socket.recv(1024).decode()
        
            # Attempt login
            login_result = process_login(data, client_socket)
            if login_result is not None:
                if login_result == "400":
                    client_socket.send("400 command not found, please log in with LOGIN username password\0".encode())
                elif login_result == "403":
                    client_socket.send("403 Wrong UserID or Password\0".encode())
                else:
                    user_id, username = login_result
                    sessions[username] = client_socket.getpeername()[0]
                    is_logged_in = True
                    client_socket.send("200 OK\0".encode())
            else:
                client_socket.send("500 Internal Server Error\0".encode())
        except Exception as e:
            print(f"Error handling client: {e}")
            break


    # Once logged in, proceed with handling commands
    while is_logged_in:
        try:
            data = client_socket.recv(1024).decode()
            interpret(data, client_socket, user_id)  # Pass the user ID to other commands
        except Exception as e:
            print(f"Error handling client: {e}")
            break

    print(f"Closing connection from {address}")
    if user_id is not None:
        del sessions[username]
    client_socket.close()

def run_server(server_ip):
    """Run the server, accepting incoming connections."""
    global is_running
    make_db()
    check_db()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)  # Listen for up to 5 connections

    print(f"Server listening on {server_ip}:{server_port}")

    try:
        while is_running:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()
    finally:
        server_socket.close()

if __name__ == "__main__":
    server_ip = input("Enter server IP address or Enter for localhost: ").strip()
    if not server_ip:
        server_ip = 'localhost'  # Default to localhost if no input provided

    run_server(server_ip)
