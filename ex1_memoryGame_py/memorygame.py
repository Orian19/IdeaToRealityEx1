import pygame
import random
import time
import sys

# Define colors
WHITE = (255, 255, 255)
GREEN = (144, 238, 144)
BLACK = (0, 0, 0)


def load_sound(file_path):
    try:
        sound = pygame.mixer.Sound(file_path)
        return sound
    except pygame.error as e:
        print(f"Unable to load sound file: {file_path}")
        return None


def draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP):
    WINDOW.fill(WHITE)
    for i in range(ROWS):
        for j in range(COLS):
            index = i * COLS + j
            if (i, j) in matched:
                pygame.draw.rect(WINDOW, WHITE,
                                 (j * (CARD_WIDTH + GAP), i * (CARD_HEIGHT + GAP), CARD_WIDTH, CARD_HEIGHT))
            elif revealed[index]:
                # Display the actual image if revealed
                image = pygame.transform.scale(images[index], (CARD_WIDTH, CARD_HEIGHT))
                WINDOW.blit(image, (j * (CARD_WIDTH + GAP), i * (CARD_HEIGHT + GAP)))
            else:
                # Display card back
                card_back = pygame.image.load(
                    "card_back.png")  # Replace "card_back.png" with the path to your card back image
                card_back = pygame.transform.scale(card_back, (CARD_WIDTH, CARD_HEIGHT))
                WINDOW.blit(card_back, (j * (CARD_WIDTH + GAP), i * (CARD_HEIGHT + GAP)))


def display_text(WINDOW, text1, text2, FONT, position1, position2, color=BLACK):
    text_surface1 = FONT.render(text1, True, color)
    text_rect1 = text_surface1.get_rect(**position1)
    WINDOW.blit(text_surface1, text_rect1)

    text_surface2 = FONT.render(text2, True, color)
    text_rect2 = text_surface2.get_rect(**position2)
    WINDOW.blit(text_surface2, text_rect2)

    return text_rect2  # Return the rectangle of the reset text for click detection


def check_match(selected, revealed, matched, images, match_sound, win_sound):
    if len(selected) == 2:
        if images[selected[0]] == images[selected[1]]:
            matched.extend(selected)
            match_sound.play()  # Play positive sound when a match is made
        else:
            # Hide the cards if they don't match
            revealed[selected[0]] = False
            revealed[selected[1]] = False
        selected.clear()

    if len(matched) == len(images):
        win_sound.play()  # Play win sound when all matches are made


def win_screen(WINDOW, FONT, WIDTH, HEIGHT):
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

    return button_rect  # Return the rectangle of the button for click detection


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

    # Load positive sound
    match_sound = load_sound("positive_sound.wav")  # Replace "positive_sound.wav" with your sound file
    # Load win sound
    win_sound = load_sound("win_sound.wav")  # Replace "win_sound.wav" with your sound file

    # Main game loop
    running = True
    game_over = False
    clock = pygame.time.Clock()

    # Start time
    start_time = time.time()

    reset_text_rect = None  # Define reset text rectangle outside the loop
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
                        revealed[index] = True
                        selected.append(index)
                        if len(selected) == 2:
                            draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP)
                            pygame.display.update()
                            time.sleep(1)
                            check_match(selected, revealed, matched, images, match_sound, win_sound)
                    elif len(selected) == 1 and selected[0] == index:
                        # If the same card is clicked twice, keep it revealed
                        revealed[index] = True
                elif reset_text_rect is not None and reset_text_rect.collidepoint(x, y):
                    # Reset the game
                    revealed = [False] * (ROWS * COLS)
                    selected = []
                    matched = []
                    random.shuffle(images)
                    start_time = time.time()
                    game_over = False
            elif game_over and event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if reset_text_rect is not None and reset_text_rect.collidepoint(x, y):
                    # Reset the game
                    revealed = [False] * (ROWS * COLS)
                    selected = []
                    matched = []
                    random.shuffle(images)
                    start_time = time.time()
                    game_over = False

        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        timer_text = f"Time: {minutes:02d}:{seconds:02d}"

        draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP)
        if len(matched) == len(images):
            game_over = True
            reset_text_rect = win_screen(WINDOW, FONT, WIDTH, HEIGHT)  # Update reset text rectangle
        else:
            reset_text_rect = display_text(WINDOW, timer_text, "Reset", FONT, position1={"bottomleft": (10, HEIGHT - 10)},
                                           position2={"bottomright": (WIDTH - 10, HEIGHT - 10)})
        pygame.display.update()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
