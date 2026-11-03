#!/opt/vw-seg/bin/python
"""Face boxes over a video with MediaPipe face detection (full-range model - works for small, far-away faces).
Prints JSON: [[x, y, w, h, score], ...] one per sampled frame where a face was found (largest confident face).
Used by prepare.py (falls back to OpenCV Haar when this venv is missing).
Usage: detect_face.py VIDEO [SAMPLES]
"""
import json, sys
import cv2
import mediapipe as mp

video = sys.argv[1]
samples = int(sys.argv[2]) if len(sys.argv) > 2 else 40
cap = cv2.VideoCapture(video)
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
out = []
with mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as fd:
    for i in range(samples):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((i + 0.5) * n / samples))
        ok, frame = cap.read()
        if not ok:
            continue
        H, W = frame.shape[:2]
        res = fd.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        best = None
        for d in res.detections or []:
            b = d.location_data.relative_bounding_box
            box = [int(b.xmin * W), int(b.ymin * H), int(b.width * W), int(b.height * H), round(d.score[0], 3)]
            if best is None or box[2] * box[3] * box[4] > best[2] * best[3] * best[4]:
                best = box
        if best:
            out.append(best)
print(json.dumps(out))
