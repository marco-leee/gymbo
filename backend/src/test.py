import socketio
import time

# Create a Socket.IO client instance
sio = socketio.Client()


# Event handlers
@sio.event
def connect():
    print("Connected to server")


@sio.event
def connect_error(data):
    print("Connection failed:", data)


@sio.event
def disconnect():
    print("Disconnected from server")


def main():
    try:
        # Replace with your server URL
        server_url = "https://api.stixman.co"

        # Connect to the server
        print(f"Attempting to connect to {server_url}...")
        sio.connect(server_url)

        # Keep the connection alive for a few seconds to test
        time.sleep(5)

        # Disconnect from the server
        sio.disconnect()

    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        if sio.connected:
            sio.disconnect()


if __name__ == "__main__":
    main()
