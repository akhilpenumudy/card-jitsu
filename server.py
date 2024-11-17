import socket
import threading
import pickle
from _thread import *
import random
import time


class GameSession:
    def __init__(self, player1_conn, player1_name, player2_conn, player2_name):
        self.player1 = {
            "conn": player1_conn,
            "name": player1_name,
            "hand": [],
            "score": 0,
        }
        self.player2 = {
            "conn": player2_conn,
            "name": player2_name,
            "hand": [],
            "score": 0,
        }

        # Randomly select who goes first
        self.current_turn = random.choice([player1_name, player2_name])
        print(f"{self.current_turn} will go first!")

        self.game_state = {
            "player1": {
                "name": player1_name,
                "score": 0,
                "played_card": None,
                "hand": [],
            },
            "player2": {
                "name": player2_name,
                "score": 0,
                "played_card": None,
                "hand": [],
            },
            "current_turn": self.current_turn,
            "status": "playing",
            "first_turn": self.current_turn,
            "round_result": None,  # Add this to store round results
        }
        self.deal_initial_cards()

    def deal_initial_cards(self):
        # Create and shuffle deck
        suits = ["hearts", "diamonds", "spades"]
        values = range(2, 11)
        deck = [(suit, value) for suit in suits for value in values]
        deck = deck * 2  # Two copies of each card
        random.shuffle(deck)

        # Deal 5 cards to each player
        self.player1["hand"] = deck[:5]
        self.player2["hand"] = deck[5:10]

        # Update game state with hands
        self.game_state["player1"]["hand"] = self.player1["hand"]
        self.game_state["player2"]["hand"] = self.player2["hand"]

    def compare_cards(self):
        card1 = self.game_state["player1"]["played_card"]
        card2 = self.game_state["player2"]["played_card"]

        if not card1 or not card2:
            return None

        print(f"Comparing cards: {card1} vs {card2}")  # Debug print

        # Define the winning relationships
        beats = {"diamonds": "spades", "spades": "hearts", "hearts": "diamonds"}

        suit1, value1 = card1
        suit2, value2 = card2

        # Check for exact same card (draw)
        if suit1 == suit2 and value1 == value2:
            print("Draw!")
            return None

        if suit1 == suit2:
            # Same suit, compare values
            winner = "player1" if value1 > value2 else "player2"
        else:
            # Different suits, check if player1's card beats player2's card
            winner = "player1" if beats[suit1] == suit2 else "player2"

        print(f"Winner determined: {winner}")  # Debug print

        # Update scores
        self.game_state[winner]["score"] += 1

        # Store round result
        self.game_state["round_result"] = {
            "winner": winner,
            "card1": card1,
            "card2": card2,
            "highlight_winner": True,
        }

        # Deal replacement cards
        self.deal_replacement_cards()

        # Update round counter
        self.game_state["round"] = self.game_state.get("round", 1) + 1

        # Reset played cards
        self.game_state["player1"]["played_card"] = None
        self.game_state["player2"]["played_card"] = None

        # Set next turn to the loser
        self.game_state["current_turn"] = self.game_state[
            "player2" if winner == "player1" else "player1"
        ]["name"]

        return winner

    def deal_replacement_cards(self):
        # Create and shuffle deck for replacements
        suits = ["hearts", "diamonds", "spades"]
        values = range(2, 11)
        deck = [(suit, value) for suit in suits for value in values]
        random.shuffle(deck)

        # Deal replacement cards
        if len(self.game_state["player1"]["hand"]) < 5:
            new_card = deck.pop()
            self.game_state["player1"]["hand"].append(new_card)

        if len(self.game_state["player2"]["hand"]) < 5:
            new_card = deck.pop()
            self.game_state["player2"]["hand"].append(new_card)


class GameServer:
    def __init__(self, host="", port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server.bind((host, port))
        except socket.error as e:
            print(str(e))
        self.server.listen(2)
        self.games = {}
        self.waiting_player = None
        print("Server Started, waiting for connections...")

    def start(self):
        while True:
            try:
                conn, addr = self.server.accept()
                print(f"Connected to: {addr}")

                try:
                    data = pickle.loads(conn.recv(2048))
                    if isinstance(data, str):  # If data is just the player name
                        player_name = data
                        print(f"Player {player_name} connected")

                        # Start new thread for this client
                        start_new_thread(self.handle_client, (conn, player_name))
                except Exception as e:
                    print(f"Error handling connection: {e}")
                    conn.close()

            except Exception as e:
                print(f"Server error: {e}")
                break

        print("Server shutting down...")
        self.server.close()

    def handle_client(self, conn, player_name):
        try:
            if self.waiting_player is None:
                # First player to join
                print(f"First player {player_name} waiting for opponent")
                self.waiting_player = (conn, player_name)

                # Keep first player updated while waiting
                while self.waiting_player and self.waiting_player[0] == conn:
                    try:
                        conn.send(pickle.dumps({"status": "waiting"}))
                        # Receive any messages from client without breaking connection
                        try:
                            data = pickle.loads(conn.recv(2048))
                            if not data:  # Client disconnected
                                break
                        except:
                            pass  # Ignore timeout/empty messages
                        time.sleep(0.1)  # Short delay to prevent CPU overload
                    except Exception as e:
                        print(f"Error in waiting loop: {e}")
                        break

            else:
                # Second player - start the game
                player1_conn, player1_name = self.waiting_player
                player2_conn = conn
                player2_name = player_name

                print(f"Second player {player_name} joined, starting game")

                # Create game session
                game_session = GameSession(
                    player1_conn, player1_name, player2_conn, player2_name
                )
                game_id = len(self.games)
                self.games[game_id] = game_session

                # Send initial game state to both players
                try:
                    # Prepare data for player 1
                    player1_data = {
                        "status": "starting",
                        "game_id": game_id,
                        "player_num": 1,
                        "game_state": game_session.game_state,
                    }

                    # Prepare data for player 2
                    player2_data = {
                        "status": "starting",
                        "game_id": game_id,
                        "player_num": 2,
                        "game_state": game_session.game_state,
                    }

                    # Send data and verify it was received
                    player1_conn.send(pickle.dumps(player1_data))
                    print(f"Sent game data to {player1_name}")

                    player2_conn.send(pickle.dumps(player2_data))
                    print(f"Sent game data to {player2_name}")

                    # Reset waiting player
                    self.waiting_player = None

                    # Start game handler threads
                    start_new_thread(
                        self.handle_game_client, (player1_conn, game_id, 1)
                    )
                    start_new_thread(
                        self.handle_game_client, (player2_conn, game_id, 2)
                    )

                    return  # Successfully started game

                except Exception as e:
                    print(f"Error starting game: {e}")
                    self.waiting_player = None
                    raise e

        except Exception as e:
            print(f"Error in handle_client: {e}")
            if self.waiting_player and self.waiting_player[0] == conn:
                self.waiting_player = None

    def handle_game_client(self, conn, game_id, player_num):
        game = self.games[game_id]

        while True:
            try:
                # Keep connection alive with periodic updates
                if player_num == 1:
                    player = game.player1
                else:
                    player = game.player2

                # Send current game state
                try:
                    game_update = {"status": "in_game", "game_state": game.game_state}
                    conn.send(pickle.dumps(game_update))

                    # Receive client response
                    data = pickle.loads(conn.recv(2048 * 2))
                    if data == "get_state":
                        continue

                    # Handle game actions
                    if isinstance(data, dict) and data.get("action") == "play_card":
                        card = data.get("card")
                        player_name = game.player1["name"] if player_num == 1 else game.player2["name"]

                        # Only allow card play if it's player's turn
                        if game.game_state["current_turn"] == player_name:
                            # Update played card and switch turn
                            if player_num == 1:
                                game.game_state["player1"]["played_card"] = card
                                game.game_state["current_turn"] = game.player2["name"]
                            else:
                                game.game_state["player2"]["played_card"] = card
                                game.game_state["current_turn"] = game.player1["name"]

                            print(f"Player {player_name} played card: {card}")
                            print(f"Turn switched to: {game.game_state['current_turn']}")

                            # Send update about played card to both players
                            turn_update = {
                                "status": "in_game",
                                "game_state": game.game_state
                            }
                            game.player1["conn"].send(pickle.dumps(turn_update))
                            game.player2["conn"].send(pickle.dumps(turn_update))

                            # Check if both players have played
                            if (game.game_state["player1"]["played_card"] and 
                                game.game_state["player2"]["played_card"]):
                                # Add delay before comparison
                                time.sleep(1)
                                
                                # First send state to reveal both cards
                                reveal_state = {
                                    "status": "in_game",
                                    "game_state": game.game_state,
                                    "reveal_cards": True
                                }
                                game.player1["conn"].send(pickle.dumps(reveal_state))
                                game.player2["conn"].send(pickle.dumps(reveal_state))
                                
                                # Wait for cards to be shown
                                time.sleep(2)
                                
                                # Compare cards and determine winner
                                winner = game.compare_cards()
                                print(f"Round complete. Winner: {winner}")
                                
                                # Send final round result
                                result_update = {
                                    "status": "in_game",
                                    "game_state": game.game_state
                                }
                                game.player1["conn"].send(pickle.dumps(result_update))
                                game.player2["conn"].send(pickle.dumps(result_update))
                                print("Sent round result to both players")

                except Exception as e:
                    print(f"Error in game loop: {e}")
                    break

                time.sleep(0.1)

            except Exception as e:
                print(f"Lost connection to player {player_num}: {e}")
                break


if __name__ == "__main__":
    server = GameServer()
    server.start()
