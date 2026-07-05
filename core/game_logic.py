import random

class GameLogic:
    def __init__(self, characters):
        self.characters = characters
        self.current = None
        self.score = 0
        self.start_test()

    def start_test(self):
        """Initialize a new test session."""
        self.score = 0
        self.next_letter()

    def next_letter(self):
        """Pick a new letter randomly from the character set."""
        self.current = random.choice(self.characters)

    def increment_score(self):
        self.score += 1
        return self.score