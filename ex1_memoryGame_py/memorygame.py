import pygame
import random
import time
import sys

# Define colors
WHITE = (255, 255, 255)
GREEN = (144, 238, 144)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Constants
MAX_HINTS = 3  # Maximum number of hints per game
INITIAL_TIME_LIMIT = 60  # Initial time limit for Time Attack mode in seconds
TIME_LIMIT_DECREMENT = 10  # Time limit decrement for each subsequent game in Time Attack mode


def load_sound(file_path):
    try:
        sound = pygame.mixer.Sound(file_path)
        return sound
    except pygame.error as e:
        print(f"Unable to load sound file: {file_path}")
        return None


def draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP, flip_animation=None):
    WINDOW.fill(WHITE)
    card_back = pygame.image.load("card_back.png")
    for i in range(ROWS):
        for j in range(COLS):
            index = i * COLS + j
            x = j * (CARD_WIDTH + GAP)
            y = i * (CARD_HEIGHT + GAP)

            if (i, j) in matched:
                pygame.draw.rect(WINDOW, WHITE, (x, y, CARD_WIDTH, CARD_HEIGHT))
            else:
                if revealed[index] or (flip_animation and flip_animation["index"] == index):
                    if flip_animation and flip_animation["index"] == index:
                        width = flip_animation["width"]
                        x += (CARD_WIDTH - width) / 2  # Center the animating card
                    else:
                        width = CARD_WIDTH

                    image = pygame.transform.scale(images[index], (width, CARD_HEIGHT))
                    WINDOW.blit(image, (x, y))
                else:
                    # Display card back
                    card_back_scaled = pygame.transform.scale(card_back, (CARD_WIDTH, CARD_HEIGHT))
                    WINDOW.blit(card_back_scaled, (x, y))

def flip_animation_step(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP, index):
    for width in list(range(CARD_WIDTH, 0, -10)) + list(range(0, CARD_WIDTH + 1, 10)):
        draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP, {"index": index, "width": width})
        pygame.display.update()
        pygame.time.wait(25)  # Control the speed of the animation


def display_text(WINDOW, text1, text2, FONT, position1, position2, color=BLACK):
    text_surface1 = FONT.render(text1, True, color)
    text_rect1 = text_surface1.get_rect(**position1)
    WINDOW.blit(text_surface1, text_rect1)

    text_surface2 = FONT.render(text2, True, color)
    text_rect2 = text_surface2.get_rect(**position2)
    WINDOW.blit(text_surface2, text_rect2)

    return text_rect2  # Return the rectangle of the reset text for click detection


def check_match(selected, revealed, matched, images, match_sound, win_sound, num_players, player_turn):
    if len(selected) == 2:
        if images[selected[0]] == images[selected[1]]:
            matched.extend(selected)
            match_sound.play()  # Play positive sound when a match is made
        else:
            # Hide the cards if they don't match
            revealed[selected[0]] = False
            revealed[selected[1]] = False

        if num_players == 2 and images[selected[0]] != images[selected[1]]:
            player_turn = 1 if player_turn == 2 else 2
        selected.clear()

    if len(matched) == len(images):
        win_sound.play()  # Play win sound when all matches are made

    return player_turn


def win_screen(WINDOW, FONT, WIDTH, HEIGHT, winner):
    if winner:
        message = "Well Done!"
        button_text = "Play Again"
        message_surface = FONT.render(message, True, BLACK)
        button_surface = FONT.render(button_text, True, BLACK)
        message_rect = message_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        button_rect = button_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

        pygame.draw.rect(WINDOW, GREEN, (WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2))
        WINDOW.blit(message_surface, message_rect)
        pygame.draw.rect(WINDOW, BLACK, button_rect, 2)
        WINDOW.blit(button_surface, button_rect)
    else:
        message = "Game Over!"
        button_text = "Try Again"
        message_surface = FONT.render(message, True, BLACK)
        button_surface = FONT.render(button_text, True, BLACK)
        message_rect = message_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        button_rect = button_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

        pygame.draw.rect(WINDOW, RED, (WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2))
        WINDOW.blit(message_surface, message_rect)
        pygame.draw.rect(WINDOW, BLACK, button_rect, 2)
        WINDOW.blit(button_surface, button_rect)

    return button_rect  # Return the rectangle of the button for click detection


def get_hint(revealed, matched, images, num_players):
    if num_players == 1:  # Check if the game is in 1 player mode
        unmatched_indices = [i for i, value in enumerate(revealed) if not value and i not in matched]
        if unmatched_indices:
            hint_index = random.choice(unmatched_indices)
            return hint_index
    return None


def main():
    # Initialize Pygame
    pygame.init()

    # Set up display
    WIDTH, HEIGHT = 400, 400
    WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Memory Game")

    # Load images
    images = [
        pygame.image.load("image1.png"),  # Replace "image1.png" with the path to your image file
        pygame.image.load("image2.png"),  # Replace "image2.png" with the path to your image file
        pygame.image.load("image3.png"),  # Replace "image3.png" with the path to your image file
        pygame.image.load("image4.png"),  # Replace "image4.png" with the path to your image file
        pygame.image.load("image5.png"),  # Replace "image5.png" with the path to your image file
        pygame.image.load("image6.png"),  # Replace "image6.png" with the path to your image file
        pygame.image.load("image7.png"),  # Replace "image7.png" with the path to your image file
        pygame.image.load("image8.png"),  # Replace "image8.png" with the path to your image file
    ]

    # Duplicate images to create pairs
    images *= 2

    # Shuffle images
    random.shuffle(images)

    # Define card properties
    CARD_WIDTH, CARD_HEIGHT = 80, 80
    GAP = 10
    ROWS, COLS = 4, 4

    # Define font
    FONT = pygame.font.SysFont(None, 40)

    # Define game variables
    revealed = [False] * (ROWS * COLS)
    selected = []
    matched = []
    hints_remaining = MAX_HINTS
    hint_index = None

    # Load positive sound
    match_sound = load_sound("positive_sound.wav")  # Replace "positive_sound.wav" with your sound file
    # Load win sound
    win_sound = load_sound("win_sound.wav")  # Replace "win_sound.wav" with your sound file

    # Display prompt for number of players
    one_player_button_rect = pygame.Rect(100, 150, 200, 50)
    two_players_button_rect = pygame.Rect(100, 250, 200, 50)
    time_attack_button_rect = pygame.Rect(100, 75, 200, 50)

    num_players = 0
    time_attack = False
    time_limit = INITIAL_TIME_LIMIT

    while num_players == 0 and not time_attack:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if one_player_button_rect.collidepoint(x, y):
                    num_players = 1
                elif two_players_button_rect.collidepoint(x, y):
                    num_players = 2
                elif time_attack_button_rect.collidepoint(x, y):
                    time_attack = True

        WINDOW.fill(WHITE)
        # Draw buttons
        pygame.draw.rect(WINDOW, GREEN, one_player_button_rect)
        pygame.draw.rect(WINDOW, GREEN, two_players_button_rect)
        pygame.draw.rect(WINDOW, GREEN, time_attack_button_rect)

        # Draw text on buttons
        display_text(WINDOW, "1 Player", "2 Players", FONT, {"center": (200, 175)}, {"center": (200, 275)})
        display_text(WINDOW, "Time Attack", "", FONT, {"center": (200, 100)}, {"center": (200, 100)})

        pygame.display.update()

    player_turn = 1  # Player 1 starts

    # Main game loop
    running = True
    game_over = False
    clock = pygame.time.Clock()

    # Start time
    start_time = time.time()

    reset_text_rect = None
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if not game_over and event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                col = x // (CARD_WIDTH + GAP)
                row = y // (CARD_HEIGHT + GAP)
                if col < COLS and row < ROWS:  # Check if the click is within the grid
                    index = row * COLS + col
                    if not revealed[index] and len(selected) < 2:
                        flip_animation_step(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP,
                                            index)
                        revealed[index] = True
                        selected.append(index)
                        if len(selected) == 2:
                            draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP)
                            pygame.display.update()
                            time.sleep(1)
                            player_turn = check_match(selected, revealed, matched, images, match_sound, win_sound,
                                                      num_players, player_turn)
                    elif len(selected) == 1 and selected[0] == index:
                        # If the same card is clicked twice, keep it revealed
                        revealed[index] = True
                elif reset_text_rect is not None and reset_text_rect.collidepoint(x, y):
                    # Reset the game
                    revealed = [False] * (ROWS * COLS)
                    selected = []
                    matched = []
                    random.shuffle(images)
                    hints_remaining = MAX_HINTS
                    hint_index = None
                    start_time = time.time()
                    game_over = False
                elif hints_remaining > 0:
                    # Check if the click was on the "Hint" button
                    hint_button_rect = pygame.Rect(WIDTH - 210, HEIGHT - 38, 80, 30)
                    if hint_button_rect.collidepoint(x, y):
                        hint_index = get_hint(revealed, matched, images, num_players)
                        if hint_index is not None:
                            hints_remaining -= 1
                            pygame.time.set_timer(pygame.USEREVENT, 3000, True)  # Set a timer to hide the hint card
            elif game_over and event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if reset_text_rect is not None and reset_text_rect.collidepoint(x, y):
                    # Reset the game
                    revealed = [False] * (ROWS * COLS)
                    selected = []
                    matched = []
                    random.shuffle(images)
                    hints_remaining = MAX_HINTS
                    hint_index = None
                    start_time = time.time()
                    game_over = False
            elif event.type == pygame.USEREVENT:
                # Timer event to hide the hint card
                hint_index = None

        # Calculate elapsed time
        if time_attack:
            elapsed_time = time_limit - (time.time() - start_time)
        else:
            elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        timer_text = f"Time: {minutes:02d}:{seconds:02d}"

        draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP, hint_index)
        if elapsed_time < 0:
            game_over = True
            reset_text_rect = win_screen(WINDOW, FONT, WIDTH, HEIGHT, winner=False)
        elif len(matched) == len(images):
            game_over = True
            reset_text_rect = win_screen(WINDOW, FONT, WIDTH, HEIGHT, winner=True)
            # Decrement time limit for Time Attack mode
            if time_attack:
                time_limit -= TIME_LIMIT_DECREMENT
                # Reset the game for the next round with reduced time limit
                revealed = [False] * (ROWS * COLS)
                selected = []
                matched = []
                random.shuffle(images)
                hints_remaining = MAX_HINTS
                hint_index = None
                start_time = time.time()
                game_over = False
        else:
            reset_text_rect = display_text(WINDOW, timer_text, "Reset", FONT,
                                           position1={"bottomleft": (10, HEIGHT - 10)},
                                           position2={"bottomright": (WIDTH - 10, HEIGHT - 10)})
            # Display "Hint" button
            hint_text = f"Hints: {hints_remaining}"
            hint_surface = FONT.render(hint_text, True, BLACK)
            hint_rect = hint_surface.get_rect(topleft=(WIDTH - 210, HEIGHT - 38))
            if num_players == 2:
                pygame.draw.rect(WINDOW, RED, hint_rect)
            else:
                pygame.draw.rect(WINDOW, GREEN, hint_rect)
            WINDOW.blit(hint_surface, hint_rect)

            # Display player turn
            player_turn_text = f"P{player_turn}"
            player_turn_surface = FONT.render(player_turn_text, True, BLACK)
            player_turn_rect = player_turn_surface.get_rect(midbottom=(WIDTH - 20, HEIGHT // 2))
            WINDOW.blit(player_turn_surface, player_turn_rect)

        pygame.display.update()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
