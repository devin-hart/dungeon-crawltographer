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
                message = data.decode('utf-8')
                
                parts = message.split(';', 1)
                if len(parts) == 2:
                    seq, command = parts
                    print(f"DEBUG: Received command '{command}' (Seq: {seq}) from {addr}")

                    # Send acknowledgment back to the original sender
                    ack_message = f"ack;{seq}".encode('utf-8')
                    self.sock.sendto(ack_message, addr)

                    event_data = {'command': command}
                    pygame.event.post(pygame.event.Event(REMOTE_MOVE_EVENT, event_data))
            except Exception:
                break