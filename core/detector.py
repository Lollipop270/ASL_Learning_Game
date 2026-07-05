import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os
import sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class HandDetector:
    def __init__(self):

        model_path = resource_path("hand_landmarker.task")

        base_options = python.BaseOptions(model_asset_path=model_path)

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1
        )

        self.detector = vision.HandLandmarker.create_from_options(options)

    def detect(self, frame_rgb):

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_rgb
        )

        result = self.detector.detect(mp_image)

        if not result.hand_landmarks:
            return []

        hands = []

        for hand in result.hand_landmarks:
            hands.append(hand)

        return hands

    def close(self):
        if hasattr(self.detector, "close"):
            self.detector.close()