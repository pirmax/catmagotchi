import os
import sys
import time
import argparse
import random
from PIL import Image, ImageTk
import tkinter as tk

# Ajout des chemins des libs personnalisées
BASE_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(BASE_DIR, 'libs', 'waveshare_epd'))
sys.path.append(os.path.join(BASE_DIR, 'libs', 'tp_lib'))

from epd2in13_V3 import EPD
from gt1151 import Touch_Init, Touch_GetPoint, digital_read, INT as INT_PIN

# Constantes
SCREEN_WIDTH = 250
SCREEN_HEIGHT = 122
FRAME_DELAY = 0.5

ANIMATIONS = {
    "idle": {"frames": 5, "duration": 10},
    "idle_to_sleep": {"frames": 8, "duration": None},
    "sleep": {"frames": 3, "duration": 15},
    "sleep_to_idle": {"frames": 8, "duration": None},
    "walking_positive": {"frames": 8, "duration": 5},
    "walking_negative": {"frames": 8, "duration": 5},
}

# État global
current_state = {"mode": "idle"}

def load_frame(animation, index):
    path = f"animations/{animation}/frame_{index}.png"
    img = Image.open(path).convert('RGB').convert('L')

    def threshold(x): return 255 if x < 20 or x > 190 else 0
    bw = img.point(threshold, '1')

    centered = Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), 255)
    x = (SCREEN_WIDTH - bw.width) // 2
    y = (SCREEN_HEIGHT - bw.height) // 2
    centered.paste(bw, (x, y))
    return centered

def display_frame_epaper(epd, animation, index):
    frame = load_frame(animation, index)
    epd.displayPartial(epd.getbuffer(frame))

def play_animation(epd, animation):
    config = ANIMATIONS[animation]
    frames = config["frames"]
    duration = config["duration"]

    if duration is None:
        for i in range(frames):
            display_frame_epaper(epd, animation, i)
            time.sleep(FRAME_DELAY)
    else:
        loops = int(duration / (FRAME_DELAY * frames))
        for _ in range(loops):
            for i in range(frames):
                display_frame_epaper(epd, animation, i)
                time.sleep(FRAME_DELAY)

def animation_sequence(epd):
    last = "idle"
    while True:
        if current_state["mode"] == "wake_up":
            play_animation(epd, "sleep_to_idle")
            current_state["mode"] = "idle"
            last = "idle"
            continue

        if last == "sleep":
            play_animation(epd, "sleep")
            last = "sleep"
        elif last in ["walking_positive", "walking_negative"]:
            play_animation(epd, "idle")
            last = "idle"
        else:
            choice = random.choice(["walk_pos", "walk_neg", "sleep", "idle"])
            if choice == "walk_pos":
                play_animation(epd, "walking_positive")
                last = "walking_positive"
            elif choice == "walk_neg":
                play_animation(epd, "walking_negative")
                last = "walking_negative"
            elif choice == "sleep":
                play_animation(epd, "idle_to_sleep")
                current_state["mode"] = "sleep"
                last = "sleep"
            else:
                play_animation(epd, "idle")
                last = "idle"

def run_epaper():
    epd = EPD()
    epd.init()
    epd.Clear(0xFF)
    epd.displayPartBaseImage(epd.getbuffer(Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), 255)))

    last_tap = 0

    def handle_touch():
        nonlocal last_tap
        while True:
            if digital_read(INT_PIN) == 0:
                time.sleep(0.05)
                x, y = Touch_GetPoint()
                now = time.time()
                if now - last_tap < 0.5 and current_state["mode"] == "sleep":
                    current_state["mode"] = "wake_up"
                last_tap = now
                while digital_read(INT_PIN) == 0:
                    time.sleep(0.05)
            time.sleep(0.1)

    import threading
    Touch_Init()
    threading.Thread(target=handle_touch, daemon=True).start()

    try:
        animation_sequence(epd)
    except KeyboardInterrupt:
        epd.init()
        epd.Clear(0xFF)
        epd.sleep()

def run_desktop():
    root = tk.Tk()
    root.title("Catmagotchi Preview")
    canvas = tk.Canvas(root, width=SCREEN_WIDTH*2, height=SCREEN_HEIGHT*2)
    canvas.pack()
    photo_img = [None]

    def display(animation, index):
        frame = load_frame(animation, index)
        display = frame.convert('L')
        tk_img = ImageTk.PhotoImage(display.resize((SCREEN_WIDTH*2, SCREEN_HEIGHT*2)))
        photo_img[0] = tk_img
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
        root.update()

    try:
        while True:
            animation_sequence(type("MockEPD", (), {"displayPartial": lambda _, img: display(_, img)})())
    except KeyboardInterrupt:
        root.destroy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()

    if args.preview:
        run_desktop()
    else:
        run_epaper()