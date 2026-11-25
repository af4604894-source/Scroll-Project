import sys
import time
from unittest.mock import MagicMock

sys.modules["matplotlib"] = MagicMock()
sys.modules["matplotlib.pyplot"] = MagicMock()
sys.modules["matplotlib.ft2font"] = MagicMock()

import cv2
import mediapipe as mp
import pyautogui

pyautogui.FAILSAFE = False

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1, min_detection_confidence=0.75, min_tracking_confidence=0.75
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
time.sleep(0.5)

window_name = "Reels Gesture Controller"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

last_action_time = 0
cooldown = 1.2  # ثانية وربع بين كل أمر والتاني عشان ميعملش سكرول مرتين ورا بعض
status_text = "Ready"
status_time = 0

# عداد لتأكيد ثبات الإشارة لـ 4 فريمات متتالية (لمنع التنفيذ بالخطأ أثناء فتح أو قفل اليد)
stable_gesture = None
gesture_frames = 0

TIP_IDS = [8, 12, 16, 20]
PIP_IDS = [6, 10, 14, 18]

while True:
    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    current_time = time.time()

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            lm = hand_landmarks.landmark

            # فحص كل إصبع (1 = مفرود، 0 = مقفول)
            fingers = []
            for tip, pip in zip(TIP_IDS, PIP_IDS):
                if lm[tip].y < lm[pip].y:
                    fingers.append(1)
                else:
                    fingers.append(0)

            current_gesture = tuple(fingers)

            # التأكد إن الإشارة ثابتة لمدة 4 فريمات قبل التنفيذ
            if current_gesture == stable_gesture:
                gesture_frames += 1
            else:
                stable_gesture = current_gesture
                gesture_frames = 1

            if (
                gesture_frames == 4
                and (current_time - last_action_time) > cooldown
            ):
                # 1. ضم كف اليد بالكامل (✊) -> إيقاف / تشغيل
                if fingers == [0, 0, 0, 0]:
                    pyautogui.press("space")
                    status_text = "PLAY / PAUSE"
                    status_time = current_time
                    last_action_time = current_time

                # 2. رفع السبابة فقط (☝️) -> الفيديو التالي
                elif fingers == [1, 0, 0, 0]:
                    pyautogui.scroll(-500)
                    pyautogui.press("down")
                    status_text = "NEXT VIDEO"
                    status_time = current_time
                    last_action_time = current_time

                # 3. رفع السبابة والوسطى معاً (✌️) -> الفيديو السابق
                elif fingers == [1, 1, 0, 0]:
                    pyautogui.scroll(500)
                    pyautogui.press("up")
                    status_text = "PREVIOUS VIDEO"
                    status_time = current_time
                    last_action_time = current_time
    else:
        stable_gesture = None
        gesture_frames = 0

    if current_time - status_time < 1.0:
        cv2.putText(
            img,
            status_text,
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            3,
        )

    cv2.imshow(window_name, img)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()