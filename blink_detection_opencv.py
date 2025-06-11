import cv2
import time
import numpy as np
import threading


blink_rate_lock = threading.Lock()
blink_rate_storage = {}
stop_event = threading.Event()

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
upperbody_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')

def detect_symmetry_and_shoulders(frame, gray, faces):
    for (x, y, w, h) in faces:
        center_x = x + w // 2
        cv2.line(frame, (center_x, y), (center_x, y + h), (0, 255, 0), 2)

        left_shoulder_x = x
        right_shoulder_x = x + w
        shoulder_y = y + int(h * 0.8)

        cv2.circle(frame, (left_shoulder_x, shoulder_y), 5, (0, 0, 255), -1)
        cv2.circle(frame, (right_shoulder_x, shoulder_y), 5, (0, 0, 255), -1)

        if abs(left_shoulder_x - center_x) != abs(right_shoulder_x - center_x):
            symmetry_text = "Not a Straight Line"
            text_color = (0, 0, 255)  # Red for poor alignment
        else:
            symmetry_text = "Good Alignment"
            text_color = (0, 255, 0)  # Green for good alignment

        cv2.putText(frame, symmetry_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)

    return frame

def main(user_id=None):
    if user_id is None:
        print("Error: No user ID provided.")
        return

    blink_count = 0
    blink_detected_time = 0
    blink_rate = 0.0  # Initialize blink rate
    start_time = time.time()

    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Unable to access the webcam.")
        return

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Error: Unable to read frame.")
            break

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=7, minSize=(50, 50))

        for (x, y, w, h) in faces:
            face = frame[y:y + h, x:x + w]
            gray_face = gray[y:y + h, x:x + w]

            eyes = eye_cascade.detectMultiScale(gray_face, scaleFactor=1.1, minNeighbors=10, minSize=(20, 20))

            if len(eyes) < 2:
                current_time = time.time()
                if current_time - blink_detected_time > 0.2:
                    blink_count += 1
                    blink_detected_time = current_time

                cv2.putText(frame, 'Blink Detected', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        elapsed_time = time.time() - start_time
        blink_rate = blink_count / (elapsed_time / 60) if elapsed_time > 0 else 0

        with blink_rate_lock:
            blink_rate_storage[user_id] = blink_rate

        cv2.putText(frame, f'Blink Rate: {blink_rate:.2f} blinks/min', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        frame = detect_symmetry_and_shoulders(frame, gray, faces)

        cv2.imshow('Blink & Symmetry Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Session ended for user ID: {user_id}")

if __name__ == "__main__":
    
    main(user_id=1)
