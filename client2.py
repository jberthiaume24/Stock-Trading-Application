import socket

# Function to prompt user for server IP address
def get_server_ip():
    ip = input("Enter server IP address or Enter for localhost: ").strip()
    if ip:
        return ip
    else:
        return "localhost"  # Default to localhost if no input provided

# Server information
server_host = get_server_ip()
server_port = 8100

# Create a socket object outside of the send function
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_host,server_port))

# Function to send commands to the server
def send(command):
    try:
        # Send the command to the server
        client_socket.sendall(command.encode())
        
        # Receive the response from the server
        response = client_socket.recv(1024).decode()
    
    except Exception as e:
        response = f"An error occurred: {e}"
    
    return response

if __name__ == "__main__":
    # Main loop for user interaction
    while True:
        # Get user input
        user_input = input("c: ")
        
        # Send the user input to the server
        response = send(user_input)
        
        # Print the response
        responses = response.split('\0')
        for resp in responses:
            if resp == "200 OK":
                print("c:", resp)
            else:
                print(resp)
        
        if user_input.strip() == "QUIT":
            # Close the socket before exiting
            client_socket.close()
            break
