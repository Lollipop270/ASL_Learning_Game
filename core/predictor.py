import pickle
import numpy as np

class Predictor:
    def __init__(self, model_path):
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)['model']

    def predict(self, hand_landmarks):
        # Flatten landmarks for prediction
        data = []
        x_list, y_list = [], []
        for lm in hand_landmarks:
            x_list.append(lm.x)
            y_list.append(lm.y)
        for lm in hand_landmarks:
            data.append(lm.x - min(x_list))
            data.append(lm.y - min(y_list))
        data = np.asarray(data)
        return self.model.predict([data])[0]