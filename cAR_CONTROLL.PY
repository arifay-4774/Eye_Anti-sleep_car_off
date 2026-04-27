import cv2
import mediapipe as mp
import serial
import time
import math

# ── CONFIG ──────────────────────────────────────────
BLUETOOTH_PORT = "COM7"
BAUD_RATE      = 9600
EAR_THRESHOLD  = 0.25
CLOSED_SECONDS = 1
# ────────────────────────────────────────────────────

# Eye landmark indexes (MediaPipe)
LEFT_EYE  = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33,  160, 158, 133, 153, 144]

def eye_aspect_ratio(landmarks, eye_points, w, h):
    # Calculate screen coordinates
    p = [(landmarks[i].x * w, landmarks[i].y * h) for i in eye_points]
    # Compute Euclidean distances
    A = math.dist(p[1], p[5])
    B = math.dist(p[2], p[4])
    C = math.dist(p[0], p[3])
    if C == 0:
        return 0.0
    return (A + B) / (2.0 * C)

def main():
    print("⏳ Connecting to Bluetooth...")
    bt = None
    try:
        # Added write_timeout so the script won't freeze if Bluetooth hangs
        bt = serial.Serial(BLUETOOTH_PORT, BAUD_RATE, timeout=1, write_timeout=1)
        time.sleep(2)
        print(f"✅ Bluetooth connected on {BLUETOOTH_PORT}!")
    except Exception as e:
        print(f"❌ Bluetooth error: {e}")
        print("⚠️ Running in camera-only mode for testing. Hardware will not move.")

    print("⏳ Starting Camera...")
    # CAP_DSHOW acts significantly faster and doesn't get stuck on Windows
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    # 640x480 resolution forces the script to run fast and efficiently
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    # Minimizing the buffer size reduces lagging behind real-time
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    mp_face_mesh = mp.solutions.face_mesh
    
    car_moving        = False
    eyes_closed_start = None

    print("🚗 Anti-Sleep Car Started!")
    print("👁️  Look at camera - car will move forward")
    print("😴 Close eyes 2+ seconds - car will STOP")

    try:
        # refine_landmarks=False increases FPS and prevents getting stuck!
        with mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as face_mesh:
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Failed to grab frame from camera. Exiting.")
                    break

                h, w = frame.shape[:2]
                # Small optimization: Convert frame to RGB and mark as not writeable
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False 
                
                results = face_mesh.process(rgb)
                
                eyes_open = True

                if results.multi_face_landmarks:
                    landmarks = results.multi_face_landmarks[0].landmark

                    left_ear  = eye_aspect_ratio(landmarks, LEFT_EYE, w, h)
                    right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE, w, h)
                    ear       = (left_ear + right_ear) / 2.0

                    cv2.putText(frame, f"EAR: {ear:.2f}", (10, 90), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    if ear < EAR_THRESHOLD:
                        eyes_open = False
                        if eyes_closed_start is None:
                            eyes_closed_start = time.time()

                        closed_duration = time.time() - eyes_closed_start
                        cv2.putText(frame, f"EYES CLOSED: {closed_duration:.1f}s", (10, 60), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                        # Stop car when eyes closed 2+ seconds
                        if closed_duration >= CLOSED_SECONDS and car_moving:
                            if bt:
                                try: bt.write(b'S')
                                except: pass
                            car_moving = False
                            print("😴 ASLEEP! Car STOPPED")

                    else:
                        eyes_closed_start = None
                        cv2.putText(frame, "EYES OPEN", (10, 60), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    # Eyes open and face detected → move car
                    if eyes_open and not car_moving:
                        if bt:
                            try: bt.write(b'F')
                            except: pass
                        car_moving = True
                        print("👁️  Awake! Car MOVING FORWARD")

                else:
                    # No face detected → stop car for safety
                    if car_moving:
                        if bt:
                            try: bt.write(b'S')
                            except: pass
                        car_moving = False
                        print("⚠️ No face detected! Car STOPPED")

                    cv2.putText(frame, "NO FACE DETECTED", (10, 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

                # UI Status display
                status = "MOVING" if car_moving else "STOPPED"
                color  = (0, 255, 0) if car_moving else (0, 0, 255)
                cv2.putText(frame, f"CAR: {status}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

                cv2.imshow("Anti-Sleep Car Monitor", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
    finally:
        # Cleanup
        print("🛑 Shutting down and releasing resources...")
        if bt:
            try:
                bt.write(b'S')
                bt.close()
            except:
                pass
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()