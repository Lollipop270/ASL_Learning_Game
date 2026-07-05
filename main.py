import customtkinter as ctk
from core.camera import Camera
from core.detector import HandDetector
from core.predictor import Predictor
from core.game_logic import GameLogic
from ui.main_menu import MainMenu
from ui.learn_mode import LearnMode
from ui.test_mode import TestMode
from utils.config import CHARACTERS, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.word_mode import WordMode

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.title("ASL Learning Game")

        # ---------------- Initialize shared resources ----------------
        print("[App] Initializing camera...")
        self.camera = Camera()
        print("[App] Initializing hand detector...")
        self.detector = HandDetector()
        print("[App] Initializing predictor...")
        self.predictor = Predictor("assets/models/asl_model.p")
        self.game_logic = GameLogic(CHARACTERS)

        # UI container
        self.ui_container = ctk.CTkFrame(self)
        self.ui_container.pack(fill="both", expand=True, padx=20, pady=20)

        self.current_ui = None

        # Show main menu
        self.show_main_menu()

    # ---------------- Main Menu ----------------
    def show_main_menu(self):
        self.switch_mode(MainMenu(self.ui_container, self.start_learn, self.start_test, self.start_word))

    # ---------------- Learn Mode ----------------
    def start_learn(self):
        learn_mode = LearnMode(
            self.ui_container,
            characters=CHARACTERS,
            camera=self.camera,
            detector=self.detector,
            predictor=self.predictor
        )
        self.switch_mode(learn_mode)

    # ---------------- Test Mode ----------------
    def start_test(self):
        self.game_logic.start_test()
        test_mode = TestMode(
            self.ui_container,
            game_logic=self.game_logic,
            camera=self.camera,
            detector=self.detector,
            predictor=self.predictor
        )
        self.switch_mode(test_mode)

    # ---------------- Helper ----------------
    def switch_mode(self, new_ui):
        # Stop previous mode
        if self.current_ui:
            if hasattr(self.current_ui, "stop"):
                self.current_ui.stop()
            self.current_ui.destroy()
            self.current_ui = None

        # Add new UI
        self.current_ui = new_ui
        self.current_ui.pack(fill="both", expand=True)
        self.fade_in()

    def fade_in(self, steps=15, delay=15):
        self.attributes("-alpha", 0.0)

        def _fade(step=0):
            alpha = step / steps
            self.attributes("-alpha", alpha)
            if step < steps:
                self.after(delay, _fade, step + 1)

        _fade()

    # ---------------- Close Application ----------------
    def on_close(self):
        print("[App] Closing application...")
        if self.current_ui and hasattr(self.current_ui, "stop"):
            self.current_ui.stop()
        self.camera.release()
        if hasattr(self.detector, "close"):
            self.detector.close()
        self.destroy()

    # ---------------- Test Mode ----------------
    def start_test(self):
        self.game_logic.start_test()
        test_mode = TestMode(
            self.ui_container,
            game_logic=self.game_logic,
            camera=self.camera,
            detector=self.detector,
            predictor=self.predictor,
            app=self  # <-- pass App instance here
        )
        self.switch_mode(test_mode)

    def start_word(self):
        word_mode = WordMode(
            self.ui_container,
            camera=self.camera,
            app=self
        )
        self.switch_mode(word_mode)

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()