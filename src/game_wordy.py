import wordy
import pytesseract
import random
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class Letter:
    """A Letter indicates a single English letter from a guess.

    It has methods and attributes to describe whether the letter was in (or in the correct place)
    in the hidden target word.

    Attributes:
        letter: a single English letter from a guess.
        in_correct_place: a boolean indicating whether the letter is in the correct place.
        in_word: a boolean indicating whether the letter is in the hidden target word.
    """
    def __init__(self, letter: str) -> None:
        """Initializes a Letter object with both boolean values set to False.

        Arguments:
            letter: a single English letter from a guess.
        """
        self.letter: str = letter
        self.in_correct_place: bool = False
        self.in_word: bool = False

    def is_in_correct_place(self) -> bool:
        """A simple getter function to check if the letter is in the correct place."""
        return self.in_correct_place

    def is_in_word(self) -> bool:
        """A simple getter function to check if the letter is in the word."""
        return self.in_word

class Bot:
    """The Bot is the game playing agent.

     This class has two substantive methods in it:
        1) make_guess which returns a string that is evaluated by the GameEngine
        2) record_guess_results which takes the evaluation done by the GameEngine in order to ensure
        that the same guess is never made twice and that the bot "learns" from previous guesses.

    Attributes:
        word_list: a list of legal words available in the "assets/words.txt" file.
        display_spec: display specifications from DisplaySpecification class.
    """
    def __init__(self, words_file: str = "assets/words.txt", display_spec: wordy.DisplaySpecification = wordy.DisplaySpecification) -> None:
        """Initializes a Bot object with a list of English words it can use.

        Arguments:
            words_file: a path to file with the list of word the bot is allowed to use. Default is "assets/words.txt".
            display_spec: display specifications from DisplaySpecification class.
        """
        self.word_list: list[str] = list(map(lambda x: x.strip().upper(), open(words_file, "r").readlines()))
        self.display_spec: wordy.DisplaySpecification = display_spec

    def process_image(self, guess_image: Image) -> (list[Letter], int):
        """Decodes guessed word and feedback from the image to Letter objects with OCR.

        This method splits the image into multiple images containing only one word. Then it extracts the letter
        with OCR and feedback from the color information, records this information in Letter objects and
        returns the list of Letter objects with the word length.

        Arguments:
            guess_image: an Image object with letters and background colors for up to 5 attempts.
        """
        letters = []
        left = 0
        top = 0
        step_width = self.display_spec.block_width
        step_height = self.display_spec.block_height
        img_width, img_height = guess_image.size
        chars = img_width // step_width
        guesses = img_height // step_height

        for g in range(guesses):
            for c in range(chars):
                img = guess_image.crop((left, top, left + step_width, top + step_height))  # crop the image with one letter
                img_ocr = img.convert('L').point(lambda x: 255 if x > 230 else 0, mode='1') # convert the image to grayscale for OCR
                char: str = pytesseract.image_to_string(img_ocr, lang='eng', config='--psm 10')[0].upper() # extract letter from the image
                letter: Letter = Letter(char) # create a new Letter object

                hex_value: str = tuple_to_str(img.getpixel((1, 1)))  # get pixel and convert color to HEX string
                if hex_value == self.display_spec.correct_location_color:
                    letter.in_correct_place = True
                    letter.in_word = True
                elif hex_value == self.display_spec.incorrect_location_color:
                    letter.in_word = True  # other parameters are correctly set to False when the Letter object is initiated

                letters.append(letter)  # add the letter to our list of letters

                left += step_width + self.display_spec.space_between_letters # move to the next block
            top += step_height # move to the next line
            left = 0 # start at the far left again

        return letters, chars

    def guess_results(self, guess_image: Image) -> str:
        """Returns a string that is evaluated by the GameEngine.

        Ensures that the same guess is never made twice and the bot "learns" from the board feedback.

        Arguments:
            guess_image: an image with feedback on the results of the guess.
        """
        letter_info, word_length = self.process_image(guess_image) # get the list of Letter object with game state
        words = self.word_list # make a copy of word_list for loops
        idx = 0 # index is used to get the current letter out of the string for comparison
        for let in letter_info:
            if let.is_in_word(): # only words that satisfy conditions remain in the list
                words = [word for word in words if let.letter in word]
                if let.is_in_correct_place():
                    words = [word for word in words if let.letter in word[idx]]
                else:
                    words = [word for word in words if let.letter not in word[idx]]
            else:
                words = [word for word in words if let.letter not in word]

            idx += 1
            if idx >= word_length: # it means we will start working with the second guess on the next loop cycle
                idx = 0

        if len(words) == 0:
            return ""
        else:
            return random.choice(words) # return a random word in the remaining list of possible words

def tuple_to_str(pixels: tuple) -> str:
    """Translates the tuple representation into a hex string equivalent.

    Arguments:
        pixels: a tuple with 4 numbers between 0 and 255 representing the pixels in the game board (R, G, B, A).
    """
    h: str = '#%02x%02x%02x' % (pixels[0:3])
    return h.upper()

# Play game
bot = Bot()

# Get an image of the current board state from wordy.
# Note that the image contains some number of random guesses (always fewer than 5 guesses).
image = wordy.get_board_state()
image.show()

# Create a new "good" guess based on the image and rules of wordy
new_guess = bot.guess_results(image)
print(f'Bot guess: {new_guess}')
wordy.make_guess(new_guess)