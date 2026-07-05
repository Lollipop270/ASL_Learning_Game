import pickle
import cv2
import mediapipe as mp
import numpy as np
import sys
import os

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# ---------------------------
# Fix for PyInstaller paths
# ---------------------------
def resource_path(relative_path):
    """ Get absolute path to resource (works for dev and PyInstaller) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Load trained model
model_path = resource_path("model.p")
task_path = resource_path("hand_landmarker.task")

model_dict = pickle.load(open(model_path, 'rb'))
model = model_dict['model']


# Create HandLandmarker
base_options = python.BaseOptions(model_asset_path=task_path)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1
)

detector = vision.HandLandmarker.create_from_options(options)


# Start webcam
cap = cv2.VideoCapture(0)


try:
    while True:

        ret, frame = cap.read()
        if not ret:
            break

        H, W, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_rgb
        )

        detection_result = detector.detect(mp_image)

        if detection_result.hand_landmarks:

            for hand_landmarks in detection_result.hand_landmarks:

                x_ = []
                y_ = []
                data_aux = []

                for landmark in hand_landmarks:
                    x_.append(landmark.x)
                    y_.append(landmark.y)

                for landmark in hand_landmarks:
                    data_aux.append(landmark.x - min(x_))
                    data_aux.append(landmark.y - min(y_))

                if len(data_aux) == 42:
                    prediction = model.predict([np.asarray(data_aux)])
                    predicted_character = prediction[0]

                    x1 = int(min(x_) * W) - 10
                    y1 = int(min(y_) * H) - 10
                    x2 = int(max(x_) * W) + 10
                    y2 = int(max(y_) * H) + 10

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    cv2.putText(frame, predicted_character,
                                (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1.3, (0, 255, 0), 3, cv2.LINE_AA)

        cv2.imshow("Hand Gesture Recognition", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    detector.close()