import os
import pickle
import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1
)

detector = vision.HandLandmarker.create_from_options(options)

DATA_DIR = './asl_dataset'

data = []
labels = []

try:
    for dir_ in os.listdir(DATA_DIR):
        for img_path in os.listdir(os.path.join(DATA_DIR, dir_)):

            data_aux = []
            x_ = []
            y_ = []

            img = cv2.imread(os.path.join(DATA_DIR, dir_, img_path))
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=img_rgb
            )

            detection_result = detector.detect(mp_image)

            if detection_result.hand_landmarks:
                for hand_landmarks in detection_result.hand_landmarks:

                    for landmark in hand_landmarks:
                        x_.append(landmark.x)
                        y_.append(landmark.y)

                    for landmark in hand_landmarks:
                        data_aux.append(landmark.x - min(x_))
                        data_aux.append(landmark.y - min(y_))

                data.append(data_aux)
                labels.append(dir_)

finally:
    detector.close()   # ✅ IMPORTANT FIX


with open('data.pickle', 'wb') as f:
    pickle.dump({'data': data, 'labels': labels}, f)

print("Dataset saved successfully.")