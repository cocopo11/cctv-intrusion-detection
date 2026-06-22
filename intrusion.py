from ultralytics import YOLO
from flask import (
    Flask,
    render_template,
    send_from_directory
)
import json
import cv2
import numpy as np
import threading
import requests
import os
from datetime import datetime
import time
from dotenv import load_dotenv

# ==========================
# 설정
# ==========================

VIDEO_SOURCE = "test.mp4"

MODEL_PATH = "yolo11n.pt"

SNAPSHOT_DIR = "snapshots"

load_dotenv()

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")

CONFIDENCE = 0.4

# ==========================
# 초기화
# ==========================

if not os.path.exists("alerts.json"):
    with open("alerts.json", "w") as f:
        json.dump([], f)

if not os.path.exists("zone.json"):
    with open("zone.json", "w") as f:
        json.dump({"points":[]}, f)

os.makedirs(SNAPSHOT_DIR, exist_ok=True)

model = YOLO(MODEL_PATH)

latest_frame = None
latest_snapshot = None

intrusion_count = 0

# ==========================
# ROI 선택
# ==========================

roi_points = []
roi_finished = False


def mouse_callback(event, x, y, flags, param):
    global roi_points, roi_finished

    if event == cv2.EVENT_LBUTTONDOWN:
        roi_points.append((x, y))

    elif event == cv2.EVENT_RBUTTONDOWN:
        roi_finished = True


# ==========================
# 디스코드 알림
# ==========================

def send_discord_alert(image_path):

    if not DISCORD_WEBHOOK:
        print("[DISCORD] webhook is not set")
        return

    try:

        with open(image_path, "rb") as f:

            response = requests.post(
                DISCORD_WEBHOOK,
                data={
                    "content":
                    f"🚨 CCTV 침입 감지\n"
                    f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"스냅샷: {image_path}"
                },
                files={
                    "file": f
                },
                timeout=10
            )

        if response.status_code in [200, 204]:
            print("[DISCORD] alert sent")
        else:
            print(
                "[DISCORD] failed:",
                response.status_code,
                response.text
            )

    except Exception as e:
        print("discord error:", e)


# ==========================
# Flask
# ==========================

app = Flask(__name__)


@app.route("/")
def home():

    try:
        with open(
            "alerts.json",
            "r",
            encoding="utf-8"
        ) as f:

            alerts = json.load(f)

    except:
        alerts = []

    return render_template(
        "index.html",
        alerts=alerts
    )


@app.route("/snapshots/<path:filename>")
def snapshots(filename):

    return send_from_directory(
        SNAPSHOT_DIR,
        filename
    )


def flask_thread():
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )


# ==========================
# ROI 선택
# ==========================

cap = cv2.VideoCapture(VIDEO_SOURCE)

ret, frame = cap.read()

if not ret:
    print("영상 열기 실패")
    exit()

clone = frame.copy()

cv2.namedWindow("ROI Select")
cv2.setMouseCallback("ROI Select", mouse_callback)

print()
print("좌클릭: 영역 점 추가")
print("우클릭: 영역 선택 완료")
print()

while True:

    temp = clone.copy()

    for p in roi_points:
        cv2.circle(temp, p, 5, (0,255,0), -1)

    if len(roi_points) >= 2:
        cv2.polylines(
            temp,
            [np.array(roi_points)],
            False,
            (0,255,0),
            2
        )

    cv2.imshow("ROI Select", temp)

    key = cv2.waitKey(1)

    if roi_finished and len(roi_points) >= 3:
        break

cv2.destroyWindow("ROI Select")

roi_polygon = np.array(roi_points)

with open(
    "zone.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        {
            "points": roi_points
        },
        f,
        indent=4
    )

cap.release()

# ==========================
# Flask 시작
# ==========================

threading.Thread(
    target=flask_thread,
    daemon=False
).start()

# ==========================
# 감지 시작
# ==========================

results = model.track(
    source=VIDEO_SOURCE,
    stream=True,
    persist=True,
    classes=[0]
)

inside_ids = set()

for result in results:

    frame = result.orig_img.copy()

    cv2.polylines(
        frame,
        [roi_polygon],
        True,
        (0,255,255),
        2
    )

    if result.boxes.id is not None:

        boxes = result.boxes.xyxy.cpu().numpy()
        ids = result.boxes.id.cpu().numpy()

        for box, track_id in zip(boxes, ids):

            x1, y1, x2, y2 = map(int, box)

            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            inside = cv2.pointPolygonTest(
                roi_polygon,
                (cx, cy),
                False
            )

            color = (0,255,0)

            if inside >= 0:

                color = (0,0,255)

                if track_id not in inside_ids:

                    inside_ids.add(track_id)

                    intrusion_count += 1

                    timestamp = datetime.now().strftime(
                        "%Y%m%d_%H%M%S"
                    )

                    filename = os.path.join(
                        SNAPSHOT_DIR,
                        f"intrusion_{timestamp}.jpg"
                    )

                    cv2.imwrite(filename, frame)

                    latest_snapshot = filename

                    try:

                        with open(
                            "alerts.json",
                            "r",
                            encoding="utf-8"
                        ) as f:

                            alerts = json.load(f)

                    except:

                        alerts = []

                    alerts.append(
                        {
                            "time": datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "snapshot": filename
                        }
                    )

                    with open(
                        "alerts.json",
                        "w",
                        encoding="utf-8"
                    ) as f:

                        json.dump(
                            alerts,
                            f,
                            ensure_ascii=False,
                            indent=4
                        )

                    print(
                        f"[ALERT] intrusion detected id={track_id}"
                    )

                    send_discord_alert(filename)

            cv2.rectangle(
                frame,
                (x1,y1),
                (x2,y2),
                color,
                2
            )

            cv2.putText(
                frame,
                f"ID {int(track_id)}",
                (x1,y1-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

    latest_frame = frame

    cv2.imshow("Intrusion Detection", frame)

    key = cv2.waitKey(1)

    if key == 27:
        break

cv2.destroyAllWindows()

print("Detection finished.")
print("Flask dashboard is still running.")
print("Open http://127.0.0.1:5000 in your browser.")
print("Press Ctrl+C in terminal to stop.")

while True:
    time.sleep(1)