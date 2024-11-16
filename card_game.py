import pygame
import sys
import random
import os

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
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
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

    for suit in suits:
        for value in values:
            image_path = os.path.join(
                "Cards (large)", f"card_{suit}_{str(value).zfill(2)}.png"
            )
            cards.append(Card(suit, value, image_path))

    return cards


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

    # Draw player's play area (bottom-left of middle screen)
    player_area = pygame.Rect(
        50, WINDOW_HEIGHT // 2 - CARD_HEIGHT // 2, CARD_WIDTH + 20, CARD_HEIGHT + 20
    )
    pygame.draw.rect(screen, GRAY, player_area)
    pygame.draw.rect(screen, BLACK, player_area, 2)

    # Draw computer's play area (bottom-right of middle screen)
    computer_area = pygame.Rect(
        WINDOW_WIDTH - CARD_WIDTH - 70,
        WINDOW_HEIGHT // 2 - CARD_HEIGHT // 2,
        CARD_WIDTH + 20,
        CARD_HEIGHT + 20,
    )
    pygame.draw.rect(screen, GRAY, computer_area)
    pygame.draw.rect(screen, BLACK, computer_area, 2)


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

    def add_card(self, card):
        self.card = card
        # Center the card in the play area
        card.rect.centerx = self.rect.centerx
        card.rect.centery = self.rect.centery

    def remove_card(self):
        self.card = None

    def is_empty(self):
        return self.card is None


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

    def set_game_over(self, winner):
        self.game_over = True
        self.winner = winner
        self.current_turn = f"{winner} WINS!"


class ComputerPlayer:
    def __init__(self, hand, play_area):
        self.hand = hand
        self.play_area = play_area
        self.card_backs = []
        self.update_card_backs()

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
        self.update_card_backs()

    def play_card(self):
        # For now, just play a random card
        if self.hand:
            chosen_card = random.choice(self.hand)
            self.hand.remove(chosen_card)
            self.play_area.add_card(chosen_card)
            self.update_card_backs()
            return chosen_card
        return None

    def draw(self, surface):
        # Draw card backs for remaining cards
        for card_back in self.card_backs:
            surface.blit(card_back["image"], card_back["rect"])


class ScoreBoard:
    def __init__(self):
        self.player_score = 0
        self.computer_score = 0
        self.player_wins = []  # List of winning cards (small versions)
        self.computer_wins = []
        self.load_small_cards()

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

    def compare_cards(self, player_card, computer_card):
        # Define the winning relationships
        beats = {"diamonds": "spades", "spades": "hearts", "hearts": "diamonds"}

        if player_card.suit == computer_card.suit:
            # Same suit, compare values
            return player_card.value > computer_card.value
        else:
            # Different suits, check if player's card beats computer's card
            return beats[player_card.suit] == computer_card.suit

    def add_win(self, winning_card, is_player_win):
        card_key = f"{winning_card.suit}_{winning_card.value}"
        if is_player_win:
            self.player_score += 1
            self.player_wins.append(self.small_card_images[card_key])
        else:
            self.computer_score += 1
            self.computer_wins.append(self.small_card_images[card_key])

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


def main():
    # Create and shuffle the deck
    deck = create_deck()

    # Deal cards to both players
    player_hand = deal_cards(deck, 5)
    computer_hand = deal_cards(deck, 5)

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

    # Create the computer player
    computer = ComputerPlayer(computer_hand, computer_play_area)

    # Create the GO button
    go_button = Button(
        WINDOW_WIDTH - 120, WINDOW_HEIGHT - 70, BUTTON_WIDTH, BUTTON_HEIGHT
    )

    # Create the header
    header = Header()

    # Position the player's cards in the dock
    dock_start_x = (WINDOW_WIDTH - (CARD_WIDTH * 5 + CARD_SPACING * 4)) // 2
    dock_y = WINDOW_HEIGHT - DOCK_HEIGHT + 25

    for i, card in enumerate(player_hand):
        card.set_position(dock_start_x + i * (CARD_WIDTH + CARD_SPACING), dock_y)

    # Add scoreboard
    scoreboard = ScoreBoard()

    # Add game state flags
    resolving_round = False
    resolution_start_time = None
    RESOLUTION_DELAY = 1500  # 1.5 seconds to show the comparison

    running = True
    clock = pygame.time.Clock()
    computer_play_time = None

    # Add end screen
    end_screen = EndScreen()
    end_screen_started = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if header.game_over:
                if end_screen.handle_event(event):
                    # Reset game
                    return main()
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
            if pygame.time.get_ticks() - resolution_start_time >= RESOLUTION_DELAY:
                # Compare cards and determine winner
                player_card = player_play_area.card
                computer_card = computer_play_area.card

                player_wins = scoreboard.compare_cards(player_card, computer_card)

                # Add winning card to score display
                if player_wins:
                    scoreboard.add_win(player_card, True)
                else:
                    scoreboard.add_win(computer_card, False)

                # Remove the played card from player's hand
                if player_card in player_hand:
                    player_hand.remove(player_card)

                # Clear play areas
                player_play_area.remove_card()
                computer_play_area.remove_card()

                # Check if game is over
                if scoreboard.player_score >= 4:
                    header.set_game_over("PLAYER")
                elif scoreboard.computer_score >= 4:
                    header.set_game_over("COMPUTER")

                # Only continue with next round if game isn't over
                if not header.game_over:
                    # Deal new cards if there are cards left in the deck
                    if len(deck) > 0:
                        # Deal to player
                        new_player_card = deal_cards(deck, 1)[0]
                        player_hand.append(new_player_card)

                        # Deal to computer
                        new_computer_card = deal_cards(deck, 1)[0]
                        computer.add_card(new_computer_card)

                    # Reposition all player cards including the new one
                    dock_start_x = (
                        WINDOW_WIDTH
                        - (
                            CARD_WIDTH * len(player_hand)
                            + CARD_SPACING * (len(player_hand) - 1)
                        )
                    ) // 2
                    dock_y = WINDOW_HEIGHT - DOCK_HEIGHT + 25

                    for i, card in enumerate(player_hand):
                        target_pos = (
                            dock_start_x + i * (CARD_WIDTH + CARD_SPACING),
                            dock_y,
                        )
                        if card == new_player_card:  # If it's the new card, animate it
                            card.start_deal_animation(target_pos)
                        else:  # Otherwise just reposition it
                            card.set_position(*target_pos)
                            card.original_pos = target_pos

                    header.round += 1

                # Reset for next round or end game
                resolving_round = False
                computer_play_time = None
                if not header.game_over:
                    header.switch_turn()

        # Update card animations
        for card in player_hand:
            card.update_animation()

        # Handle end screen
        if header.game_over and not end_screen_started:
            end_screen_started = True
            end_screen.start_animation()

        if header.game_over:
            end_screen.update()

        # Draw everything
        draw_game_board()

        # Draw player cards
        for card in player_hand:
            card.draw(screen)

        # Draw computer's cards (backs)
        computer.draw(screen)

        # Draw cards in play areas
        if player_play_area.card:
            player_play_area.card.draw(screen)
        if computer_play_area.card:
            computer_play_area.card.draw(screen)

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


if __name__ == "__main__":
    main()
