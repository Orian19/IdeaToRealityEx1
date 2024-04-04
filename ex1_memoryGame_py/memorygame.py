import pygame
import random
import time
import sys
from vosk import Model, KaldiRecognizer
import pyaudio
import json

# Define colors
WHITE = (255, 255, 255)
GREEN = (144, 238, 144)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Constants
WIDTH, HEIGHT = 400, 450  # game screen size

CARD_WIDTH, CARD_HEIGHT = 80, 80  # Define card properties
GAP = 10  # between cards
ROWS, COLS = 4, 4  # cards arrangement

MAX_HINTS = 3  # Maximum number of hints per game
INITIAL_TIME_LIMIT = 60  # Initial time limit for Time Attack mode in seconds
TIME_LIMIT_DECREMENT = 10  # Time limit decrement for each subsequent game in Time Attack mode

VOICE_MODEL = "vosk-model-small-en-us-0.15"


def text_to_index(text):
    """
    convert text audio to card index in the game
    :param text: audio text
    :return:
    """
    num_dict = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
        "sixteen": 16
    }

    parts = text.split()
    if len(parts) > 1 and parts[0] == "number":
        return num_dict.get(parts[1].lower(), "Number not recognized")
    return "Format not recognized"


def speech_recognition():
    """
    voice control using VOSK
    :return: card index of what the user said
    """
    model = Model(VOICE_MODEL)
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)

    mic = pyaudio.PyAudio()
    stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
    stream.start_stream()

    while True:
        data = stream.read(4096)
        if len(data) == 0:
            break
        if recognizer.AcceptWaveform(data):
            text = recognizer.Result()
            index = json.loads(text)
            print(index["text"])
            index = text_to_index(index["text"])

            if isinstance(index, int):
                return index - 1

    stream.stop_stream()
    stream.close()
    mic.terminate()


def load_sound(file_path):
    """
    load game sounds
    :param file_path:
    :return: sound
    """
    try:
        sound = pygame.mixer.Sound(file_path)
        return sound
    except pygame.error as e:
        print(f"Unable to load sound file: {file_path}")
        return None


def draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP, flip_animation=None,
               card_back=None):
    """
    board drawing and updates for the game play
    :param WINDOW:
    :param images: card images
    :param revealed: cards that have already been revealed by the player
    :param matched: matching pair
    :param ROWS:
    :param COLS:
    :param CARD_WIDTH:
    :param CARD_HEIGHT:
    :param GAP:
    :param flip_animation:
    :param card_back:
    :return:
    """

    WINDOW.fill(WHITE)
    if card_back is None:
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
                        if flip_animation["phase"] == "hiding":
                            # Show card back shrinking
                            img = pygame.transform.scale(card_back, (width, CARD_HEIGHT))
                        else:
                            # Show card face expanding
                            img = pygame.transform.scale(images[index], (width, CARD_HEIGHT))
                    else:
                        width = CARD_WIDTH
                        img = pygame.transform.scale(images[index], (width, CARD_HEIGHT))
                    WINDOW.blit(img, (x, y))
                else:
                    # Display card back
                    card_back_scaled = pygame.transform.scale(card_back, (CARD_WIDTH, CARD_HEIGHT))
                    WINDOW.blit(card_back_scaled, (x, y))


def flip_animation_step(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP, index, card_back,
                        hint=False):
    """
    flipping card anmation for when a card is to be revealed to the player
    :param WINDOW:
    :param images:
    :param revealed:
    :param matched:
    :param ROWS:
    :param COLS:
    :param CARD_WIDTH:
    :param CARD_HEIGHT:
    :param GAP:
    :param index:
    :param card_back:
    :param hint:
    :return:
    """
    # First phase: shrinking the card to the middle
    for width in range(CARD_WIDTH, 0, -10):
        draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP,
                   flip_animation={"index": index, "width": width, "phase": "hiding"}, card_back=card_back)
        pygame.display.update()
        pygame.time.wait(25)

    # Swap from the card back to the card face here if necessary
    if not revealed[index]:
        revealed[index] = True  # This ensures that the card face is shown in the expanding phase

    # Second phase: expanding the card from the middle to full width
    for width in range(0, CARD_WIDTH + 1, 10):
        draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP,
                   flip_animation={"index": index, "width": width, "phase": "revealing"}, card_back=card_back)
        pygame.display.update()
        pygame.time.wait(25)

    # close card shortly after revealed if hint
    if hint:
        revealed[index] = False
        draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP,
                   flip_animation={"index": index, "width": width, "phase": "revealing"}, card_back=card_back)
        pygame.display.update()
        pygame.time.wait(25)


def display_text(WINDOW, text1, text2, FONT, position1, position2, color=BLACK):
    """
    helper function to display text
    :param WINDOW:
    :param text1:
    :param text2:
    :param FONT:
    :param position1:
    :param position2:
    :param color:
    :return:
    """
    text_surface1 = FONT.render(text1, True, color)
    text_rect1 = text_surface1.get_rect(**position1)
    WINDOW.blit(text_surface1, text_rect1)

    text_surface2 = FONT.render(text2, True, color)
    text_rect2 = text_surface2.get_rect(**position2)
    WINDOW.blit(text_surface2, text_rect2)

    return text_rect2


def check_match(selected, revealed, matched, images, match_sound, win_sound, num_players, player_turn):
    """
    logic function to check if a pair of cards is matched
    :param selected:
    :param revealed:
    :param matched:
    :param images:
    :param match_sound:
    :param win_sound:
    :param num_players:
    :param player_turn:
    :return:
    """
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
    """
    a window for when the player wins or losses the game which includes a play again option or game over
    :param WINDOW:
    :param FONT:
    :param WIDTH:
    :param HEIGHT:
    :param winner:
    :return:
    """
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


def get_hint(revealed, matched, num_players):
    """
    helper function to get a random index of a card to be revealed (shortly) for a hint (only for 1 player)
    :param revealed:
    :param matched:
    :param num_players:
    :return:
    """
    if num_players == 1:  # Check if the game is in 1 player mode
        unmatched_indices = [i for i, value in enumerate(revealed) if not value and i not in matched]
        if unmatched_indices:
            hint_index = random.choice(unmatched_indices)
            return hint_index
    return None


def hint_processing(WINDOW, x, y, revealed, matched, num_players, images, card_back, hints_remaining, hint_button_rect):
    """
    handle hint processing. revealing a card for a short amount of time
    :return:
    """
    # Check if the click was on the "Hint" button
    # hint_button_rect = hint_surface.get_rect(topleft=(WIDTH - 210, HEIGHT - 38))
    # hint_button_rect = pygame.Rect(WIDTH - 210, HEIGHT - 38, 80, 30)
    if hint_button_rect.collidepoint(x, y):
        hint_index = get_hint(revealed, matched, num_players)
        if hint_index is not None:
            hints_remaining -= 1
            pygame.time.set_timer(pygame.USEREVENT, 3000, True)
            flip_animation_step(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP,
                                hint_index, card_back, True)

    return hints_remaining


def card_selection_processing(WINDOW, voice_index, row, col, revealed, selected, matched, images, card_back,
                              num_players, player_turn, match_sound, win_sound):
    """
    handling the process of cards selection
    :param WINDOW:
    :param voice_index:
    :param row:
    :param col:
    :param revealed:
    :param selected:
    :param matched:
    :param images:
    :param card_back:
    :param num_players:
    :param player_turn:
    :param match_sound:
    :param win_sound:
    :return: current player's turn
    """
    if voice_index:  # if in voice control mode
        index = voice_index
    else:  # if in "regular" clicking mode
        index = row * COLS + col
    if not revealed[index] and len(selected) < 2:
        flip_animation_step(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP,
                            index, card_back)
        revealed[index] = True
        selected.append(index)
        if len(selected) == 2:  # if the user selected two cards --> updating board and checking for a match
            draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP)
            pygame.display.update()
            time.sleep(1)
            player_turn = check_match(selected, revealed, matched, images, match_sound, win_sound,
                                      num_players, player_turn)
    elif len(selected) == 1 and selected[0] == index:
        # If the same card is clicked twice, keep it revealed
        revealed[index] = True

    return player_turn


def load_card_images(pygame):
    """
    load images for the game
    :param pygame:
    :return:
    """
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
    card_back = pygame.image.load("card_back.png")

    return images, card_back


def draw_main_win_buttons(WINDOW, FONT, pygame, rect_list):
    """
    drae the buttons which will appear on the main window of the game
    :param WINDOW:
    :param FONT:
    :param pygame:
    :param rect_list:
    :return:
    """
    # Draw buttons
    for rect in rect_list:
        pygame.draw.rect(WINDOW, GREEN, rect)

    # Draw text on buttons
    display_text(WINDOW, "1 Player", "2 Players", FONT, {"center": (200, 175)}, {"center": (200, 275)})
    display_text(WINDOW, "Time Attack", "", FONT, {"center": (200, 100)}, {"center": (200, 100)})
    display_text(WINDOW, "Voice Control", "", FONT, {"center": (200, 50)}, {"center": (200, 50)})


def game_reset(images):
    """
    reset all game parameters for a new game
    :param revealed:
    :param selected:
    :param matched:
    :param images:
    :param hints_remaining:
    :param hint_index:
    :param start_time:
    :param game_over:
    :param player_turn:
    :return:
    """
    revealed = [False] * (ROWS * COLS)
    selected = []
    matched = []
    random.shuffle(images)  # reshuffle the cards
    hints_remaining = MAX_HINTS  # reset hints
    hint_index = None
    start_time = time.time()  # reset time
    game_over = False
    player_turn = 1  # reset player turn (for 2 player mode)

    return revealed, selected, matched, hints_remaining, hint_index, start_time, game_over, player_turn


def game_mode_window(WINDOW, FONT, timer_text, voice_control, hints_remaining, num_players, time_attack, player_turn):
    """
    handling actual game mode window
    :param WINDOW:
    :param FONT:
    :param timer_text:
    :param voice_control:
    :param hints_remaining:
    :param num_players:
    :param time_attack:
    :param player_turn:
    :return:
    """
    reset_text_rect = display_text(WINDOW, timer_text, "Reset", FONT,
                                   position1={"bottomleft": (10, HEIGHT - 10)},
                                   position2={"bottomright": (WIDTH - 10, HEIGHT - 10)})

    if voice_control:
        small_font_size = 25
        small_font = pygame.font.Font(None, small_font_size)  # Create a new Font object for the smaller text

        info_text = "Say 'number' followed by the card number (1-16)"
        info_text_surface = small_font.render(info_text, True, BLACK)
        info_text_rect = info_text_surface.get_rect(midbottom=(WIDTH - 196, HEIGHT - 60))
        WINDOW.blit(info_text_surface, info_text_rect)

    # Display "Hint" button
    hint_text = f"Hints: {hints_remaining}"
    hint_surface = FONT.render(hint_text, True, BLACK)
    hint_rect = hint_surface.get_rect(topleft=(WIDTH - 210, HEIGHT - 38))

    if num_players == 2 or time_attack or voice_control:
        pygame.draw.rect(WINDOW, RED, hint_rect)
    else:
        pygame.draw.rect(WINDOW, GREEN, hint_rect)
    WINDOW.blit(hint_surface, hint_rect)

    # Display player turn
    player_turn_text = f"P{player_turn}"
    player_turn_surface = FONT.render(player_turn_text, True, BLACK)
    player_turn_rect = player_turn_surface.get_rect(midbottom=(WIDTH - 20, HEIGHT // 2))
    WINDOW.blit(player_turn_surface, player_turn_rect)

    return reset_text_rect, hint_rect


def process_game_mode(WINDOW, FONT, num_players, time_attack, voice_control, buttons):
    """
    handling the mode the user chose
    :param num_players:
    :param time_attack:
    :param voice_control:
    :param buttons: [one_player_button_rect,two_players_button_rect, time_attack_button_rect, voice_control_button_rect]
    :return:
    """
    while num_players == 0 and not time_attack and not voice_control:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if buttons[0].collidepoint(x, y):
                    num_players = 1
                elif buttons[1].collidepoint(x, y):
                    num_players = 2
                elif buttons[2].collidepoint(x, y):
                    time_attack = True
                elif buttons[3].collidepoint(x, y):
                    voice_control = True

        WINDOW.fill(WHITE)

        draw_main_win_buttons(WINDOW, FONT, pygame, buttons)
        pygame.display.update()

    return num_players, time_attack, voice_control


def main():
    # Initialize Pygame
    pygame.init()

    # Set up display
    WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Memory Game")

    # Load images
    images, card_back = load_card_images(pygame)

    # Duplicate images to create pairs
    images *= 2

    # Shuffle images
    random.shuffle(images)

    # Define font
    FONT = pygame.font.SysFont(None, 40)

    # Define game variables
    revealed = [False] * (ROWS * COLS)
    selected = []
    matched = []
    hints_remaining = MAX_HINTS
    hint_index = None

    # Load positive sound
    match_sound = load_sound("positive_sound.wav")
    # Load win sound
    win_sound = load_sound("win_sound.wav")

    num_players = 0
    time_attack = False
    voice_control = False
    time_limit = INITIAL_TIME_LIMIT

    running = True
    game_over = False
    clock = pygame.time.Clock()

    start_time = time.time()  # Start time
    voice_index = None
    reset_text_rect = None

    player_turn = 1  # Player 1 starts

    # Display window for game modes
    one_player_button_rect = pygame.Rect(100, 150, 200, 50)
    two_players_button_rect = pygame.Rect(100, 250, 200, 50)
    time_attack_button_rect = pygame.Rect(100, 75, 200, 50)
    voice_control_button_rect = pygame.Rect(100, 20, 200, 50)
    rect_list = [one_player_button_rect, two_players_button_rect, time_attack_button_rect, voice_control_button_rect]

    num_players, time_attack, voice_control = process_game_mode(WINDOW, FONT, num_players, time_attack, voice_control,
                                                                rect_list)

    # game loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if voice_control:
                voice_index = speech_recognition()
            if not game_over and event.type == pygame.MOUSEBUTTONDOWN or voice_control:
                x, y = pygame.mouse.get_pos()
                col = x // (CARD_WIDTH + GAP)
                row = y // (CARD_HEIGHT + GAP)
                if col < COLS and row < ROWS or voice_index:  # Check if the click is within the grid
                    player_turn = card_selection_processing(WINDOW, voice_index, row, col, revealed, selected, matched,
                                                            images,
                                                            card_back, num_players, player_turn, match_sound, win_sound)
                elif reset_text_rect is not None and reset_text_rect.collidepoint(x, y):
                    (revealed, selected, matched, hints_remaining, hint_index, start_time,
                     game_over, player_turn) = game_reset(images)
                elif hints_remaining > 0 and num_players == 1:  # handling hints updates (for 1 player mode)
                    hints_remaining = hint_processing(WINDOW, x, y, revealed, matched, num_players,
                                                      images, card_back, hints_remaining, hint_rect)
            elif game_over and event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if reset_text_rect is not None and reset_text_rect.collidepoint(x, y):
                    (revealed, selected, matched, hints_remaining, hint_index, start_time,
                     game_over, player_turn) = game_reset(images)
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

        draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP,
                   flip_animation={"index": hint_index, "width": CARD_WIDTH, "phase": "hiding"}, card_back=card_back)

        # game stop conditions
        if elapsed_time < 0:  # checking if time is over (for attack mode)
            game_over = True
            reset_text_rect = win_screen(WINDOW, FONT, WIDTH, HEIGHT, winner=False)
        elif len(matched) == len(images):  # checking if all images were matched
            game_over = True
            reset_text_rect = win_screen(WINDOW, FONT, WIDTH, HEIGHT, winner=True)
            # Decrement time limit for Time Attack mode
            if time_attack:
                time_limit -= TIME_LIMIT_DECREMENT
                (revealed, selected, matched, hints_remaining, hint_index,
                 start_time, game_over, player_turn) = (
                    game_reset(revealed, selected, matched, images, hints_remaining,
                               hint_index, start_time, game_over, player_turn))
        else:  # game continues
            reset_text_rect, hint_rect = game_mode_window(WINDOW, FONT, timer_text, voice_control, hints_remaining,
                                                          num_players, time_attack, player_turn)

        pygame.display.update()
        clock.tick(60)  # frame rate control

    pygame.quit()


if __name__ == "__main__":
    main()
