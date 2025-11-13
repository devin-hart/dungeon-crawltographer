import time
import socket
import threading
from inputs import get_gamepad, UnpluggedError

# --- CONFIGURATION ---
# >>> REPLACE THIS WITH THE ACTUAL LOCAL IP OF YOUR MAPPER PC <<<
MAPPER_PC_IP = "192.168.1.213" 
MAPPER_PC_PORT = 5000

ACK_TIMEOUT = 0.1 # 100ms
# Map controller input codes to the command strings expected by the mapper.
COMMAND_MAP = {
    # D-Pad Y-axis: -1 for UP, 1 for DOWN
    'ABS_HAT0Y': lambda state: 'forward' if state == -1 else ('backward' if state == 1 else None),
    # D-Pad X-axis: -1 for LEFT, 1 for RIGHT
    'ABS_HAT0X': lambda state: 'rotate_left' if state == -1 else ('rotate_right' if state == 1 else None),
    # L2 Trigger: state == 255 for a full press
    'ABS_Z': lambda state: 'mark_cell' if state == 255 else None,
}

class AckListener(threading.Thread):
    """A thread to listen for acknowledgment packets from the mapper."""
    def __init__(self, sock):
        super().__init__(daemon=True)
        self.sock = sock
        self.latest_ack_seq = -1
        self.running = True

    def run(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(1024)
                ack_msg = data.decode('utf-8')
                if ack_msg.startswith('ack;'):
                    self.latest_ack_seq = int(ack_msg.split(';')[1])
            except (socket.timeout, BlockingIOError):
                continue # Ignore timeouts, just keep listening
            except Exception:
                break # Exit on other errors

def process_gamepad_events():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP socket
    sock.settimeout(0.05) # Set a short timeout for receiving acks
    last_sent_command = None
    sequence_number = 0

    # Start the acknowledgment listener thread
    ack_listener = AckListener(sock)
    ack_listener.start()
    
    print(f"Listening for input and sending UDP to {MAPPER_PC_IP}:{MAPPER_PC_PORT}")
    
    while True:
        try:
            events = get_gamepad()
            current_command = None
            dpad_released = False

            for event in events:
                # print(f"Raw Event: code={event.code}, state={event.state}, event_type={event.ev_type}") # DEBUG
                if event.code in COMMAND_MAP:
                    command = COMMAND_MAP[event.code](event.state)
                    # A non-None command means a direction was pressed
                    if command:
                        current_command = command
                        print(f"Detected command: {current_command}")
                    # A state of 0 means the D-pad axis returned to neutral
                    elif event.state == 0:
                        dpad_released = True

            # If the D-pad was released, we must clear the last sent command
            # to allow the next press to be registered.
            if dpad_released:
                last_sent_command = None

            # Transmit only if the command is active and different from the last sent command
            if current_command and current_command != last_sent_command:
                sequence_number += 1
                message = f"{sequence_number};{current_command}"
                
                # Retry loop
                retries = 3
                while retries > 0:
                    print(f"Sending: '{current_command}' (Seq: {sequence_number})")
                    sock.sendto(message.encode('utf-8'), (MAPPER_PC_IP, MAPPER_PC_PORT))
                    
                    # Wait for acknowledgment
                    wait_until = time.time() + ACK_TIMEOUT
                    while time.time() < wait_until:
                        if ack_listener.latest_ack_seq == sequence_number:
                            break # Ack received!
                        time.sleep(0.01)
                    
                    if ack_listener.latest_ack_seq == sequence_number:
                        break # Exit retry loop
                    
                    print(f"Timeout, retrying... ({retries-1} left)")
                    retries -= 1

                last_sent_command = current_command
                
            time.sleep(0.005) # Maintain fast polling

        except UnpluggedError:
            print("Controller disconnected. Waiting for reconnection...")
            last_sent_command = None
            time.sleep(2)
        except Exception as e:
            # Catch any other unexpected errors during event processing or sending
            print(f"An unexpected error occurred in game_pc_client: {e}")
            time.sleep(0.1)

if __name__ == "__main__":
    process_gamepad_events()
