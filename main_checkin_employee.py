import cv2
import numpy as np
from datetime import datetime
from utils import get_embedding, load_employees, recognize_face, mark_checkin
import subprocess
import sys

# --- Configuration ---
THRESHOLD = 0.7
# increase cooldown to avoid multiple rapid check-ins (seconds)
COOLDOWN_SECONDS = 10
MIN_FACE_SIZE = 80

# --- Load models and data ---
from face_engine import get_detector, get_embedder

detector = get_detector()
embedder = get_embedder()

if detector is None or embedder is None:
    print("[ERROR] Failed to load face recognition models")
    exit(1)

employees = load_employees()
if not employees:
    print("[WARN] No employees found! Please register employees first.")
    exit(0)

print(f"[INFO] Loaded {len(employees)} employees")

# --- State management ---
last_checkin = {}

def can_checkin(emp_id):
    if emp_id not in last_checkin:
        return True
    elapsed = (datetime.now() - last_checkin[emp_id]).total_seconds()
    return elapsed > COOLDOWN_SECONDS

# --- Main loop ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[ERROR] Cannot open camera")
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

print("[INFO] Check-in system started")
print("[INFO] Press ESC to exit")
print("-" * 50)

frame_count = 0
# process every N frames (camera ~30fps). Increasing reduces processing frequency.
process_every_n_frames = 6

# require N consecutive positive recognitions (on processed frames) to accept
CONSECUTIVE_REQUIRED = 2
consecutive_hits = {}

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_count += 1
        if frame_count % process_every_n_frames != 0:
            cv2.imshow("Check-in System", frame)
            if cv2.waitKey(1) == 27:
                break
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = detector.detect_faces(rgb)

        if not results:
            cv2.putText(frame, "No face detected", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.imshow("Check-in System", frame)
            if cv2.waitKey(1) == 27:
                break
            continue

        largest = max(results, key=lambda r: r["box"][2] * r["box"][3])
        x, y, w, h = largest["box"]
        confidence = largest["confidence"]
        x, y = max(0, x), max(0, y)

        if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(frame, "Face too small", (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.imshow("Check-in System", frame)
            if cv2.waitKey(1) == 27:
                break
            continue

        if confidence < 0.95:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 165, 255), 2)
            cv2.putText(frame, f"Low confidence: {confidence:.2f}", (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            cv2.imshow("Check-in System", frame)
            if cv2.waitKey(1) == 27:
                break
            continue

        face = rgb[y:y+h, x:x+w]
        # Validate crop
        if face is None or getattr(face, 'size', 0) == 0:
            cv2.putText(frame, "Invalid face crop", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.imshow("Check-in System", frame)
            if cv2.waitKey(1) == 27:
                break
            continue

        try:
            face_resized = cv2.resize(face, (160, 160))
        except Exception as e:
            print(f"[WARN] Resize failed: {e}")
            continue

        try:
            # Ensure correct array shape and dtype
            arr = np.asarray(face_resized)
            if arr.size == 0 or arr.shape[0] == 0 or arr.shape[1] == 0:
                continue
            try:
                emb = get_embedding(arr)
            except Exception as ge:
                print(f"[WARN] get_embedding skipped: {ge}")
                continue
            matched, dist = recognize_face(emb, employees, threshold=THRESHOLD)

            # require consecutive matches to avoid flakiness
            if matched:
                eid = str(matched['id'])
                consecutive_hits[eid] = consecutive_hits.get(eid, 0) + 1
            else:
                # reset all counts when unknown
                consecutive_hits.clear()
            # only proceed when consecutive_hits reaches threshold
            if not matched or consecutive_hits.get(str(matched['id']), 0) < CONSECUTIVE_REQUIRED:
                # show detection but don't register yet
                cv2.rectangle(frame, (x, y), (x+w, y+h), (200, 200, 0), 2)
                cv2.putText(frame, "Recognizing...", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,0), 2)
                cv2.imshow("Check-in System", frame)
                if cv2.waitKey(1) == 27:
                    break
                continue

            if matched:
                emp_id = matched['id']
                emp_name = matched['name']

                if can_checkin(emp_id):
                    success = mark_checkin(matched)
                    if success:
                        last_checkin[emp_id] = datetime.now()
                        color = (0, 255, 0)
                        status = "CHECKED IN"
                        print(f"✓ {emp_name} (ID: {emp_id}) checked in successfully")
                    else:
                        color = (0, 165, 255)
                        status = "ALREADY CHECKED IN"
                else:
                    color = (255, 255, 0)
                    status = "COOLDOWN"

                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, f"{emp_name}", (x, y-30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                cv2.putText(frame, f"{status}", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                cv2.putText(frame, f"Confidence: {1-dist:.2f}", (x, y+h+20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            else:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, "Unknown Person", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(frame, f"Distance: {dist:.2f}", (x, y+h+20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                print(f"✗ Unknown person detected (distance: {dist:.2f})")

        except Exception as e:
            print(f"[ERROR] Processing failed: {e}")
            cv2.putText(frame, "Processing Error", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("Check-in System", frame)
        if cv2.waitKey(1) == 27:
            break

finally:
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("\n[INFO] Check-in system stopped")
    print(f"[INFO] Total check-ins processed: {len(last_checkin)}")

    # --- Automatically return to main menu ---
    subprocess.Popen([sys.executable, "main_menu.pyw"])
