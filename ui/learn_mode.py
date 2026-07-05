import customtkinter as ctk
from PIL import Image
import threading
import random
import cv2
from collections import deque
from utils.resource_path import resource_path


class LearnMode(ctk.CTkFrame):
    def __init__(self, parent, characters, camera, detector, predictor):
        super().__init__(parent)

        self.characters = characters
        self.camera = camera
        self.detector = detector
        self.predictor = predictor
        self.running = True
        self.frame_count = 0
        self.current_letter = random.choice(self.characters)

        # Prediction smoothing
        self.pred_buffer = deque(maxlen=8)

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

        # Letter display
        self.letter_label = ctk.CTkLabel(self.right_frame, text=self.current_letter.upper(),
                                         font=("Arial", 80, "bold"))
        self.letter_label.place(relx=0.5, y=10, anchor="n")

        # Letter image
        self.letter_img_label = ctk.CTkLabel(self.right_frame)
        self.letter_img_label.place(relx=0.5, y=120, anchor="n")
        self.show_letter_image(self.current_letter)

        # ---------------- Feedback messages (empty) ----------------
        self.feedback_label = ctk.CTkLabel(
            self.right_frame,
            text="",  # empty since we removed Correct/Try Again/Skipped
            font=("Arial", 30),
            wraplength=280,
            justify="center"
        )
        self.feedback_label.place(relx=0.5, y=380, anchor="n")  # properly aligned under letter image

        # Hints for A–Z and numbers
        self.hints_label = ctk.CTkLabel(
            self.right_frame,
            text="",
            font=("Arial", 22),
            text_color="blue",
            wraplength=280,
            justify="center"
        )
        self.hints_label.place(relx=0.5, y=430, anchor="n")  # aligned under feedback_label

        # ---------------- Buttons ----------------
        self.pass_button = ctk.CTkButton(self.right_frame, text="Pass",
                                         fg_color="#444444", hover_color="#666666",
                                         command=self.pass_letter)
        self.pass_button.place(relx=0.5, y=490, anchor="center")

        self.home_button = ctk.CTkButton(self.right_frame, text="Home", command=self.go_home)
        self.home_button.place(relx=0.5, y=540, anchor="center")

        # Start video thread
        self.thread = threading.Thread(target=self.video_loop, daemon=True)
        self.thread.start()

    # ---------------- Show letter image ----------------
    def show_letter_image(self, letter):
        try:
            img_path = resource_path(f"assets/images/{letter.lower()}.jpeg")
            pil_img = Image.open(img_path).resize((250, 250))
            self.letter_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(250, 250))
            self.letter_img_label.configure(image=self.letter_image)
            self.letter_label.configure(text=letter.upper())
        except:
            pass

    # ---------------- Update prediction ----------------
    def update_prediction(self, prediction):
        predicted = prediction.lower()
        target = self.current_letter.lower()

        if predicted == target:
            # Do not show "Correct!" message
            self.current_letter = random.choice(self.characters)
            self.show_letter_image(self.current_letter)
            self.hints_label.configure(text="")
            self.pred_buffer.clear()
        elif prediction:
            # Do not show "Try Again" message
            self.shake_label(self.feedback_label)  # optional shake animation
            self.hints_label.configure(text=self.get_hint(self.current_letter))

    # ---------------- Shake animation ----------------
    def shake_label(self, label, magnitude=5, times=4):
        original_x = label.winfo_x()
        original_y = label.winfo_y()

        def _shake(count=0):
            if count >= times:
                label.place_configure(x=original_x, y=original_y)
                return
            offset = magnitude if count % 2 == 0 else -magnitude
            label.place_configure(x=original_x + offset, y=original_y)
            self.after(50, _shake, count + 1)

        _shake()

    # ---------------- Hints for A–Z and 0–9 ----------------
    def get_hint(self, char):
        char = char.lower()
        number_hints = {
            "0": "Make a circle with your fingers",
            "1": "Point index finger up",
            "2": "Index and middle fingers up",
            "3": "Thumb + index + middle",
            "4": "All fingers except thumb",
            "5": "Open hand, all fingers up",
            "6": "Thumb touches pinky",
            "7": "Thumb touches ring finger",
            "8": "Thumb touches middle finger",
            "9": "Thumb touches index finger"
        }
        letter_hints = {
            "a": "Make a fist, thumb on the side",
            "b": "All fingers up, thumb across palm",
            "c": "Curve your hand like a C",
            "d": "Index up, other fingers in a circle",
            "e": "Curl fingers, thumb across",
            "f": "Thumb and index make a circle, other fingers up",
            "g": "Index and thumb pointing sideways",
            "h": "Index and middle fingers pointing sideways",
            "i": "Pinky up, other fingers down",
            "j": "Draw a J with pinky",
            "k": "Index and middle fingers up, thumb between",
            "l": "Index up, thumb out",
            "m": "Fingers together, thumb under",
            "n": "Fingers together, thumb under index",
            "o": "Make an O with fingers",
            "p": "Index and middle down, thumb out",
            "q": "Thumb and index pointing down",
            "r": "Cross index and middle fingers",
            "s": "Fist, thumb over fingers",
            "t": "Thumb under index finger",
            "u": "Index and middle fingers up together",
            "v": "Index and middle fingers up in V",
            "w": "Index, middle, ring fingers up",
            "x": "Index bent, others down",
            "y": "Thumb and pinky out",
            "z": "Draw a Z with index finger"
        }

        if char in number_hints:
            return f"Hint: {number_hints[char]}"
        elif char in letter_hints:
            return f"Hint: {letter_hints[char]}"
        return ""

    # ---------------- Video Loop ----------------
    def video_loop(self):
        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_small = cv2.resize(frame_rgb, (500, 400))
            pil_img = Image.fromarray(frame_small)
            self.after(0, self.update_video_frame, pil_img)

            self.frame_count += 1

            if self.frame_count % 3 == 0:
                try:
                    hands = self.detector.detect(frame_rgb)

                    for hand_landmarks in hands:
                        prediction = self.predictor.predict(hand_landmarks)
                        if prediction:
                            self.after(0, self.update_prediction, prediction)

                except Exception as e:
                    print("[LearnMode] Prediction error:", e)

            cv2.waitKey(1)

    # ---------------- Update video frame ----------------
    def update_video_frame(self, pil_img):
        if not self.running:
            return
        try:
            self.video_ctk_image.configure(light_image=pil_img, dark_image=pil_img)
            self.video_label.configure(image=self.video_ctk_image)
        except:
            pass

    # ---------------- Buttons ----------------
    def pass_letter(self):
        if not self.running:
            return
        self.current_letter = random.choice(self.characters)
        self.show_letter_image(self.current_letter)
        self.hints_label.configure(text="")
        self.pred_buffer.clear()
        # Removed "Skipped" message

    def go_home(self):
        self.stop()
        app = self.master.master
        app.show_main_menu()

    # ---------------- Stop ----------------
    def stop(self):
        self.running = False
        if hasattr(self, "thread") and self.thread.is_alive():
            self.thread.join(timeout=0.5)