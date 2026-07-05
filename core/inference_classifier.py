import pickle
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import sys
import os


# ---------------------------
# Resource path (PyInstaller safe)
# ---------------------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class InferenceClassifier:
    def __init__(self):
        # Load trained classifier
        model_path = resource_path("asl_model.p")
        task_path = resource_path("hand_landmarker.task")

        model_dict = pickle.load(open(model_path, 'rb'))
        self.model = model_dict['model']

        # Setup MediaPipe Tasks HandLandmarker
        base_options = python.BaseOptions(model_asset_path=task_path)

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1
        )

        self.detector = vision.HandLandmarker.create_from_options(options)

    def predict(self, frame_rgb):
        """
        frame_rgb must be RGB numpy array
        Returns predicted character or None
        """
        try:
            # ✅ Correct way to create MP image in Tasks API
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=frame_rgb
            )

            result = self.detector.detect(mp_image)

            if not result.hand_landmarks:
                return None

            hand_landmarks = result.hand_landmarks[0]

            x_, y_ = [], []
            data_aux = []

            for lm in hand_landmarks:
                x_.append(lm.x)
                y_.append(lm.y)

            for lm in hand_landmarks:
                data_aux.append(lm.x - min(x_))
                data_aux.append(lm.y - min(y_))

            if len(data_aux) == 42:
                prediction = self.model.predict([np.asarray(data_aux)])
                return prediction[0]

        except Exception as e:
            print("[InferenceClassifier] Detection error:", e)

        return None

    def close(self):
        if hasattr(self.detector, "close"):
            self.detector.close()