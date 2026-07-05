import cv2

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # <-- force DirectShow
if not cap.isOpened():
    print("Cannot open camera")
else:
    print("Camera opened successfully")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        cv2.imshow("Camera Test", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
            break
    cap.release()
    cv2.destroyAllWindows()