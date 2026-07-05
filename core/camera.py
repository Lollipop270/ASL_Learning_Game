import cv2

class Camera:
    def __init__(self, camera_id=0):
        print(f"[Camera] Trying to open camera {camera_id}...")
        self.cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)  # DSHOW backend for Windows
        if not self.cap.isOpened():
            print(f"[Camera] ERROR: Cannot access camera {camera_id}")
        else:
            print(f"[Camera] Camera {camera_id} opened successfully")

    def read(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("[Camera] Failed to grab frame")
            return ret, frame
        return False, None

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            print("[Camera] Camera released")