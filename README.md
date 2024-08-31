# Stock Transaction Server-Client Application

## Overview

This project is a server-client application for managing stock transactions. The server handles commands related to buying, selling, and managing stocks, while the client application interacts with the server to execute these commands.

## Environment and Requirements

### Required Software

- **Python**: This project requires Python 3.6 or higher. Ensure Python is installed on your system.

### Dependencies

- **Python Libraries**:
  - `socket`: For network communication.
  - `sqlite3`: For database management.
  - `time`: For handling time-related tasks.
  - `decimal.Decimal`: For precise decimal arithmetic.
  - `re`: For regular expressions.
  - `os`: For interacting with the operating system.
  - `threading`: For handling multiple threads.
  - `secrets`: For generating cryptographically strong random numbers.

These libraries are part of Python's standard library and do not require separate installation via pip.

## Setup

1. **Clone the Repository**: Download or clone the project repository to your local machine.

   ```bash
   git clone <repository_url>
   ```

2. **Create and Activate a Python Virtual Environment**:
   - **Create the virtual environment:**

     ```bash
     python -m venv venv
     ```

   - **Activate the virtual environment:**
     - **On Windows:**

       ```bash
       venv\Scripts\activate
       ```

     - **On macOS and Linux:**

       ```bash
       source venv/bin/activate
       ```

3. **Install Dependencies** (if applicable in the future): Since the current project uses only Python's standard libraries, no additional packages are required. If external libraries are added later, they can be installed using pip.

4. **Setup Database**: The server script automatically creates and initializes the database (`stocks.db`) with default data upon the first run.

## Launching the Application

### Launch the Server

1. Open a terminal or command prompt.

2. Navigate to the directory containing the server script.

3. Run the server script with the command:

    ```bash
    python server.py
    ```

4. The server will prompt you to enter the server IP address. Press Enter to use the default `localhost`, or provide a specific IP address if needed.

### Launch the Client

1. Open a terminal or command prompt.

2. Navigate to the directory containing the client script.

3. Run the client script with the command:

    ```bash
    python client.py
    ```

4. The client will prompt you to enter the server IP address. Press Enter to use the default `localhost`, or provide the IP address of the server if it's running on a different machine.

## Server Functions

The server script includes various functions to handle client requests and manage stock transactions:

- **`make_db()`**: Creates the initial database structure if it doesn't exist and inserts default users.

- **`check_db()`**: Checks if the database has any users; if not, adds a default user.

- **`list_command(user_id)`**: Retrieves and lists stocks for a user or all stocks if the user is an admin.

- **`buy_command(command, user_id)`**: Handles stock purchases for a user, checking for sufficient funds.

- **`sell_command(command, user_id)`**: Handles stock sales for a user, checking for sufficient stock.

- **`shutdown_command()`**: Shuts down the server.

- **`quit_command(client_connection)`**: Closes the client connection.

- **`balance_command(user_id)`**: Retrieves and returns the balance of a user.

- **`who_command()`**: Lists all active user sessions.

- **`lookup_command(command, user_id)`**: Searches for stocks based on the command.

- **`logout_command(user_id)`**: Removes a user session.

- **`deposit_command(command, user_id)`**: Deposits funds into a user's balance.

- **`interpret(data, conn, user_id)`**: Interprets and executes commands sent by clients.

- **`process_login(user_input, conn)`**: Processes user login requests and returns user ID if successful.

- **`handle_client(client_socket, address)`**: Handles client connections, including login and command execution.

- **`run_server(server_ip)`**: Runs the server, accepting incoming connections.

## Client Functions

- **`get_server_ip()`**: Prompts the user for the server IP address.

- **`send(command)`**: Sends commands to the server and receives the response.

## Examples of Commands

Here are some example commands you can send from the client to interact with the server:

1. **Login**:
    - `LOGIN <username> <password>`
    - Example: `LOGIN John John01`

2. **List Stocks**:
    - `LIST`
    - Retrieves all stocks or stocks for a specific user based on permissions.

3. **Buy Stocks**:
    - `BUY <stock_symbol> <quantity> <price_per_stock>`
    - Example: `BUY AAPL 10 150.00`

4. **Sell Stocks**:
    - `SELL <stock_symbol> <quantity> <price_per_stock>`
    - Example: `SELL AAPL 5 155.00`

5. **Check Balance**:
    - `BALANCE`
    - Retrieves the current balance of the logged-in user.

6. **Deposit Funds**:
    - `DEPOSIT <amount>`
    - Example: `DEPOSIT 50.00`

7. **Lookup Stocks**:
    - `LOOKUP <stock_symbol>`
    - Example: `LOOKUP AAPL`

8. **Logout**:
    - `LOGOUT`
    - Logs out the current user.

9. **Shutdown Server** (Admin Only):
    - `SHUTDOWN`
    - Shuts down the server if the user has the proper permissions.

10. **List Active Sessions** (Admin Only):
    - `WHO`
    - Lists all active user sessions if the user has the proper permissions.

11. **Quit Client**:
    - `QUIT`
    - Closes the client connection.

## Known Issues

- **Command Handling**: The `BUY` and `SELL` commands currently do not handle partial stock purchases correctly.
- **Default Stock Name**: If no name is provided for a stock, it defaults to "Default".
- **Error Handling**: The command "LOGIN space space" does not trigger a 403 error as expected.
- **Formatting Issues**: There are some formatting issues, such as extra lines between commands, though messages are still legible.