This document outlines the architecture and implementation steps for using **UDP Sockets** to enable real-time, low-latency controller input from your Gaming PC to your Python-based Dungeon Crawltographer application running on a separate Mapper PC.

The UDP Sockets approach is chosen because it minimizes network overhead and latency, which is critical for responsive, real-time input like button presses.

## Cross-PC Controller Mapping Project: UDP Sockets Solution

### I. Architecture Overview

| Component | Role | Technology | Required Library |
| :--- | :--- | :--- | :--- |
| **Gaming PC** (Client) | Reads controller input and transmits commands as simple strings. | Python `socket` & `inputs` | `inputs` |
| **Mapper PC** (Server) | Runs a Python `socket` listener in a background thread to receive commands. | Python `socket` & `pygame` | None (Standard Library) |
| **Communication** | Connectionless, low-latency data packets. | UDP (User Datagram Protocol) | None (Standard Library) |

### II. Mapper PC (Server/Receiver) Setup

The Mapper PC is where your `dungeon_mapper.py` code resides. It will listen for the controller commands.

#### A. Required New File: `udp_listener.py`

Create this file in the same directory as `dungeon_mapper.py`. This script sets up the non-blocking UDP socket and translates incoming commands into a custom Pygame event (`REMOTE_MOVE_EVENT`) that the main thread can safely process.

```python
import threading
import socket
import pygame

UDP_IP = "0.0.0.0"
UDP_PORT = 5000
# Define a custom Pygame event ID
REMOTE_MOVE_EVENT = pygame.event.custom_type() 

class UDPInputListener(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind((UDP_IP, UDP_PORT))
        except OSError as e:
            print(f"ERROR: Could not bind UDP socket to port {UDP_PORT}. {e}")
            self.sock = None

    def run(self):
        if not self.sock: return
        print(f"Starting UDP listener on port {UDP_PORT}...")
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                command = data.decode('utf-8')
                
                event_data = {'command': command}
                pygame.event.post(pygame.event.Event(REMOTE_MOVE_EVENT, event_data))
            except Exception:
                break
```

#### B. Modify `dungeon_mapper.py`

1.  **Imports:** Replace any previous remote server imports:

    ```python
    # Top of dungeon_mapper.py
    try:
        from udp_listener import UDPInputListener
    except ImportError:
        print("Warning: Could not import UDPInputListener. Remote mapping disabled.")
        UDPInputListener = None
    ```

2.  **Initialization:** Start the listener in `DungeonMapper.__init__`:

    ```python
    # Inside DungeonMapper.__init__(self):
    # ... existing initialization ...

    # New: Start the UDP listener
    self.udp_listener = None
    if UDPInputListener:
        self.udp_listener = UDPInputListener()
        self.udp_listener.start()
    ```

3.  **Command Handling:** Add the method to process the received commands:

    ```python
    # New method in DungeonMapper class
    def handle_remote_command(self, command: str):
        """Processes commands received from the remote UDP client."""
        if command == 'forward':
            self.move_player(forward=True)
        elif command == 'backward':
            self.move_player(forward=False)
        elif command == 'rotate_left':
            self.rotation = (self.rotation + 90) % 360
        elif command == 'rotate_right':
            self.rotation = (self.rotation - 90) % 360
        # Add other commands here as needed (e.g., 'change_floor_up')
    ```

#### C. Modify `event_handler.py`

1.  **Imports:** Import the custom event ID:

    ```python
    # Top of event_handler.py
    try:
        from udp_listener import REMOTE_MOVE_EVENT
    except ImportError:
        REMOTE_MOVE_EVENT = -1
    ```

2.  **Event Handling:** Process the custom event in `EventHandler.handle_events`:

    ```python
    # Inside EventHandler.handle_events(self):
        for event in pygame.event.get():
            # ... existing checks (QUIT, VIDEORESIZE) ...

            # Handle the custom UDP event
            elif event.type == REMOTE_MOVE_EVENT:
                self.app.handle_remote_command(event.command)
                continue 
            
            # ... rest of the event handling logic ...
    ```

### III. Gaming PC (Client/Sender) Setup

The Gaming PC will run a script to read your controller and instantly transmit data.

#### A. Install Dependency

```sh
pip install inputs
```

#### B. Required New File: `game_pc_client.py`

This script uses the `inputs` library to read the controller state and the `socket` library to send the command string via UDP.

```python
import time
import socket
from inputs import get_gamepad, UnpluggedError

# --- CONFIGURATION ---
# >>> REPLACE THIS WITH THE ACTUAL LOCAL IP OF YOUR MAPPER PC <<<
MAPPER_PC_IP = "192.168.1.100" 
MAPPER_PC_PORT = 5000

# Map controller input codes to the command strings expected by the mapper.
COMMAND_MAP = {
    # D-Pad Y-axis: -1 for UP, 1 for DOWN
    'ABS_HAT0Y': lambda state: 'forward' if state == -1 else ('backward' if state == 1 else None),
    # D-Pad X-axis: -1 for LEFT, 1 for RIGHT
    'ABS_HAT0X': lambda state: 'rotate_left' if state == -1 else ('rotate_right' if state == 1 else None),
}

def process_gamepad_events():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP socket
    last_sent_command = None
    
    print(f"Listening for input and sending UDP to {MAPPER_PC_IP}:{MAPPER_PC_PORT}")
    
    while True:
        try:
            events = get_gamepad()
            current_command = None
            
            for event in events:
                if event.code in COMMAND_MAP:
                    # Execute the lambda function to get the command string
                    command = COMMAND_MAP[event.code](event.state)
                    if command:
                        current_command = command
                        break 

            # Transmit only if the command is active and different from the last sent command
            if current_command and current_command != last_sent_command:
                message = current_command.encode('utf-8')
                sock.sendto(message, (MAPPER_PC_IP, MAPPER_PC_PORT))
                last_sent_command = current_command
                
            time.sleep(0.005) # Maintain fast polling

        except UnpluggedError:
            print("Controller disconnected. Waiting for reconnection...")
            last_sent_command = None
            time.sleep(2)
        except Exception:
            time.sleep(0.1)

if __name__ == "__main__":
    process_gamepad_events()
```