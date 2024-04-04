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


class MemoryGame:
    def __init__(self):
        # Initialize Pygame
        pygame.init()

        # Set up display
        self.WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Memory Game")

        # Load images
        self.images, self.card_back = self.load_card_images()  # TODO: should be methods from now on
        # Duplicate images to create pairs
        self.images *= 2
        # Shuffle images
        random.shuffle(self.images)

        # Define font
        self.FONT = pygame.font.SysFont("", 40)

        # Define game variables
        self.revealed = [False] * (ROWS * COLS)
        self.selected = []
        self.matched = []
        self.hints_remaining = MAX_HINTS
        self.hint_index = None

        # Load positive sound
        self.match_sound = self.load_sound("positive_sound.wav")
        # Load win sound
        self.win_sound = self.load_sound("win_sound.wav")

        self.num_players = 0
        self.time_attack = False
        self.voice_control = False
        self.time_limit = INITIAL_TIME_LIMIT

        self.running = True
        self.game_over = False
        self.clock = pygame.time.Clock()

        self.start_time = time.time()  # Start time
        self.voice_index = None
        self.reset_text_rect = None
        self.hint_rect = None

        self.player_turn = 1  # Player 1 starts

    @staticmethod
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

    def speech_recognition(self):
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

        print("speak")
        while True:
            data = stream.read(4096)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                text = recognizer.Result()
                index = json.loads(text)
                print(index["text"])
                index = self.text_to_index(index["text"])

                if isinstance(index, int):
                    return index - 1

        stream.stop_stream()
        stream.close()
        mic.terminate()

    @staticmethod
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

    def draw_board(self, flip_animation=None):
        """
        board drawing and updates for the game play
        :param flip_animation:
        :return:
        """
        self.WINDOW.fill(WHITE)
        if self.card_back is None:
            self.card_back = pygame.image.load("card_back.png")
        for i in range(ROWS):
            for j in range(COLS):
                index = i * COLS + j
                x = j * (CARD_WIDTH + GAP)
                y = i * (CARD_HEIGHT + GAP)

                if (i, j) in self.matched:
                    pygame.draw.rect(self.WINDOW, WHITE, (x, y, CARD_WIDTH, CARD_HEIGHT))
                else:
                    if self.revealed[index] or (flip_animation and flip_animation["index"] == index):
                        if flip_animation and flip_animation["index"] == index:
                            width = flip_animation["width"]
                            x += (CARD_WIDTH - width) / 2  # Center the animating card
                            if flip_animation["phase"] == "hiding":
                                # Show card back shrinking
                                img = pygame.transform.scale(self.card_back, (width, CARD_HEIGHT))
                            else:
                                # Show card face expanding
                                img = pygame.transform.scale(self.images[index], (width, CARD_HEIGHT))
                        else:
                            width = CARD_WIDTH
                            img = pygame.transform.scale(self.images[index], (width, CARD_HEIGHT))
                        self.WINDOW.blit(img, (x, y))
                    else:
                        # Display card back
                        card_back_scaled = pygame.transform.scale(self.card_back, (CARD_WIDTH, CARD_HEIGHT))
                        self.WINDOW.blit(card_back_scaled, (x, y))

    def flip_animation_step(self, index, hint=False):
        """
        flipping card animation for when a card is to be revealed to the player
        :param index:
        :param hint:
        :return:
        """
        width = None
        # First phase: shrinking the card to the middle
        for width in range(CARD_WIDTH, 0, -10):
            self.draw_board(flip_animation={"index": index, "width": width, "phase": "hiding"})
            pygame.display.update()
            pygame.time.wait(25)

        # Swap from the card back to the card face here if necessary
        if not self.revealed[index]:
            self.revealed[index] = True  # This ensures that the card face is shown in the expanding phase

        # Second phase: expanding the card from the middle to full width
        for width in range(0, CARD_WIDTH + 1, 10):
            self.draw_board(flip_animation={"index": index, "width": width, "phase": "revealing"})
            pygame.display.update()
            pygame.time.wait(25)

        # close card shortly after revealed if hint
        if hint:
            self.revealed[index] = False
            self.draw_board(flip_animation={"index": index, "width": width, "phase": "revealing"})
            pygame.display.update()
            pygame.time.wait(25)

    @staticmethod
    def display_text(window, text1, text2, font, position1, position2, color=BLACK):
        """
        helper function to display text
        :param window:
        :param text1:
        :param text2:
        :param font:
        :param position1:
        :param position2:
        :param color:
        :return:
        """
        text_surface1 = font.render(text1, True, color)
        text_rect1 = text_surface1.get_rect(**position1)
        window.blit(text_surface1, text_rect1)

        text_surface2 = font.render(text2, True, color)
        text_rect2 = text_surface2.get_rect(**position2)
        window.blit(text_surface2, text_rect2)

        return text_rect2

    def check_match(self):
        """
        logic function to check if a pair of cards is matched
        :return:
        """
        if len(self.selected) == 2:
            if self.images[self.selected[0]] == self.images[self.selected[1]]:
                self.matched.extend(self.selected)
                self.match_sound.play()  # Play positive sound when a match is made
            else:
                # Hide the cards if they don't match
                self.revealed[self.selected[0]] = False
                self.revealed[self.selected[1]] = False

            if self.num_players == 2 and self.images[self.selected[0]] != self.images[self.selected[1]]:
                self.player_turn = 1 if self.player_turn == 2 else 2
            self.selected.clear()

        if len(self.matched) == len(self.images):
            self.win_sound.play()  # Play win sound when all matches are made

    def win_screen(self, winner):
        """
        a window for when the player wins or losses the game which includes a play again option or game over
        :param winner:
        :return:
        """
        if winner:
            message = "Well Done!"
            button_text = "Play Again"
            message_surface = self.FONT.render(message, True, BLACK)
            button_surface = self.FONT.render(button_text, True, BLACK)
            message_rect = message_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            button_rect = button_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

            pygame.draw.rect(self.WINDOW, GREEN, (WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2))
            self.WINDOW.blit(message_surface, message_rect)
            pygame.draw.rect(self.WINDOW, BLACK, button_rect, 2)
            self.WINDOW.blit(button_surface, button_rect)
        else:
            message = "Game Over!"
            button_text = "Try Again"
            message_surface = self.FONT.render(message, True, BLACK)
            button_surface = self.FONT.render(button_text, True, BLACK)
            message_rect = message_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            button_rect = button_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

            pygame.draw.rect(self.WINDOW, RED, (WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2))
            self.WINDOW.blit(message_surface, message_rect)
            pygame.draw.rect(self.WINDOW, BLACK, button_rect, 2)
            self.WINDOW.blit(button_surface, button_rect)

        return button_rect  # Return the rectangle of the button for click detection

    def get_hint(self):
        """
        helper function to get a random index of a card to be revealed (shortly) for a hint (only for 1 player)
        :return:
        """
        if self.num_players == 1:  # Check if the game is in 1 player mode
            unmatched_indices = [i for i, value in enumerate(self.revealed) if not value and i not in self.matched]
            if unmatched_indices:
                self.hint_index = random.choice(unmatched_indices)

    def hint_processing(self, x, y):
        """
        handle hint processing. revealing a card for a short amount of time
        :return:
        """
        # Check if the click was on the "Hint" button
        # hint_button_rect = hint_surface.get_rect(topleft=(WIDTH - 210, HEIGHT - 38))
        # hint_button_rect = pygame.Rect(WIDTH - 210, HEIGHT - 38, 80, 30)
        if self.hint_rect.collidepoint(x, y):
            self.get_hint()
            if self.hint_index is not None:
                self.hints_remaining -= 1
                pygame.time.set_timer(pygame.USEREVENT, 3000, True)
                self.flip_animation_step(self.hint_index, True)

    def card_selection_processing(self, row, col):
        """
        handling the process of cards selection
        :param row:
        :param col:
        :return: current player's turn
        """
        if self.voice_index:  # if in voice control mode
            index = self.voice_index
        else:  # if in "regular" clicking mode
            index = row * COLS + col
        if not self.revealed[index] and len(self.selected) < 2:
            self.flip_animation_step(index)
            self.revealed[index] = True
            self.selected.append(index)
            if len(self.selected) == 2:  # if the user selected two cards --> updating board and checking for a match
                self.draw_board()
                pygame.display.update()
                time.sleep(1)
                self.check_match()
        elif len(self.selected) == 1 and self.selected[0] == index:
            # If the same card is clicked twice, keep it revealed
            self.revealed[index] = True

        return self.player_turn

    @staticmethod
    def load_card_images():
        """
        load images for the game
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

    def draw_main_win_buttons(self, rect_list):
        """
        drae the buttons which will appear on the main window of the game
        :param rect_list:
        :return:
        """
        # Draw buttons
        for rect in rect_list:
            pygame.draw.rect(self.WINDOW, GREEN, rect)

        # Draw text on buttons
        self.display_text(self.WINDOW, "1 Player", "2 Players", self.FONT, {"center": (200, 175)},
                          {"center": (200, 275)})
        self.display_text(self.WINDOW, "Time Attack", "", self.FONT, {"center": (200, 100)}, {"center": (200, 100)})
        self.display_text(self.WINDOW, "Voice Control", "", self.FONT, {"center": (200, 50)}, {"center": (200, 50)})

    def game_reset(self):
        """
        reset all game parameters for a new game
        :return:
        """
        self.revealed = [False] * (ROWS * COLS)
        self.selected = []
        self.matched = []
        random.shuffle(self.images)  # reshuffle the cards
        self.hints_remaining = MAX_HINTS  # reset hints
        self.hint_index = None
        self.start_time = time.time()  # reset time
        self.game_over = False
        self.player_turn = 1  # reset player turn (for 2 player mode)

    def game_mode_window(self, timer_text):
        """
        handling actual game mode window
        :return:
        """
        self.reset_text_rect = self.display_text(self.WINDOW, timer_text, "Reset", self.FONT,
                                                 position1={"bottomleft": (10, HEIGHT - 10)},
                                                 position2={"bottomright": (WIDTH - 10, HEIGHT - 10)})

        if self.voice_control:
            small_font_size = 25
            small_font = pygame.font.Font(None, small_font_size)  # Create a new Font object for the smaller text

            info_text = "Say 'number' followed by the card number (1-16)"
            info_text_surface = small_font.render(info_text, True, BLACK)
            info_text_rect = info_text_surface.get_rect(midbottom=(WIDTH - 196, HEIGHT - 60))
            self.WINDOW.blit(info_text_surface, info_text_rect)

        # Display "Hint" button
        hint_text = f"Hints: {self.hints_remaining}"
        hint_surface = self.FONT.render(hint_text, True, BLACK)
        self.hint_rect = hint_surface.get_rect(topleft=(WIDTH - 210, HEIGHT - 38))

        if self.num_players == 2 or self.time_attack or self.voice_control:
            pygame.draw.rect(self.WINDOW, RED, self.hint_rect)
        else:
            pygame.draw.rect(self.WINDOW, GREEN, self.hint_rect)
        self.WINDOW.blit(hint_surface, self.hint_rect)

        # Display player turn
        player_turn_text = f"P{self.player_turn}"
        player_turn_surface = self.FONT.render(player_turn_text, True, BLACK)
        player_turn_rect = player_turn_surface.get_rect(midbottom=(WIDTH - 20, HEIGHT // 2))
        self.WINDOW.blit(player_turn_surface, player_turn_rect)

    def process_game_mode(self, buttons):
        """
        handling the mode the user chose
        :param buttons: [one_player_button_rect,two_players_button_rect, time_attack_button_rect, voice_control_button_rect]
        :return:
        """
        while self.num_players == 0 and not self.time_attack and not self.voice_control:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if buttons[0].collidepoint(x, y):
                        self.num_players = 1
                    elif buttons[1].collidepoint(x, y):
                        self.num_players = 2
                    elif buttons[2].collidepoint(x, y):
                        self.time_attack = True
                    elif buttons[3].collidepoint(x, y):
                        self.voice_control = True

            self.WINDOW.fill(WHITE)

            self.draw_main_win_buttons(buttons)
            pygame.display.update()

    def game_loop(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.voice_control:
                    self.voice_index = self.speech_recognition()
                if not self.game_over and event.type == pygame.MOUSEBUTTONDOWN or self.voice_control:
                    x, y = pygame.mouse.get_pos()
                    col = x // (CARD_WIDTH + GAP)
                    row = y // (CARD_HEIGHT + GAP)
                    if col < COLS and row < ROWS or self.voice_index:  # Check if the click is within the grid
                        self.card_selection_processing(row, col)
                    elif self.reset_text_rect is not None and self.reset_text_rect.collidepoint(x, y):
                        self.game_reset()
                    elif self.hints_remaining > 0 and self.num_players == 1:  # handling hints updates (for 1 player mode)
                        self.hint_processing(x, y)
                elif self.game_over and event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if self.reset_text_rect is not None and self.reset_text_rect.collidepoint(x, y):
                        self.game_reset()
                elif event.type == pygame.USEREVENT:
                    # Timer event to hide the hint card
                    self.hint_index = None

            # Calculate elapsed time
            if self.time_attack:
                self.elapsed_time = self.time_limit - (time.time() - self.start_time)
            else:
                self.elapsed_time = time.time() - self.start_time
            minutes = int(self.elapsed_time // 60)
            seconds = int(self.elapsed_time % 60)
            timer_text = f"Time: {minutes:02d}:{seconds:02d}"

            self.draw_board(flip_animation={"index": self.hint_index, "width": CARD_WIDTH, "phase": "hiding"})

            # game stop conditions
            if self.elapsed_time < 0:  # checking if time is over (for attack mode)
                self.game_over = True
                self.reset_text_rect = self.win_screen(winner=False)
            elif len(self.matched) == len(self.images):  # checking if all images were matched
                self.game_over = True
                self.reset_text_rect = self.win_screen(winner=True)
                # Decrement time limit for Time Attack mode
                if self.time_attack:
                    self.time_limit -= TIME_LIMIT_DECREMENT
                    self.game_reset()
            else:  # game continues
                self.game_mode_window(timer_text)

            pygame.display.update()
            self.clock.tick(60)  # frame rate control

        pygame.quit()


def main():
    # create game
    game = MemoryGame()

    # Display window for game modes
    one_player_button_rect = pygame.Rect(100, 150, 200, 50)
    two_players_button_rect = pygame.Rect(100, 250, 200, 50)
    time_attack_button_rect = pygame.Rect(100, 75, 200, 50)
    voice_control_button_rect = pygame.Rect(100, 20, 200, 50)
    rect_list = [one_player_button_rect, two_players_button_rect, time_attack_button_rect, voice_control_button_rect]

    game.process_game_mode(rect_list)

    # game loop
    game.game_loop()


if __name__ == "__main__":
    main()
