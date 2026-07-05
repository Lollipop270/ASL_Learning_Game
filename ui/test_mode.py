import customtkinter as ctk
from PIL import Image
import threading
import random
import cv2
from core.inference_classifier import InferenceClassifier
import mediapipe as mp
import numpy as np
from collections import deque

class TestMode(ctk.CTkFrame):
    def __init__(self, parent, game_logic, camera, detector=None, predictor=None, app=None):
        super().__init__(parent)

        self.app = app
        self.game_logic = game_logic
        self.camera = camera

        self.running = True
        self.frame_count = 0
        self.score = 0

        # ---------------- Difficulty ----------------
        self.difficulty = "Medium"  # Default
        self.configure_difficulty()

        # ---------------- Layout ----------------
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---------------- Video Feed ----------------
        blank = Image.new("RGB", (500, 400), (0, 0, 0))
        self.video_ctk_image = ctk.CTkImage(light_image=blank, dark_image=blank, size=(500, 400))
        self.video_label = ctk.CTkLabel(self, image=self.video_ctk_image)
        self.video_label.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # ---------------- Right Panel ----------------
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.right_frame.grid_rowconfigure(10, weight=1)

        # Difficulty selector
        self.difficulty_menu = ctk.CTkOptionMenu(
            self.right_frame,
            values=["Easy", "Medium", "Hard"],
            command=self.change_difficulty
        )
        self.difficulty_menu.set("Medium")
        self.difficulty_menu.pack(pady=10)

        # Timer display
        self.timer_label = ctk.CTkLabel(self.right_frame, text=f"Time: {self.time_left}", font=("Arial", 28))
        self.timer_label.pack(pady=10)

        # Current letter
        self.current_letter = random.choice(self.letters)
        self.letter_label = ctk.CTkLabel(
            self.right_frame,
            text=f"Sign: {self.current_letter.upper()}",
            font=("Arial", 60, "bold")
        )
        self.letter_label.pack(pady=20)

        # Score
        self.score_label = ctk.CTkLabel(self.right_frame, text=f"Score: {self.score}", font=("Arial", 30))
        self.score_label.pack(pady=10)

        self.correct_answers = 0
        self.total_attempts = 0
        self.pass_count = 0

        # Feedback
        self.feedback_label = ctk.CTkLabel(self.right_frame, text="Show the sign", font=("Arial", 28))
        self.feedback_label.pack(pady=20)

        # Pass button
        self.pass_button = ctk.CTkButton(
            self.right_frame,
            text="Pass",
            fg_color="#444444",
            hover_color="#666666",
            command=self.pass_letter
        )
        self.pass_button.pack(pady=10)

        # Home button
        self.home_button = ctk.CTkButton(
            self.right_frame,
            text="Home",
            command=self.go_home
        )
        self.home_button.pack(pady=10)

        # ---------------- Classifier ----------------
        self.classifier = InferenceClassifier()
        self.pred_buffer = deque(maxlen=5)

        # Start timer
        self.update_timer()

        # Start video thread
        self.thread = threading.Thread(target=self.video_loop, daemon=True)
        self.thread.start()

    # ---------------- Difficulty Settings ----------------
    def configure_difficulty(self):
        if self.difficulty == "Easy":
            self.required_streak = 2
            self.time_left = 90
            self.letters = self.game_logic.characters[:10]
        elif self.difficulty == "Hard":
            self.required_streak = 4
            self.time_left = 45
            self.letters = self.game_logic.characters
        else:  # Medium
            self.required_streak = 3
            self.time_left = 60
            self.letters = self.game_logic.characters

        self.correct_streak = 0
        self.last_prediction = None

    def change_difficulty(self, value):
        self.difficulty = value
        self.configure_difficulty()
        self.score = 0
        self.score_label.configure(text=f"Score: {self.score}")
        self.current_letter = random.choice(self.letters)
        self.letter_label.configure(text=f"Sign: {self.current_letter.upper()}")

    # ---------------- Timer ----------------
    def update_timer(self):
        if not self.running:
            return
        if self.time_left > 0:
            self.timer_label.configure(text=f"Time: {self.time_left}")
            self.time_left -= 1
            self.after(1000, self.update_timer)
        else:
            self.end_game()

    # ---------------- Video Loop ----------------
    def video_loop(self):
        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_small = cv2.resize(frame_rgb, (500, 400))
            pil_img = Image.fromarray(frame_small)

            # Update video frame
            self.after(0, self.update_video_frame, pil_img)

            self.frame_count += 1
            if self.frame_count % 3 == 0:
                try:
                    # Convert to MediaPipe Image
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
                    result = self.classifier.detector.detect(mp_image)

                    if result.hand_landmarks:
                        for hand_landmarks in result.hand_landmarks:
                            # Flatten landmarks for prediction
                            x_list, y_list = [], []
                            for lm in hand_landmarks:
                                x_list.append(lm.x)
                                y_list.append(lm.y)

                            data = []
                            for lm in hand_landmarks:
                                data.append(lm.x - min(x_list))
                                data.append(lm.y - min(y_list))
                            data = np.asarray(data)

                            prediction = self.classifier.model.predict([data])[0]
                            if prediction:
                                self.pred_buffer.append(prediction)
                                if len(self.pred_buffer) == self.pred_buffer.maxlen:
                                    final_pred = max(set(self.pred_buffer), key=self.pred_buffer.count)
                                    self.after(0, self.handle_prediction, final_pred)

                except Exception as e:
                    print("[TestMode] Prediction error:", e)

            cv2.waitKey(1)

    def update_video_frame(self, pil_img):
        if not self.running:
            return
        try:
            self.video_ctk_image.configure(light_image=pil_img, dark_image=pil_img)
            self.video_label.configure(image=self.video_ctk_image)
        except:
            pass

    # ---------------- Prediction Logic ----------------
    def handle_prediction(self, prediction):
        predicted = prediction.lower()
        target = self.current_letter.lower()

        if predicted != self.last_prediction:
            self.correct_streak = 0
            self.last_prediction = predicted

        if predicted == target:
            self.correct_streak += 1
            if self.correct_streak >= self.required_streak:
                self.score += 1
                self.correct_answers += 1
                self.total_attempts += 1
                self.score_label.configure(text=f"Score: {self.score}")

                self.correct_streak = 0
                self.last_prediction = None
                self.current_letter = random.choice(self.letters)
                self.letter_label.configure(text=f"Sign: {self.current_letter.upper()}")

    # ---------------- Buttons ----------------
    def pass_letter(self):
        if not self.running:
            return
        self.pass_count += 1
        self.total_attempts += 1
        self.correct_streak = 0
        self.last_prediction = None

        new_letter = random.choice(self.letters)
        while new_letter == self.current_letter:
            new_letter = random.choice(self.letters)

        self.current_letter = new_letter
        self.letter_label.configure(text=f"Sign: {self.current_letter.upper()}")
        self.feedback_label.configure(text="Skipped", text_color="orange")

    def go_home(self):
        self.stop()
        if self.app:
            self.app.show_main_menu()

    def restart_game(self):
        if hasattr(self, "stop"):
            self.stop()
        if self.app:
            self.app.start_test()

    # ---------------- Stop ----------------
    def stop(self):
        self.running = False
        if hasattr(self, "thread") and self.thread.is_alive():
            self.thread.join(timeout=0.5)
        if hasattr(self, "classifier"):
            self.classifier.close()

    # ---------------- End Game ----------------
    def end_game(self):
        self.running = False
        for widget in self.winfo_children():
            widget.destroy()

        score_frame = ctk.CTkFrame(self)
        score_frame.pack(fill="both", expand=True, padx=20, pady=20)

        accuracy = 0
        if self.total_attempts > 0:
            accuracy = round((self.correct_answers / self.total_attempts) * 100, 2)

        ctk.CTkLabel(score_frame, text="Game Over!", font=("Arial", 50, "bold")).pack(pady=20)
        ctk.CTkLabel(score_frame, text=f"Score: {self.score}", font=("Arial", 36)).pack(pady=10)
        ctk.CTkLabel(score_frame, text=f"Passes: {self.pass_count}", font=("Arial", 30)).pack(pady=10)
        ctk.CTkLabel(score_frame, text=f"Accuracy: {accuracy}%", font=("Arial", 30)).pack(pady=10)

        ctk.CTkButton(score_frame, text="Play Again", command=self.restart_game).pack(pady=10)
        ctk.CTkButton(score_frame, text="Home", command=self.go_home).pack(pady=10)