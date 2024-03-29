import pygame
import random
import time
import sys

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP):
    WINDOW.fill(WHITE)
    for i in range(ROWS):
        for j in range(COLS):
            index = i * COLS + j
            if (i, j) in matched:
                pygame.draw.rect(WINDOW, WHITE, (j * (CARD_WIDTH + GAP), i * (CARD_HEIGHT + GAP), CARD_WIDTH, CARD_HEIGHT))
            elif revealed[index]:
                # Display the actual image if revealed
                image = pygame.transform.scale(images[index], (CARD_WIDTH, CARD_HEIGHT))
                WINDOW.blit(image, (j * (CARD_WIDTH + GAP), i * (CARD_HEIGHT + GAP)))
            else:
                # Display card back
                card_back = pygame.image.load("card_back.png")  # Replace "card_back.png" with the path to your card back image
                card_back = pygame.transform.scale(card_back, (CARD_WIDTH, CARD_HEIGHT))
                WINDOW.blit(card_back, (j * (CARD_WIDTH + GAP), i * (CARD_HEIGHT + GAP)))

def display_text(WINDOW, text, FONT, WIDTH, HEIGHT):
    text_surface = FONT.render(text, True, BLACK)
    text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    WINDOW.blit(text_surface, text_rect)

def check_match(selected, revealed, matched, images):
    if len(selected) == 2:
        if images[selected[0]] == images[selected[1]]:
            matched.extend(selected)
        else:
            # Hide the cards if they don't match
            revealed[selected[0]] = False
            revealed[selected[1]] = False
        selected.clear()

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

    # Main game loop
    running = True
    game_over = False
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if not game_over and event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                col = x // (CARD_WIDTH + GAP)
                row = y // (CARD_HEIGHT + GAP)
                index = row * COLS + col
                if not revealed[index] and len(selected) < 2:
                    revealed[index] = True
                    selected.append(index)
                    if len(selected) == 2:
                        check_match(selected, revealed, matched, images)
                elif len(selected) == 1 and selected[0] == index:
                    # If the same card is clicked twice, keep it revealed
                    revealed[index] = True

        draw_board(WINDOW, images, revealed, matched, ROWS, COLS, CARD_WIDTH, CARD_HEIGHT, GAP)
        if len(matched) == ROWS * COLS:
            display_text(WINDOW, "You Win!", FONT, WIDTH, HEIGHT)
            game_over = True

        pygame.display.update()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
