import pygame
import sys
import random
import os
import math
from network import NetworkGame

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
CARD_WIDTH = 64
CARD_HEIGHT = 64
DOCK_HEIGHT = 150
CARD_SPACING = 10
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 50
HEADER_HEIGHT = 60
TIMER_RADIUS = 25
TIMER_CENTER = (TIMER_RADIUS + 20, HEADER_HEIGHT // 2)
TIMER_DURATION = 20  # seconds
COMPUTER_TURN_DELAY = 1000  # milliseconds before computer plays
SMALL_CARD_WIDTH = 32  # Size for the small victory cards
SMALL_CARD_HEIGHT = 32
END_SCREEN_ANIMATION_DURATION = 1000  # 1 second for fade in
VICTORY_CARD_SPIN_SPEED = 2  # degrees per frame
CONFETTI_COUNT = 100
COMPARISON_PAUSE = 3000  # 3 seconds to show the winner
WINNER_COLOR = (50, 205, 50)  # Green color for winner highlight

# Colors
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
GRAY = (169, 169, 169)
BUTTON_INACTIVE = (169, 169, 169)  # Gray
BUTTON_ACTIVE = (50, 205, 50)  # Green
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Set up the display
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Card Game")

# Load and scale instructions image
instructions_img = pygame.image.load("instructions.png")
instructions_img = pygame.transform.scale(instructions_img, (100, 100))
instructions_rect = instructions_img.get_rect()
# Center the image
instructions_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)


class Card:
    def __init__(self, suit, value, image_path):
        self.suit = suit
        self.value = value
        # Load and scale the card image
        original_image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(original_image, (CARD_WIDTH, CARD_HEIGHT))
        self.rect = self.image.get_rect()
        self.dragging = False
        self.original_pos = None
        self.animating = False
        self.animation_start = None
        self.animation_duration = 500  # milliseconds
        self.animation_start_pos = None
        self.animation_end_pos = None

    def set_position(self, x, y):
        self.rect.x = x
        self.rect.y = y
        if self.original_pos is None:
            self.original_pos = (x, y)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def handle_event(self, event, play_area, go_button):
        if not hasattr(self, 'dragging'):
            self.dragging = False
        if not hasattr(self, 'draggable'):
            self.draggable = True

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) and self.draggable:  # Only allow dragging if draggable
                self.dragging = True
                mouse_x, mouse_y = event.pos
                self.offset_x = self.rect.x - mouse_x
                self.offset_y = self.rect.y - mouse_y
                # If this card was in the play area, remove it
                if play_area.card == self:
                    play_area.remove_card()
                    go_button.active = False
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging:
                self.dragging = False
                # Check if card is dropped in play area
                if play_area.is_empty() and play_area.rect.colliderect(self.rect):
                    play_area.add_card(self)
                    go_button.active = True
                else:
                    self.rect.x, self.rect.y = self.original_pos
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_x, mouse_y = event.pos
                self.rect.x = mouse_x + self.offset_x
                self.rect.y = mouse_y + self.offset_y
        return False

    def start_deal_animation(self, end_pos):
        self.animating = True
        self.animation_start = pygame.time.get_ticks()
        # Start from below the screen
        self.animation_start_pos = (end_pos[0], WINDOW_HEIGHT + 50)
        self.animation_end_pos = end_pos
        self.rect.topleft = self.animation_start_pos

    def update_animation(self):
        if not self.animating:
            return False

        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.animation_start

        if elapsed >= self.animation_duration:
            self.animating = False
            self.rect.topleft = self.animation_end_pos
            self.original_pos = self.animation_end_pos
            return False

        # Calculate position using easing function
        progress = elapsed / self.animation_duration
        # Ease out cubic function
        progress = 1 - (1 - progress) ** 3

        x = (
            self.animation_start_pos[0]
            + (self.animation_end_pos[0] - self.animation_start_pos[0]) * progress
        )
        y = (
            self.animation_start_pos[1]
            + (self.animation_end_pos[1] - self.animation_start_pos[1]) * progress
        )

        self.rect.topleft = (x, y)
        return True


def create_deck():
    cards = []
    suits = ["hearts", "diamonds", "spades"]
    values = range(2, 11)

    # Create two identical decks
    for _ in range(2):  # Make two copies of each card
        for suit in suits:
            for value in values:
                image_path = os.path.join(
                    "Cards (large)", f"card_{suit}_{str(value).zfill(2)}.png"
                )
                cards.append(Card(suit, value, image_path))

    # Split the deck into player and computer portions
    random.shuffle(cards)
    mid = len(cards) // 2
    return cards[:mid], cards[mid:]  # Return (player_deck, computer_deck)


background = pygame.Surface(screen.get_size())
ts, w, h, c1, c2 = 50, *background.get_size(), (128, 128, 128), (64, 64, 64)
tiles = [
    ((x * ts, y * ts, ts, ts), c1 if (x + y) % 2 == 0 else c2)
    for x in range((w + ts - 1) // ts)
    for y in range((h + ts - 1) // ts)
]


def draw_game_board():
    # Fill the background (game table)

    screen.fill((135, 206, 235))

    # Draw the card dock area (bottom of screen)
    dock_rect = pygame.Rect(0, WINDOW_HEIGHT - DOCK_HEIGHT, WINDOW_WIDTH, DOCK_HEIGHT)
    pygame.draw.rect(screen, BLACK, dock_rect, 2)


def deal_cards(deck, num_cards):
    return random.sample(deck, num_cards)


class Button:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.active = False
        self.font = pygame.font.Font(None, 36)

    def draw(self, surface):
        color = BUTTON_ACTIVE if self.active else BUTTON_INACTIVE
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)

        text = self.font.render("GO", True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)


class PlayArea:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.card = None
        self.highlight = False
        self.highlight_color = WINNER_COLOR

    def add_card(self, card):
        # Remove existing card if there is one
        if self.card:
            self.remove_card()
        self.card = card
        # Center the card in the play area
        card.rect.centerx = self.rect.centerx
        card.rect.centery = self.rect.centery

    def remove_card(self):
        self.card = None

    def is_empty(self):
        return self.card is None

    def draw(self, surface):
        # Draw the play area
        pygame.draw.rect(surface, GRAY, self.rect)
        # Draw the border with appropriate color
        border_color = self.highlight_color if self.highlight else BLACK
        pygame.draw.rect(surface, border_color, self.rect, 2)

        # Draw the card if there is one
        if self.card:
            self.card.draw(surface)


class Timer:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 36)

    def reset(self):
        self.time_left = TIMER_DURATION
        self.last_update = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update >= 1000:  # 1000ms = 1s
            self.time_left -= 1
            self.last_update = now
            if self.time_left < 0:
                self.time_left = 0

    def draw(self, surface):
        # Draw outer circle
        pygame.draw.circle(surface, WHITE, TIMER_CENTER, TIMER_RADIUS)
        pygame.draw.circle(surface, BLACK, TIMER_CENTER, TIMER_RADIUS, 2)

        # Draw arc for remaining time
        if self.time_left > 0:
            angle = (self.time_left / TIMER_DURATION) * 360
            pygame.draw.arc(
                surface,
                RED,
                (
                    TIMER_CENTER[0] - TIMER_RADIUS,
                    TIMER_CENTER[1] - TIMER_RADIUS,
                    TIMER_RADIUS * 2,
                    TIMER_RADIUS * 2,
                ),
                0,
                -angle * (3.14159 / 180),
                3,
            )

        # Draw time text
        text = self.font.render(str(max(0, self.time_left)), True, BLACK)
        text_rect = text.get_rect(center=TIMER_CENTER)
        surface.blit(text, text_rect)


class Header:
    def __init__(self):
        self.font = pygame.font.Font(None, 48)
        self.timer = Timer()
        self.current_turn = "YOUR TURN"
        self.round = 1
        self.is_player_turn = True
        self.game_over = False
        self.winner = None  # Will be either "PLAYER" or "COMPUTER"
        self.reveal_message = None
        self.reveal_message_start = None
        self.reveal_message_duration = 2000  # 2 seconds

    def switch_turn(self):
        self.is_player_turn = not self.is_player_turn
        self.current_turn = "YOUR TURN" if self.is_player_turn else "COMPUTER'S TURN"
        self.timer.reset()

    def update(self):
        self.timer.update()
        return self.timer.time_left <= 0  # Return True if timer has expired

    def draw(self, surface):
        # Draw header background
        header_rect = pygame.Rect(0, 0, WINDOW_WIDTH, HEADER_HEIGHT)
        pygame.draw.rect(surface, WHITE, header_rect)
        pygame.draw.line(
            surface, BLACK, (0, HEADER_HEIGHT), (WINDOW_WIDTH, HEADER_HEIGHT), 2
        )

        # Draw timer
        self.timer.draw(surface)

        # Draw turn indicator
        turn_text = self.font.render(self.current_turn, True, BLACK)
        turn_rect = turn_text.get_rect(center=(WINDOW_WIDTH // 2, HEADER_HEIGHT // 2))
        surface.blit(turn_text, turn_rect)

        # Draw round counter
        round_text = self.font.render(f"Round {self.round}", True, BLACK)
        round_rect = round_text.get_rect(
            midright=(WINDOW_WIDTH - 20, HEADER_HEIGHT // 2)
        )
        surface.blit(round_text, round_rect)

        # Draw reveal message if active
        if self.reveal_message and self.reveal_message_start:
            current_time = pygame.time.get_ticks()
            if current_time - self.reveal_message_start < self.reveal_message_duration:
                alpha = 255
                if (
                    current_time - self.reveal_message_start
                    > self.reveal_message_duration - 500
                ):
                    # Fade out in last 500ms
                    alpha = int(
                        255
                        * (
                            1
                            - (
                                current_time
                                - (
                                    self.reveal_message_start
                                    + self.reveal_message_duration
                                    - 500
                                )
                            )
                            / 500
                        )
                    )

                reveal_text = self.font.render(
                    self.reveal_message, True, (255, 215, 0)
                )  # Golden color
                reveal_text.set_alpha(alpha)
                reveal_rect = reveal_text.get_rect(
                    center=(WINDOW_WIDTH // 2, HEADER_HEIGHT + 20)
                )
                surface.blit(reveal_text, reveal_rect)
            else:
                self.reveal_message = None
                self.reveal_message_start = None

    def set_game_over(self, winner):
        self.game_over = True
        self.winner = winner
        self.current_turn = f"{winner} WINS!"

    def show_reveal_message(self, is_player_revealed):
        self.reveal_message = (
            "Computer's Cards Revealed!"
            if not is_player_revealed
            else "Your Cards Revealed!"
        )
        self.reveal_message_start = pygame.time.get_ticks()


class ComputerPlayer:
    def __init__(self, hand, play_area, scoreboard):
        self.hand = hand
        self.play_area = play_area
        self.scoreboard = scoreboard
        self.card_backs = []
        self.animating_new_card = False
        self.animation_start = None
        self.animation_duration = 500  # milliseconds
        self.animation_start_pos = None
        self.animation_end_pos = None
        self.update_card_backs()
        self.glow_effect = 0
        self.glow_speed = 0.1

    def update_card_backs(self):
        # Clear existing card backs
        self.card_backs = []
        # Load and create card back images for display
        card_back_img = pygame.image.load(
            os.path.join("Cards (large)", "card_back.png")
        )
        card_back_img = pygame.transform.scale(card_back_img, (CARD_WIDTH, CARD_HEIGHT))

        # Position the card backs in the top dock
        dock_start_x = (
            WINDOW_WIDTH
            - (CARD_WIDTH * len(self.hand) + CARD_SPACING * (len(self.hand) - 1))
        ) // 2
        dock_y = 10 + HEADER_HEIGHT  # Just below header

        for i in range(len(self.hand)):
            card_back = {
                "image": card_back_img,
                "rect": pygame.Rect(
                    dock_start_x + i * (CARD_WIDTH + CARD_SPACING),
                    dock_y,
                    CARD_WIDTH,
                    CARD_HEIGHT,
                ),
            }
            self.card_backs.append(card_back)

    def add_card(self, card):
        self.hand.append(card)
        # Calculate the position for the new card back
        dock_start_x = (
            WINDOW_WIDTH
            - (CARD_WIDTH * len(self.hand) + CARD_SPACING * (len(self.hand) - 1))
        ) // 2
        dock_y = 10 + HEADER_HEIGHT
        new_pos = (
            dock_start_x + (len(self.hand) - 1) * (CARD_WIDTH + CARD_SPACING),
            dock_y,
        )

        # Start animation
        self.animating_new_card = True
        self.animation_start = pygame.time.get_ticks()
        self.animation_start_pos = (new_pos[0], -CARD_HEIGHT)  # Start above screen
        self.animation_end_pos = new_pos

        # Update all card backs
        self.update_card_backs()

    def play_card(self):
        # Safety check to prevent crashes
        if not self.hand:
            return None

        # Choose a random card from hand
        chosen_card = random.choice(self.hand)

        # Remove the card from hand
        self.hand.remove(chosen_card)

        # Update the card backs display
        self.update_card_backs()

        # Add the card to the play area
        if chosen_card:
            self.play_area.add_card(chosen_card)

        return chosen_card

    def update_animation(self):
        if not self.animating_new_card:
            return

        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.animation_start

        if elapsed >= self.animation_duration:
            self.animating_new_card = False
            return

        # Calculate position using easing function
        progress = elapsed / self.animation_duration
        # Ease out cubic function
        progress = 1 - (1 - progress) ** 3

        # Only animate the last card back
        if self.card_backs:
            last_card = self.card_backs[-1]
            x = self.animation_start_pos[0]
            y = (
                self.animation_start_pos[1]
                + (self.animation_end_pos[1] - self.animation_start_pos[1]) * progress
            )
            last_card["rect"].topleft = (x, y)

    def draw(self, surface):
        print(f"Reveal status: {self.scoreboard.reveal_computer_cards}")  # Debug print
        if self.scoreboard.reveal_computer_cards:
            print(f"Drawing revealed cards. Hand size: {len(self.hand)}")  # Debug print
            # Draw actual cards with glow effect
            self.glow_effect = (self.glow_effect + self.glow_speed) % (2 * math.pi)
            glow_intensity = (math.sin(self.glow_effect) + 1) / 2  # 0 to 1

            for i, card in enumerate(self.hand):
                # Draw glow effect
                glow_surf = pygame.Surface(
                    (CARD_WIDTH + 20, CARD_HEIGHT + 20), pygame.SRCALPHA
                )
                pygame.draw.rect(
                    glow_surf,
                    (0, 255, 0, int(128 * glow_intensity)),
                    glow_surf.get_rect(),
                    border_radius=10,
                )

                if i < len(self.card_backs):
                    card_rect = self.card_backs[i]["rect"]
                    # Draw glow
                    glow_rect = glow_surf.get_rect(center=card_rect.center)
                    surface.blit(glow_surf, glow_rect)

                    # Draw actual card
                    surface.blit(card.image, card_rect)
                    print(f"Drew card {i}: {card.suit}_{card.value}")  # Debug print
        else:
            # Original drawing code for card backs
            for i, card_back in enumerate(self.card_backs):
                if not (self.animating_new_card and i == len(self.card_backs) - 1):
                    surface.blit(card_back["image"], card_back["rect"])

            if self.animating_new_card and self.card_backs:
                surface.blit(self.card_backs[-1]["image"], self.card_backs[-1]["rect"])


class ScoreBoard:
    def __init__(self):
        self.player_score = 0
        self.computer_score = 0
        self.player_wins = []  # List of winning cards (small versions)
        self.computer_wins = []
        self.player_win_history = []  # List of (card, timestamp) tuples
        self.computer_win_history = []
        self.reveal_player_cards = False
        self.reveal_computer_cards = False
        self.reveal_effect_start = None
        self.reveal_effect_duration = 2000  # 2 seconds for flash effect
        self.load_small_cards()
        self.current_round = 1  # Add this to track rounds
        self.reveal_started_round = None  # Add this to track when reveal started

    def check_matching_wins(self, win_history):
        if len(win_history) < 2:
            return False

        last_two_wins = win_history[-2:]
        card1, _ = last_two_wins[-1]
        card2, _ = last_two_wins[-2]

        # Print debug info
        print(
            f"Checking cards: {card1.suit}_{card1.value} vs {card2.suit}_{card2.value}"
        )

        # Check for matching suit or value
        matches = card1.suit == card2.suit or card1.value == card2.value
        if matches:
            print("Found a match!")
        return matches

    def compare_cards(self, player_card, computer_card):
        # Check for exact same card (draw)
        if (
            player_card.suit == computer_card.suit
            and player_card.value == computer_card.value
        ):
            return None  # Return None to indicate a draw

        # Define the winning relationships
        beats = {"diamonds": "spades", "spades": "hearts", "hearts": "diamonds"}

        if player_card.suit == computer_card.suit:
            # Same suit, compare values
            return player_card.value > computer_card.value
        else:
            # Different suits, check if player's card beats computer's card
            return beats[player_card.suit] == computer_card.suit

    def update_reveal_effect(self):
        if self.reveal_effect_start is not None:
            current_time = pygame.time.get_ticks()
            # Only reset the reveal effect start time, but keep the reveal flags
            if current_time - self.reveal_effect_start > self.reveal_effect_duration:
                print("Resetting reveal effect start time")  # Debug print
                self.reveal_effect_start = None

    def new_round(self):
        print(f"Starting new round {self.current_round + 1}")
        print(
            "Current reveal flags:",
            self.reveal_player_cards,
            self.reveal_computer_cards,
        )

        # Only reset reveal flags if they've been active for one full round
        if (
            self.reveal_player_cards or self.reveal_computer_cards
        ) and self.reveal_started_round is not None:
            if self.current_round > self.reveal_started_round:
                print("Resetting reveal flags after one round")
                self.reveal_player_cards = False
                self.reveal_computer_cards = False
                self.reveal_started_round = None

        self.current_round += 1

    def add_win(self, winning_card, is_player_win, header):
        card_key = f"{winning_card.suit}_{winning_card.value}"
        timestamp = pygame.time.get_ticks()

        if is_player_win:
            self.player_score += 1
            self.player_wins.append(self.small_card_images[card_key])
            self.player_win_history.append((winning_card, timestamp))
            # Check if player's last two wins match
            if self.check_matching_wins(self.player_win_history):
                print("Player matched! Revealing computer cards")  # Debug print
                self.reveal_computer_cards = True
                self.reveal_effect_start = timestamp
                self.reveal_started_round = (
                    self.current_round
                )  # Track when reveal started
                header.show_reveal_message(False)
                print(
                    f"Set reveal_computer_cards to {self.reveal_computer_cards}"
                )  # Debug print
        else:
            self.computer_score += 1
            self.computer_wins.append(self.small_card_images[card_key])
            self.computer_win_history.append((winning_card, timestamp))
            # Check if computer's last two wins match
            if self.check_matching_wins(self.computer_win_history):
                print("Computer matched! Revealing player cards")  # Debug print
                self.reveal_player_cards = True
                self.reveal_effect_start = timestamp
                self.reveal_started_round = (
                    self.current_round
                )  # Track when reveal started
                header.show_reveal_message(True)
                print(
                    f"Set reveal_player_cards to {self.reveal_player_cards}"
                )  # Debug print

    def load_small_cards(self):
        self.small_card_images = {}
        small_cards_path = "Cards (small)"
        for suit in ["hearts", "diamonds", "spades"]:
            for value in range(2, 11):
                filename = f"card_{suit}_{str(value).zfill(2)}.png"
                path = os.path.join(small_cards_path, filename)
                img = pygame.image.load(path)
                img = pygame.transform.scale(img, (SMALL_CARD_WIDTH, SMALL_CARD_HEIGHT))
                self.small_card_images[f"{suit}_{value}"] = img

    def draw(self, surface):
        # Draw player's winning cards on the left
        for i, card_img in enumerate(self.player_wins):
            x = 20 + (i * (SMALL_CARD_WIDTH + 5))
            y = HEADER_HEIGHT + 20
            surface.blit(card_img, (x, y))

        # Draw computer's winning cards on the right
        for i, card_img in enumerate(self.computer_wins):
            x = WINDOW_WIDTH - 20 - SMALL_CARD_WIDTH - (i * (SMALL_CARD_WIDTH + 5))
            y = HEADER_HEIGHT + 20
            surface.blit(card_img, (x, y))


class Confetti:
    def __init__(self):
        self.particles = []
        self.colors = [
            (255, 215, 0),
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 192, 203),
        ]

    def create_particles(self):
        self.particles = []
        for _ in range(CONFETTI_COUNT):
            x = random.randint(0, WINDOW_WIDTH)
            y = random.randint(-WINDOW_HEIGHT, 0)
            color = random.choice(self.colors)
            speed = random.uniform(2, 5)
            size = random.randint(5, 10)
            self.particles.append(
                {
                    "pos": [x, y],
                    "speed": speed,
                    "size": size,
                    "color": color,
                    "angle": random.uniform(0, 360),
                }
            )

    def update(self):
        for p in self.particles:
            p["pos"][1] += p["speed"]
            p["angle"] += VICTORY_CARD_SPIN_SPEED
            if p["pos"][1] > WINDOW_HEIGHT:
                p["pos"][1] = random.randint(-50, 0)
                p["pos"][0] = random.randint(0, WINDOW_WIDTH)

    def draw(self, surface):
        for p in self.particles:
            rect = pygame.Rect(p["pos"][0], p["pos"][1], p["size"], p["size"])
            pygame.draw.rect(surface, p["color"], rect)


class EndScreen:
    def __init__(self):
        self.font_large = pygame.font.Font(None, 74)
        self.font_medium = pygame.font.Font(None, 48)
        self.alpha = 0
        self.surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.surface.set_alpha(self.alpha)
        self.animation_start = None
        self.confetti = Confetti()
        self.replay_button = ReplayButton(
            WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 50, 200, 50
        )

    def start_animation(self):
        self.animation_start = pygame.time.get_ticks()
        self.confetti.create_particles()

    def update(self):
        if self.animation_start is None:
            return

        elapsed = pygame.time.get_ticks() - self.animation_start
        if elapsed < END_SCREEN_ANIMATION_DURATION:
            self.alpha = int((elapsed / END_SCREEN_ANIMATION_DURATION) * 255)
        else:
            self.alpha = 255

        self.confetti.update()

    def draw(self, surface, winner, player_score, computer_score):
        # Draw semi-transparent background
        self.surface.fill((0, 0, 0))
        self.surface.set_alpha(min(160, self.alpha))
        surface.blit(self.surface, (0, 0))

        # Draw victory text
        winner_text = self.font_large.render(f"{winner} WINS!", True, (255, 215, 0))
        score_text = self.font_medium.render(
            f"Final Score: {player_score} - {computer_score}", True, WHITE
        )

        # Calculate positions
        winner_pos = winner_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50)
        )
        score_pos = score_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10)
        )

        # Apply fade-in effect to text
        winner_text.set_alpha(self.alpha)
        score_text.set_alpha(self.alpha)

        # Draw confetti
        self.confetti.draw(surface)

        # Draw text
        surface.blit(winner_text, winner_pos)
        surface.blit(score_text, score_pos)

        # Draw replay button
        self.replay_button.draw(surface)

    def handle_event(self, event):
        return self.replay_button.handle_event(event)


class ReplayButton:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 36)
        self.color = (50, 205, 50)
        self.hover = False

    def draw(self, surface):
        color = (60, 235, 60) if self.hover else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)

        text = self.font.render("Play Again", True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class TitleScreen:
    def __init__(self):
        self.font_title = pygame.font.Font(None, 100)
        self.font_info = pygame.font.Font(None, 36)
        self.background_color = (135, 206, 235)
        self.title_color = (255, 215, 0)

        # Create buttons for different game modes
        button_width = 400
        button_height = 60
        button_spacing = 20
        start_y = WINDOW_HEIGHT // 2 + 50

        # Center all buttons horizontally
        center_x = WINDOW_WIDTH // 2 - button_width // 2

        self.singleplayer_button = StartButton(
            center_x, start_y, button_width, button_height, "VS COMPUTER"
        )

        self.multiplayer_button = StartButton(
            center_x,
            start_y + button_height + button_spacing,
            button_width,
            button_height,
            "PLAY ONLINE",
        )

        self.info_button = InfoButton(WINDOW_WIDTH - 50, 20, 30, 30)
        self.show_info = False
        self.info_popup = InfoPopup()

    def draw(self, surface):
        # Fill background
        surface.fill(self.background_color)

        # Draw title
        title_text = self.font_title.render("Poker-jitsu!", True, self.title_color)
        title_shadow = self.font_title.render("Poker-jitsu!", True, BLACK)

        # Position for title
        title_pos = title_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50)
        )

        # Draw shadow slightly offset
        shadow_pos = title_pos.copy()
        shadow_pos.x += 3
        shadow_pos.y += 3
        surface.blit(title_shadow, shadow_pos)

        # Draw main title
        surface.blit(title_text, title_pos)

        # Draw buttons
        self.singleplayer_button.draw(surface)
        self.multiplayer_button.draw(surface)
        self.info_button.draw(surface)

        # Draw info popup if active
        if self.show_info:
            self.info_popup.draw(surface)

    def handle_event(self, event):
        if self.show_info:
            if self.info_popup.handle_event(event):
                self.show_info = False
                return None
        else:
            if self.info_button.handle_event(event):
                self.show_info = True
                return None

            # Check which button was clicked
            if self.singleplayer_button.handle_event(event):
                return "singleplayer"
            if self.multiplayer_button.handle_event(event):
                return "multiplayer"
        return None


class StartButton:
    def __init__(self, x, y, width, height, text="START"):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 48)
        self.color = (50, 205, 50)  # Green
        self.hover = False
        self.text = text

    def draw(self, surface):
        color = (60, 235, 60) if self.hover else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)

        text = self.font.render(self.text, True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class InfoButton:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 36)
        self.color = (50, 205, 50)
        self.hover = False

    def draw(self, surface):
        # Draw circle background
        color = (60, 235, 60) if self.hover else self.color
        pygame.draw.circle(surface, color, self.rect.center, self.rect.width // 2)
        pygame.draw.circle(surface, BLACK, self.rect.center, self.rect.width // 2, 2)

        # Draw "i" text
        text = self.font.render("i", True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class InfoPopup:
    def __init__(self):
        self.width = 600
        self.height = 550
        self.rect = pygame.Rect(
            (WINDOW_WIDTH - self.width) // 2,
            (WINDOW_HEIGHT - self.height) // 2,
            self.width,
            self.height,
        )
        self.font_title = pygame.font.Font(None, 36)
        self.font_text = pygame.font.Font(None, 24)
        self.close_button = pygame.Rect(
            self.rect.right - 40, self.rect.top + 10, 30, 30
        )

        # Game instructions text
        self.instructions = [
            "Welcome to Poker-jitsu!",
            "",
            "Game Rules:",
            "- Each player starts with 5 cards",
            "- Players take turns playing one card at a time",
            "- Cards follow a rock-paper-scissors style system:",
            "  • Diamonds beat Spades",
            "  • Spades beat Hearts",
            "  • Hearts beat Diamonds",
            "",
            "- If both players play the same suit, the higher number wins",
            "",
            "- First player to win 4 rounds wins the game!",
        ]

    def draw(self, surface):
        # Draw semi-transparent background
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        surface.blit(overlay, (0, 0))

        # Draw popup background
        pygame.draw.rect(surface, WHITE, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)

        # Draw close button
        pygame.draw.rect(surface, (255, 100, 100), self.close_button)
        pygame.draw.rect(surface, BLACK, self.close_button, 2)
        close_text = self.font_text.render("X", True, BLACK)
        close_rect = close_text.get_rect(center=self.close_button.center)
        surface.blit(close_text, close_rect)

        # Draw instructions text
        y_offset = self.rect.top + 20
        for line in self.instructions:
            if line.startswith("Welcome"):
                text = self.font_title.render(line, True, BLACK)
                y_offset += 10
            else:
                text = self.font_text.render(line, True, BLACK)
            text_rect = text.get_rect(x=self.rect.left + 20, y=y_offset)
            surface.blit(text, text_rect)
            y_offset += 30

        # Draw instruction image
        img_rect = instructions_img.get_rect()
        img_rect.centerx = self.rect.centerx
        img_rect.bottom = self.rect.bottom - 10
        surface.blit(instructions_img, img_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if clicked outside popup or on close button
            if not self.rect.collidepoint(event.pos) or self.close_button.collidepoint(
                event.pos
            ):
                return True
        return False


class PlayerLoginScreen:
    def __init__(self):
        self.font_title = pygame.font.Font(None, 64)
        self.font_text = pygame.font.Font(None, 36)
        self.background_color = (135, 206, 235)
        self.input_box = pygame.Rect(
            WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2, 200, 32
        )
        self.color_inactive = pygame.Color("lightskyblue3")
        self.color_active = pygame.Color("dodgerblue2")
        self.color = self.color_inactive
        self.text = ""
        self.active = False
        self.done = False

        # Create join button
        self.join_button = StartButton(
            WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 50, 200, 50, "JOIN GAME"
        )
        self.join_button.active = False  # Disable until name is entered

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.input_box.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive

            # Check if join button is clicked
            if self.join_button.active and self.join_button.handle_event(event):
                return self.text  # Return the player's name

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN and self.text.strip():
                    return self.text
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    # Only allow reasonable name lengths
                    if len(self.text) < 12:
                        self.text += event.unicode

                # Enable join button if text is not empty
                self.join_button.active = bool(self.text.strip())

        return None

    def draw(self, screen):
        screen.fill(self.background_color)

        # Draw title
        title_text = self.font_title.render("Enter Your Name", True, (255, 215, 0))
        title_rect = title_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100)
        )
        screen.blit(title_text, title_rect)

        # Draw input box
        txt_surface = self.font_text.render(self.text, True, self.color)
        width = max(200, txt_surface.get_width() + 10)
        self.input_box.w = width
        self.input_box.centerx = WINDOW_WIDTH // 2
        pygame.draw.rect(screen, self.color, self.input_box, 2)
        screen.blit(txt_surface, (self.input_box.x + 5, self.input_box.y + 5))

        # Draw join button
        self.join_button.draw(screen)


class WaitingScreen:
    def __init__(self, player_name):
        self.font_title = pygame.font.Font(None, 64)
        self.font_text = pygame.font.Font(None, 36)
        self.background_color = (135, 206, 235)
        self.player_name = player_name
        self.dots = ""
        self.dot_timer = 0

    def update(self):
        self.dot_timer += 1
        if self.dot_timer > 30:  # Update dots every half second
            self.dots = "." * ((len(self.dots) + 1) % 4)
            self.dot_timer = 0

    def draw(self, screen):
        screen.fill(self.background_color)

        # Draw welcome message
        welcome_text = self.font_title.render(
            f"Welcome, {self.player_name}!", True, (255, 215, 0)
        )
        welcome_rect = welcome_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100)
        )
        screen.blit(welcome_text, welcome_rect)

        # Draw waiting message with animated dots
        waiting_text = self.font_text.render(
            f"Waiting for opponent{self.dots}", True, BLACK
        )
        waiting_rect = waiting_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        )
        screen.blit(waiting_text, waiting_rect)


class LobbyScreen:
    def __init__(self, player_name, network):
        self.font_title = pygame.font.Font(None, 64)
        self.font_text = pygame.font.Font(None, 36)
        self.background_color = (135, 206, 235)
        self.player_name = player_name
        self.network = network
        self.status_message = "Connecting to server..."
        self.dots = ""
        self.dot_timer = 0
        self.connection_status = "connecting"  # connecting, waiting, matched, error

    def update(self):
        self.dot_timer += 1
        if self.dot_timer > 30:
            self.dots = "." * ((len(self.dots) + 1) % 4)
            self.dot_timer = 0

        # Check server status
        try:
            response = self.network.send("get_status")
            print(f"Lobby update response: {response}")  # Debug print

            if response:
                if response.get("status") == "waiting":
                    self.connection_status = "waiting"
                    self.status_message = "Waiting for opponent"
                    return False
                elif response.get("status") in [
                    "starting",
                    "game_started",
                    "in_game",
                ]:  # Add these conditions
                    print("Game is starting!")  # Debug print
                    print(f"Game data received: {response}")  # Debug print
                    self.connection_status = "matched"
                    self.status_message = "Opponent found! Starting game..."
                    # Store game data
                    if "game_id" in response:
                        self.network.game_id = response["game_id"]
                    if "player_num" in response:
                        self.network.player_num = response["player_num"]
                    if "game_state" in response:
                        self.network.game_state = response["game_state"]
                    return True

            if not self.network.connected:
                print("Lost connection to server")  # Debug print
                self.connection_status = "error"
                self.status_message = "Lost connection to server"
                return False

        except Exception as e:
            print(f"Network error in lobby: {e}")
            self.network.connected = False
            self.connection_status = "error"
            self.status_message = "Connection error"
            return False

        return False

    def draw(self, screen):
        screen.fill(self.background_color)

        # Draw title
        title_text = self.font_title.render("Game Lobby", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4))
        screen.blit(title_text, title_rect)

        # Draw player name
        name_text = self.font_text.render(f"Player: {self.player_name}", True, BLACK)
        name_rect = name_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50)
        )
        screen.blit(name_text, name_rect)

        # Draw status message with dots
        status_text = self.font_text.render(
            f"{self.status_message}{self.dots}", True, BLACK
        )
        status_rect = status_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50)
        )
        screen.blit(status_text, status_rect)


def start_game():
    # Create and shuffle the decks
    player_deck, computer_deck = create_deck()

    # Deal cards to both players from their respective decks
    player_hand = deal_cards(player_deck, 5)
    computer_hand = deal_cards(computer_deck, 5)

    # Remove dealt cards from decks
    for card in player_hand:
        player_deck.remove(card)
    for card in computer_hand:
        computer_deck.remove(card)

    # Create the play areas
    player_play_area = PlayArea(
        50, WINDOW_HEIGHT // 2 - CARD_HEIGHT // 2, CARD_WIDTH + 20, CARD_HEIGHT + 20
    )
    computer_play_area = PlayArea(
        WINDOW_WIDTH - CARD_WIDTH - 70,
        WINDOW_HEIGHT // 2 - CARD_HEIGHT // 2,
        CARD_WIDTH + 20,
        CARD_HEIGHT + 20,
    )

    # Create the scoreboard first
    scoreboard = ScoreBoard()

    # Create the computer player with scoreboard
    computer = ComputerPlayer(computer_hand, computer_play_area, scoreboard)

    # Create the GO button
    go_button = Button(
        WINDOW_WIDTH - 120, WINDOW_HEIGHT - 70, BUTTON_WIDTH, BUTTON_HEIGHT
    )

    # Create the header
    header = Header()

    # Create end screen
    end_screen = EndScreen()
    end_screen_started = False

    # Position the player's cards in the dock
    dock_start_x = (
        WINDOW_WIDTH
        - (CARD_WIDTH * len(player_hand) + CARD_SPACING * (len(player_hand) - 1))
    ) // 2
    dock_y = WINDOW_HEIGHT - DOCK_HEIGHT + 25

    for i, card in enumerate(player_hand):
        card.set_position(dock_start_x + i * (CARD_WIDTH + CARD_SPACING), dock_y)

    running = True
    clock = pygame.time.Clock()
    computer_play_time = None
    resolving_round = False
    resolution_start_time = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if header.game_over:
                if end_screen.handle_event(event):
                    return main()  # Restart the game
            elif header.is_player_turn and not resolving_round:
                # Handle card dragging during player's turn
                for card in player_hand:
                    card.handle_event(event, player_play_area, go_button)

                # Handle GO button click
                if event.type == pygame.MOUSEBUTTONDOWN and go_button.active:
                    if go_button.rect.collidepoint(event.pos):
                        header.switch_turn()
                        go_button.active = False

        # Check if timer expired
        if header.update() and not resolving_round:
            if header.is_player_turn and player_play_area.card:
                header.switch_turn()
                go_button.active = False
            elif header.is_player_turn:
                if player_play_area.card:
                    player_play_area.card.rect.x, player_play_area.card.rect.y = (
                        player_play_area.card.original_pos
                    )
                    player_play_area.remove_card()

        # Handle computer's turn
        if not header.game_over and not header.is_player_turn and not resolving_round:
            if computer_play_time is None:
                computer_play_time = pygame.time.get_ticks() + COMPUTER_TURN_DELAY
            elif pygame.time.get_ticks() >= computer_play_time:
                computer.play_card()
                resolving_round = True
                resolution_start_time = pygame.time.get_ticks()

        # Handle round resolution
        if resolving_round:
            current_time = pygame.time.get_ticks()

            # First phase: Show winner highlight
            if current_time - resolution_start_time < COMPARISON_PAUSE:
                # Compare cards and highlight winner
                player_card = player_play_area.card
                computer_card = computer_play_area.card

                player_wins = scoreboard.compare_cards(player_card, computer_card)

                # Highlight winner's play area (no highlight for draws)
                if player_wins is not None:  # Only highlight if not a draw
                    player_play_area.highlight = player_wins
                    computer_play_area.highlight = not player_wins

            # Second phase: Process round end and deal new cards
            elif current_time - resolution_start_time >= COMPARISON_PAUSE:
                player_card = player_play_area.card
                computer_card = computer_play_area.card

                player_wins = scoreboard.compare_cards(player_card, computer_card)

                # Add winning card to score display (skip if draw)
                if player_wins is not None:  # Only add win if not a draw
                    if player_wins:
                        scoreboard.add_win(player_card, True, header)
                    else:
                        scoreboard.add_win(computer_card, False, header)

                # Check if game is over
                if scoreboard.player_score >= 4:
                    header.set_game_over("PLAYER")
                elif scoreboard.computer_score >= 4:
                    header.set_game_over("COMPUTER")

                # Remove the played card from player's hand
                if player_card in player_hand:
                    player_hand.remove(player_card)

                # Clear play areas
                player_play_area.remove_card()
                computer_play_area.remove_card()

                # Only continue with next round if game isn't over
                if not header.game_over:
                    # Calculate how many cards need to be dealt to player
                    cards_needed = 5 - len(player_hand)

                    # Deal new cards if there are cards left in the deck
                    if len(player_deck) > 0 and cards_needed > 0:
                        # Deal to player from player deck
                        new_player_cards = deal_cards(
                            player_deck, min(cards_needed, len(player_deck))
                        )
                        player_hand.extend(new_player_cards)

                        # Deal to computer from computer deck
                        if len(computer_deck) > 0:
                            new_computer_card = deal_cards(computer_deck, 1)[0]
                            computer.add_card(new_computer_card)
                    # Reposition all player cards including the new ones
                    dock_start_x = (
                        WINDOW_WIDTH
                        - (CARD_WIDTH * len(player_hand) + CARD_SPACING * (len(player_hand) - 1))
                    ) // 2
                    dock_y = WINDOW_HEIGHT - DOCK_HEIGHT + 25

                    for i, card in enumerate(player_hand):
                        target_pos = (
                            dock_start_x + i * (CARD_WIDTH + CARD_SPACING),
                            dock_y,
                        )
                        if card in new_player_cards:  # If it's a new card, animate it
                            card.start_deal_animation(target_pos)
                        else:  # Otherwise just reposition it
                            card.set_position(*target_pos)
                            card.original_pos = target_pos

                    # Update round counter
                    header.round += 1

                    # Just call new_round without any additional tracking
                    scoreboard.new_round()

                # Reset for next round
                resolving_round = False
                computer_play_time = None
                player_play_area.highlight = False
                computer_play_area.highlight = False
                if not header.game_over:
                    header.switch_turn()

        # Update animations
        for card in player_hand:
            card.update_animation()
        computer.update_animation()

        # Handle end screen
        if header.game_over and not end_screen_started:
            end_screen_started = True
            end_screen.start_animation()

        if header.game_over:
            end_screen.update()

        # Draw everything
        draw_game_board()

        # Draw instructions image in center
        screen.blit(instructions_img, instructions_rect)

        # Find the currently dragged card (if any)
        dragged_card = None
        for card in player_hand:
            if card.dragging:
                dragged_card = card
                break

        # Draw non-dragged player cards
        for card in player_hand:
            if not card.dragging:
                card.draw(screen)

        # Draw computer's cards (backs)
        computer.draw(screen)

        # Draw play areas and their cards
        player_play_area.draw(screen)
        computer_play_area.draw(screen)

        # Draw the dragged card last (on top)
        if dragged_card:
            dragged_card.draw(screen)

        # Draw the GO button
        go_button.draw(screen)

        # Draw the header
        header.draw(screen)

        # Draw the scoreboard
        scoreboard.draw(screen)

        # Draw end screen if game is over
        if header.game_over:
            end_screen.draw(
                screen,
                header.winner,
                scoreboard.player_score,
                scoreboard.computer_score,
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


def start_online_game():
    # Show login screen first
    login_screen = PlayerLoginScreen()
    player_name = None
    running = True
    clock = pygame.time.Clock()

    # Get player name
    while running and player_name is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            result = login_screen.handle_event(event)
            if result:
                player_name = result

        login_screen.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    if player_name and running:
        network = NetworkGame()
        if network.connect():
            # Send player name to server
            network.send(player_name)

            # Enter lobby
            lobby = LobbyScreen(player_name, network)
            in_lobby = True

            while running and in_lobby:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                # Update lobby and check for game start
                if lobby.update():
                    in_lobby = False
                    # Start multiplayer game
                    start_multiplayer_game(network, player_name)

                lobby.draw(screen)
                pygame.display.flip()
                clock.tick(60)
        else:
            print("Failed to connect to server")


def start_multiplayer_game(network, player_name):
    try:
        # Wait for game start confirmation
        response = network.send("ready")
        print(f"Waiting for game start confirmation... Response: {response}")  # Debug print
        
        # Modified this check to accept both "game_started" and "in_game" status
        if not response or (response.get("status") not in ["game_started", "in_game"]):
            print(f"Failed to start game. Status: {response.get('status') if response else 'No response'}")
            return

        # Create play areas
        player_play_area = PlayArea(
            50, WINDOW_HEIGHT // 2 - CARD_HEIGHT // 2, CARD_WIDTH + 20, CARD_HEIGHT + 20
        )
        opponent_play_area = PlayArea(
            WINDOW_WIDTH - CARD_WIDTH - 70,
            WINDOW_HEIGHT // 2 - CARD_HEIGHT // 2,
            CARD_WIDTH + 20,
            CARD_HEIGHT + 20,
        )

        # Create the scoreboard
        scoreboard = ScoreBoard()

        # Create the GO button
        go_button = Button(
            WINDOW_WIDTH - 120, WINDOW_HEIGHT - 70, BUTTON_WIDTH, BUTTON_HEIGHT
        )

        # Get initial game state
        game_state = network.game_state
        if not game_state:
            print("No initial game state received")
            return
            
        print(f"Initial game state: {game_state}")  # Debug print
        print(f"Player number: {network.player_num}")  # Debug print

        # Set up initial turn based on server's choice
        is_my_turn = game_state["current_turn"] == player_name
        if network.player_num == 1:
            opponent_name = game_state["player2"]["name"]
        else:
            opponent_name = game_state["player1"]["name"]
        print(f"My name: {player_name}, Opponent name: {opponent_name}")

        # Create the header
        header = Header()
        header.is_player_turn = is_my_turn
        header.current_turn = "YOUR TURN" if is_my_turn else f"{opponent_name}'s TURN"

        # Create player hand from server data
        player_hand = []
        if network.player_num == 1:
            hand_data = game_state["player1"]["hand"]
        else:
            hand_data = game_state["player2"]["hand"]

        # Convert server card data to Card objects
        for suit, value in hand_data:
            image_path = os.path.join("Cards (large)", f"card_{suit}_{str(value).zfill(2)}.png")
            card = Card(suit, value, image_path)
            player_hand.append(card)

        # Position cards
        dock_start_x = (
            WINDOW_WIDTH
            - (CARD_WIDTH * len(player_hand) + CARD_SPACING * (len(player_hand) - 1))
        ) // 2
        dock_y = WINDOW_HEIGHT - DOCK_HEIGHT + 25

        for i, card in enumerate(player_hand):
            card.set_position(dock_start_x + i * (CARD_WIDTH + CARD_SPACING), dock_y)

        # Initialize timer
        turn_timer = TIMER_DURATION
        last_timer_update = pygame.time.get_ticks()
        dragged_card = None  # Initialize dragged_card

        running = True
        clock = pygame.time.Clock()

        # Load face-down card image
        card_back_image = pygame.image.load(
            os.path.join("Cards (large)", "card_back.png")
        )
        card_back_image = pygame.transform.scale(
            card_back_image, (CARD_WIDTH, CARD_HEIGHT)
        )

        while running:
            current_time = pygame.time.get_ticks()

            # Update game state
            try:
                updated_state = network.send("get_state")
                if updated_state and isinstance(updated_state, dict):
                    if updated_state.get("status") == "in_game":
                        new_state = updated_state.get("game_state", game_state)

                        # Check if opponent played a card
                        opponent_played_card = None
                        if network.player_num == 1:
                            opponent_played_card = new_state["player2"]["played_card"]
                        else:
                            opponent_played_card = new_state["player1"]["played_card"]

                        # Update opponent's play area if they played a card
                        if opponent_played_card and not opponent_play_area.card:
                            # Create a face-down card initially
                            face_down_card = Card(
                                "back",
                                0,
                                os.path.join("Cards (large)", "card_back.png"),
                            )
                            opponent_play_area.add_card(face_down_card)
                            print("Showing opponent's face-down card")

                        # Check if both players have played
                        both_played = (
                            new_state["player1"]["played_card"] is not None
                            and new_state["player2"]["played_card"] is not None
                        )

                        if both_played:
                            # Get opponent's actual card and reveal it
                            if network.player_num == 1:
                                opp_card = new_state["player2"]["played_card"]
                            else:
                                opp_card = new_state["player1"]["played_card"]

                            # Show actual card immediately when both have played
                            if opp_card:
                                opp_card_obj = Card(
                                    opp_card[0],
                                    opp_card[1],
                                    os.path.join(
                                        "Cards (large)",
                                        f"card_{opp_card[0]}_{str(opp_card[1]).zfill(2)}.png",
                                    ),
                                )
                                opponent_play_area.add_card(opp_card_obj)
                                print("Revealing opponent's actual card for comparison")

                            # Handle round result and winner display
                            if new_state.get("round_result") and new_state["round_result"] != game_state.get("round_result"):
                                round_result = new_state["round_result"]
                                winner = round_result["winner"]
                                
                                print(f"Processing round result. Winner: {winner}")  # Debug print
                                
                                # Update play area highlights
                                if network.player_num == 1:
                                    player_play_area.highlight = winner == "player1"
                                    opponent_play_area.highlight = winner == "player2"
                                else:
                                    player_play_area.highlight = winner == "player2"
                                    opponent_play_area.highlight = winner == "player1"
                                
                                # Update scoreboard with winning card
                                if (network.player_num == 1 and winner == "player1") or (network.player_num == 2 and winner == "player2"):
                                    winning_card = player_play_area.card
                                    scoreboard.add_win(winning_card, True, header)
                                    print("Added winning card to player's scoreboard")
                                else:
                                    winning_card = opponent_play_area.card
                                    scoreboard.add_win(winning_card, False, header)
                                    print("Added winning card to opponent's scoreboard")
                                
                                # Show comparison for a moment
                                pygame.time.wait(COMPARISON_PAUSE)
                                print("Comparison pause complete")
                                
                                # Clear play areas and reset highlights
                                player_play_area.remove_card()
                                opponent_play_area.remove_card()
                                player_play_area.highlight = False
                                opponent_play_area.highlight = False
                                
                                # Update round counter
                                header.round = new_state.get("round", 1)
                                
                                # Update player's hand with new cards
                                if network.player_num == 1:
                                    hand_data = new_state["player1"]["hand"]
                                else:
                                    hand_data = new_state["player2"]["hand"]
                                
                                # Convert new hand data to Card objects and position them
                                player_hand = []
                                for suit, value in hand_data:
                                    image_path = os.path.join("Cards (large)", f"card_{suit}_{str(value).zfill(2)}.png")
                                    card = Card(suit, value, image_path)
                                    player_hand.append(card)
                                
                                # Position new cards
                                dock_start_x = (WINDOW_WIDTH - (CARD_WIDTH * len(player_hand) + CARD_SPACING * (len(player_hand) - 1))) // 2
                                dock_y = WINDOW_HEIGHT - DOCK_HEIGHT + 25
                                
                                for i, card in enumerate(player_hand):
                                    card.set_position(dock_start_x + i * (CARD_WIDTH + CARD_SPACING), dock_y)
                                
                                print(f"Round {header.round} starting with new cards")

                        # Check if turn changed
                        if new_state["current_turn"] != game_state["current_turn"]:
                            is_my_turn = new_state["current_turn"] == player_name
                            header.is_player_turn = is_my_turn
                            header.current_turn = (
                                "YOUR TURN" if is_my_turn else f"{opponent_name}'s TURN"
                            )

                            if is_my_turn:
                                turn_timer = TIMER_DURATION
                                last_timer_update = current_time

                            print(f"Turn changed to: {header.current_turn}")

                        game_state = new_state
            except Exception as e:
                print(f"Error updating game state: {e}")
                print(f"Current state: {game_state}")
                running = False

            # Update timer only if it's player's turn
            if header.is_player_turn:
                if current_time - last_timer_update >= 1000:
                    turn_timer -= 1
                    last_timer_update = current_time
                    print(f"Timer: {turn_timer}")

            # Find currently dragged card
            dragged_card = None
            for card in player_hand:
                if hasattr(card, 'dragging') and card.dragging:
                    dragged_card = card
                    break

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Only handle card events if it's player's turn
                if header.is_player_turn:
                    # Handle card dragging
                    for card in player_hand[:]:
                        if card.handle_event(event, player_play_area, go_button):
                            break

                    # Handle GO button
                    if event.type == pygame.MOUSEBUTTONDOWN and go_button.active:
                        if go_button.rect.collidepoint(event.pos):
                            if player_play_area.card:
                                network.play_card((player_play_area.card.suit, player_play_area.card.value))
                                if player_play_area.card in player_hand:
                                    player_hand.remove(player_play_area.card)
                                header.is_player_turn = False
                                header.current_turn = f"{opponent_name}'s TURN"
                                go_button.active = False

            # Update game state
            try:
                updated_state = network.send("get_state")
                if updated_state and isinstance(updated_state, dict):
                    if updated_state.get("status") == "in_game":
                        new_state = updated_state.get("game_state", game_state)
                        
                        # Check if turn changed
                        if new_state["current_turn"] != game_state["current_turn"]:
                            is_my_turn = new_state["current_turn"] == player_name
                            header.is_player_turn = is_my_turn
                            header.current_turn = "YOUR TURN" if is_my_turn else f"{opponent_name}'s TURN"
                            
                            if is_my_turn:
                                turn_timer = TIMER_DURATION
                                last_timer_update = current_time
                
                        # Check for opponent's played card
                        if network.player_num == 1:
                            opponent_played = new_state["player2"]["played_card"] is not None
                            opponent_card = new_state["player2"]["played_card"]
                        else:
                            opponent_played = new_state["player1"]["played_card"] is not None
                            opponent_card = new_state["player1"]["played_card"]

                        if opponent_played and not opponent_play_area.card:
                            # Show face-down card
                            face_down_card = Card("back", 0, os.path.join("Cards (large)", "card_back.png"))
                            opponent_play_area.add_card(face_down_card)
                        
                        game_state = new_state
                        
            except Exception as e:
                print(f"Error updating game state: {e}")
                running = False

            # Draw everything
            draw_game_board()
            
            # Draw all game elements
            # Draw non-dragged player cards first
            for card in player_hand:
                if not card.dragging:
                    card.draw(screen)

            # Draw play areas
            player_play_area.draw(screen)
            opponent_play_area.draw(screen)
            go_button.draw(screen)
            header.draw(screen)
            scoreboard.draw(screen)

            # Draw the dragged card last (on top)
            if dragged_card:
                dragged_card.draw(screen)

            pygame.display.flip()
            clock.tick(60)

    except Exception as e:
        print(f"Error in multiplayer game: {e}")
        print(f"Game state: {network.game_state}")  # Additional debug info


def main():
    # Create title screen
    title_screen = TitleScreen()
    game_mode = None
    running = True
    clock = pygame.time.Clock()

    while running and game_mode is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Handle title screen events
            result = title_screen.handle_event(event)
            if result:
                game_mode = result

        # Draw title screen
        title_screen.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    if running:
        if game_mode == "singleplayer":
            start_game()  # Existing single player game
        elif game_mode == "multiplayer":
            start_online_game()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
