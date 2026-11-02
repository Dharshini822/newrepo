import os
import sys
import time
import argparse
import cv2

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from backend.utils.security import sanitize_name

def capture_samples(sign_name: str, count: int = 25, split: str = "train", delay_sec: float = 0.5):
    """
    Captures live camera frames directly into dataset/<split>/<sign_name>/
    to make building custom sign datasets effortless.
    """
    clean_sign = sanitize_name(sign_name)
    target_dir = os.path.join(config.DATASET_DIR, split, clean_sign)
    os.makedirs(target_dir, exist_ok=True)

    print("===============================================================")
    print(f"  SignAI — Camera Dataset Collector for Sign: '{clean_sign}'")
    print(f"  Target Directory: {target_dir}")
    print(f"  Target Sample Count: {count}")
    print("===============================================================")
    print("Controls:")
    print("  [SPACE] : Start/Pause capturing")
    print("  [Q]     : Quit capture tool\n")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam (index 0). Please check your camera connection.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    capturing = False
    saved = 0
    last_capture_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to grab frame.")
            break

        # Flip horizontally for natural mirror feel
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Draw scanning guide box
        box_size = 280
        x1 = (w - box_size) // 2
        y1 = (h - box_size) // 2
        x2 = x1 + box_size
        y2 = y1 + box_size

        color = (0, 255, 0) if capturing else (255, 165, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Header info
        status_text = f"RECORDING ({saved}/{count})" if capturing else "PAUSED (Press SPACE to record)"
        cv2.putText(frame, f"Sign: {clean_sign}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, status_text, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, "Keep hand inside the box", (x1 + 10, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # If recording and delay elapsed, save crop or frame
        current_time = time.time()
        if capturing and saved < count and (current_time - last_capture_time >= delay_sec):
            filename = f"{clean_sign}_{int(current_time*1000)}_{saved+1}.jpg"
            save_path = os.path.join(target_dir, filename)
            # Save frame
            cv2.imwrite(save_path, frame)
            saved += 1
            last_capture_time = current_time
            print(f"Captured [{saved}/{count}]: {filename}")

            if saved >= count:
                capturing = False
                print(f"\n[DONE] Successfully captured {count} samples for sign '{clean_sign}'!")
                print(f"Saved into: {target_dir}")
                print("You can now train the model in the Dashboard or by running:")
                print("  python training/train.py\n")

        cv2.imshow(f"SignAI Dataset Collector - {clean_sign}", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == 32:  # SPACE
            capturing = not capturing

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SignAI Live Camera Dataset Capture Tool")
    parser.add_argument("--sign", type=str, required=True, help="Name of sign (e.g. HELLO, A, YES, THANKS)")
    parser.add_argument("--count", type=int, default=25, help="Number of samples to capture (default: 25)")
    parser.add_argument("--split", type=str, default="train", choices=["train", "validation"], help="Dataset split (train or validation)")
    parser.add_argument("--delay", type=float, default=0.4, help="Delay between captures in seconds (default: 0.4)")
    args = parser.parse_args()

    capture_samples(sign_name=args.sign, count=args.count, split=args.split, delay_sec=args.delay)
