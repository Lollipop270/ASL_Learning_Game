import customtkinter as ctk
from PIL import Image
import threading
import random
import cv2
from collections import deque
from utils.word_list import WORDS_EASY, WORDS_MEDIUM, WORDS_HARD
from core.inference_classifier import InferenceClassifier


class WordMode(ctk.CTkFrame):
    def __init__(self, parent, camera, app=None):
        super().__init__(parent)

        self.camera = camera
        self.app = app
        self.running = True

        # Word system
        self.current_word = random.choice(WORDS_EASY).upper()
        self.current_index = 0

        # Prediction smoothing
        self.pred_buffer = deque(maxlen=5)

        self.words_completed = 0
        self.total_words = 5

        self.score = 0
        self.correct_letters = 0
        self.total_attempts = 0
        self.pass_count = 0

        # ---------------- Layout ----------------
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        # Camera
        blank = Image.new("RGB", (500, 400), (0, 0, 0))
        self.video_ctk_image = ctk.CTkImage(light_image=blank, dark_image=blank, size=(500, 400))
        self.video_label = ctk.CTkLabel(self, image=self.video_ctk_image)
        self.video_label.grid(row=0, column=0, padx=20, pady=20)

        # Right panel
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.difficulty = "Easy"
        self.configure_difficulty()

        # Optional timer
        self.use_timer = ctk.BooleanVar(value=False)  # checkbox variable
        self.timer_checkbox = ctk.CTkCheckBox(
            self.right_frame,
            text="Enable Timer (Hard Mode)",
            variable=self.use_timer,
            command=self.toggle_timer
        )
        self.timer_checkbox.pack(pady=10)

        # Timer input (seconds per word)
        self.timer_seconds = ctk.IntVar(value=30)
        self.timer_entry = ctk.CTkEntry(
            self.right_frame,
            width=80,
            placeholder_text="Seconds per word",
            textvariable=self.timer_seconds
        )
        self.timer_entry.pack(pady=5)

        # Timer label (visible during gameplay)
        self.timer_label = ctk.CTkLabel(
            self.right_frame,
            text="",
            font=("Arial", 28)
        )
        self.timer_label.pack(pady=10)

        self.word_label = ctk.CTkLabel(self.right_frame, text=f"Word: {self.current_word}", font=("Arial", 40))
        self.word_label.pack(pady=20)

        self.difficulty_menu = ctk.CTkOptionMenu(
            self.right_frame,
            values=["Easy", "Medium", "Hard"],
            command=self.change_difficulty
        )
        self.difficulty_menu.set("Easy")
        self.difficulty_menu.pack(pady=10)

        self.progress_label = ctk.CTkLabel(self.right_frame, text=self.get_progress(), font=("Arial", 40))
        self.progress_label.pack(pady=20)

        self.letter_label = ctk.CTkLabel(self.right_frame, text=f"Sign: {self.get_current_letter()}", font=("Arial", 60))
        self.letter_label.pack(pady=20)

        self.feedback_label = ctk.CTkLabel(
            self.right_frame,
            text="",
            font=("Arial", 28)
        )
        self.feedback_label.pack(pady=10)

        # Pass button
        self.pass_button = ctk.CTkButton(
            self.right_frame,
            text="Pass",
            fg_color="#444444",
            hover_color="#666666",
            command=self.pass_letter
        )
        self.pass_button.pack(pady=10)

        self.home_button = ctk.CTkButton(self.right_frame, text="Home", command=self.go_home)
        self.home_button.pack(pady=20)

        self.classifier = InferenceClassifier()

        # Start camera thread
        self.thread = threading.Thread(target=self.video_loop, daemon=True)
        self.thread.start()

    def get_current_letter(self):
        return self.current_word[self.current_index]

    def get_progress(self):
        progress = ""

        for i in range(len(self.current_word)):
            if i < self.current_index:
                progress += self.current_word[i] + " "
            else:
                progress += "_ "

        return progress

    def video_loop(self):
        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_small = cv2.resize(frame_rgb, (500, 400))
            pil_img = Image.fromarray(frame_small)

            self.after(0, self.update_video_frame, pil_img)

            prediction = self.classifier.predict(frame_rgb)

            if prediction:
                self.pred_buffer.append(prediction)

                if len(self.pred_buffer) == self.pred_buffer.maxlen:
                    final_pred = max(set(self.pred_buffer), key=self.pred_buffer.count)
                    self.after(0, self.handle_prediction, final_pred)

            cv2.waitKey(1)

    def update_video_frame(self, pil_img):
        if not self.running:
            return
        self.video_ctk_image.configure(light_image=pil_img, dark_image=pil_img)
        self.video_label.configure(image=self.video_ctk_image)

    def handle_prediction(self, prediction):
        expected = self.get_current_letter()
        self.total_attempts += 1

        if prediction.upper() == expected:

            self.correct_letters += 1
            self.current_index += 1

            # Word finished
            if self.current_index >= len(self.current_word):

                self.words_completed += 1
                self.score += 1

                self.show_feedback("Word Complete!", "green")

                # Stop after 5 words
                if self.words_completed >= self.total_words:
                    self.end_game()
                    return

                # Load next word
                self.current_word = random.choice(self.word_list).upper()
                self.current_index = 0

                self.word_label.configure(text=f"Word: {self.current_word}")

                # Reset timer if enabled
                if self.use_timer.get():
                    self.time_left = self.timer_seconds.get()

            else:
                self.show_feedback("Correct", "green")

            self.progress_label.configure(text=self.get_progress())
            self.letter_label.configure(text=f"Sign: {self.get_current_letter()}")

        else:
            self.show_feedback("Try Again", "red")

    def go_home(self):
        self.stop()
        if self.app:
            self.app.show_main_menu()

    def stop(self):
        self.running = False
        if hasattr(self, "thread") and self.thread.is_alive():
            self.thread.join(timeout=0.5)

        if hasattr(self, "classifier"):
            self.classifier.close()

    def pass_letter(self):
        if not self.running:
            return

        self.pass_count += 1
        self.total_attempts += 1

        self.current_index += 1

        if self.current_index >= len(self.current_word):

            self.words_completed += 1

            if self.words_completed >= self.total_words:
                self.end_game()
                return

            self.current_word = random.choice(self.word_list).upper()
            self.current_index = 0

            self.word_label.configure(text=f"Word: {self.current_word}")

            # Reset timer if enabled
            if self.use_timer.get():
                self.time_left = self.timer_seconds.get()

        self.progress_label.configure(text=self.get_progress())
        self.letter_label.configure(text=f"Sign: {self.get_current_letter()}")

        self.show_feedback("Skipped", "orange")

    def show_feedback(self, text, color="white"):
        if not self.running:
            return
        self.feedback_label.configure(text=text, text_color=color)
        if hasattr(self, "feedback_timer"):
            self.after_cancel(self.feedback_timer)
        def clear_feedback():
            if self.running and self.feedback_label.winfo_exists():
                self.feedback_label.configure(text="")

        self.feedback_timer = self.after(2000, clear_feedback)

    def configure_difficulty(self):
        if self.difficulty == "Easy":
            self.word_list = WORDS_EASY
        elif self.difficulty == "Hard":
            self.word_list = WORDS_HARD
        else:  # Medium
            self.word_list = WORDS_MEDIUM
        self.current_word = random.choice(self.word_list).upper()
        self.current_index = 0

    def change_difficulty(self, value):
        self.difficulty = value
        self.configure_difficulty()

        self.word_label.configure(text=f"Word: {self.current_word}")
        self.progress_label.configure(text=self.get_progress())
        self.letter_label.configure(text=f"Sign: {self.get_current_letter()}")

    def end_game(self):

        self.running = False

        for widget in self.winfo_children():
            widget.destroy()

        score_frame = ctk.CTkFrame(self)
        score_frame.pack(fill="both", expand=True, padx=20, pady=20)

        accuracy = 0
        if self.total_attempts > 0:
            accuracy = round((self.correct_letters / self.total_attempts) * 100, 2)

        ctk.CTkLabel(
            score_frame,
            text="Game Over!",
            font=("Arial", 50, "bold")
        ).pack(pady=20)

        ctk.CTkLabel(
            score_frame,
            text=f"Words Completed: {self.words_completed}",
            font=("Arial", 36)
        ).pack(pady=10)

        ctk.CTkLabel(
            score_frame,
            text=f"Passes: {self.pass_count}",
            font=("Arial", 30)
        ).pack(pady=10)

        ctk.CTkLabel(
            score_frame,
            text=f"Accuracy: {accuracy}%",
            font=("Arial", 30)
        ).pack(pady=10)

        ctk.CTkButton(
            score_frame,
            text="Play Again",
            command=self.restart_game
        ).pack(pady=10)

        ctk.CTkButton(
            score_frame,
            text="Home",
            command=self.go_home
        ).pack(pady=10)

    def restart_game(self):
        if hasattr(self, "stop"):
            self.stop()

        if self.app:
            from ui.word_mode import WordMode
            self.app.switch_mode(
                WordMode(
                    self.app.ui_container,
                    camera=self.camera,
                    app=self.app
                )
            )

    def stop(self):
        self.running = False

        if hasattr(self, "feedback_timer"):
            try:
                self.after_cancel(self.feedback_timer)
            except:
                pass

        if hasattr(self, "thread") and self.thread.is_alive():
            self.thread.join(timeout=0.5)

        if hasattr(self, "classifier"):
            self.classifier.close()

    def toggle_timer(self):
        if self.use_timer.get():
            self.start_timer()
        else:
            self.stop_timer()

    def start_timer(self):
        self.time_left = self.timer_seconds.get()
        self.update_timer()

    def stop_timer(self):
        self.time_left = None
        self.timer_label.configure(text="")

    def update_timer(self):
        if not self.running or not self.use_timer.get():
            return

        if self.time_left > 0:
            # Update timer label
            self.timer_label.configure(text=f"Time: {self.time_left}")
            self.time_left -= 1
            self.after(1000, self.update_timer)
        else:
            # Timer reached zero → automatically skip current word
            self.show_feedback("Time's up!", "orange")
            self.pass_word()  # reuse existing logic for skipping

            # Reset timer for the next word if game is still running
            if self.running and self.words_completed < self.total_words:
                self.time_left = self.timer_seconds.get()
                self.after(1000, self.update_timer)

    def pass_word(self):
    
        if not self.running:
            return

        self.pass_count += 1
        self.words_completed += 1

        # Show feedback
        self.show_feedback("Word Skipped!", "orange")

        # Stop if reached total words
        if self.words_completed >= self.total_words:
            self.end_game()
            return

        # Load next word
        self.current_word = random.choice(self.word_list).upper()
        self.current_index = 0
        self.word_label.configure(text=f"Word: {self.current_word}")

        # Update next letter display
        self.letter_label.configure(text=f"Sign: {self.get_current_letter()}")

        # Reset timer if enabled
        if self.use_timer.get():
            self.time_left = self.timer_seconds.get()