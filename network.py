import socket
import pickle
import threading


class NetworkGame:
    def __init__(self, host="localhost", port=5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.addr = (self.host, self.port)
        self.connected = False
        self.game_id = None
        self.player_num = None
        self.game_state = None

    def connect(self):
        try:
            self.client.connect(self.addr)
            self.connected = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def send(self, data):
        if not self.connected:
            return None
        
        try:
            self.client.settimeout(5.0)
            self.client.send(pickle.dumps(data))
            
            try:
                response = pickle.loads(self.client.recv(2048*2))
                print(f"Network response: {response}")  # Debug print
                
                if isinstance(response, dict):
                    if response.get("status") == "starting":
                        print("Received game start data")  # Debug print
                        if "game_id" in response:
                            self.game_id = response["game_id"]
                        if "player_num" in response:
                            self.player_num = response["player_num"]
                        if "game_state" in response:
                            self.game_state = response["game_state"]
                    
                return response
                
            except pickle.UnpicklingError as e:
                print(f"Error unpickling response: {e}")
                return None
                
        except socket.error as e:
            print(f"Network error in send: {e}")
            self.connected = False
            return None
        finally:
            self.client.settimeout(None)

    def play_card(self, card):
        if not self.connected:
            return None
        return self.send({
            "action": "play_card",
            "card": card,
            "game_id": self.game_id,
            "player_num": self.player_num
        })
