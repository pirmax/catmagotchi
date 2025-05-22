import os
import sys
import time
import argparse
import random
import PIL
import tkinter as TK

# Add the paths to the libraries
# Ensure the paths are correct based on your directory structure
# This is a placeholder. Adjust the paths as necessary.
BASE_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(BASE_DIR, 'libs', 'waveshare_epd'))
sys.path.append(os.path.join(BASE_DIR, 'libs', 'tp_lib'))

import epd2in13_V3 as EPD
import gt1151 as TPLIB

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

def load_frame(animation_name, frame_index):
    path = f"animations/{animation_name}/frame_{frame_index}.png"
    img = PIL.Image.open(path).convert('RGB').convert('L')

    def threshold(x):
        if x < 20: return 255
        elif x > 190: return 255
        else: return 0

    bw = img.point(threshold, '1')
    centered = PIL.Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), 255)
    pos_x = (SCREEN_WIDTH - bw.width) // 2
    pos_y = (SCREEN_HEIGHT - bw.height) // 2
    centered.paste(bw, (pos_x, pos_y))
    return centered

def display_frame_epaper(epd, animation_name, frame_index):
    frame = load_frame(animation_name, frame_index)
    epd.displayPartial(epd.getbuffer(frame))

def display_frame_desktop(canvas, photo_img, animation_name, frame_index, root):
    frame = load_frame(animation_name, frame_index)
    display = frame.convert('L')
    tk_img = PIL.ImageTk.PhotoImage(display.resize((SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2)))
    photo_img[0] = tk_img
    canvas.create_image(0, 0, anchor=TK.NW, image=tk_img)
    root.update()

def play_animation(animation_name, display_fn):
    config = ANIMATIONS[animation_name]
    frames = config["frames"]
    total = config["duration"]

    if total is None:
        for i in range(frames):
            display_fn(animation_name, i)
            time.sleep(FRAME_DELAY)
    else:
        loops = int(total / (FRAME_DELAY * frames))
        for _ in range(loops):
            for i in range(frames):
                display_fn(animation_name, i)
                time.sleep(FRAME_DELAY)

def detect_double_tap(gt1151, last_taps, threshold_ms=500):
    if gt1151.digital_read(17) == 0:
        now = int(time.time() * 1000)
        last_taps.append(now)
        if len(last_taps) > 2:
            last_taps.pop(0)
        if len(last_taps) == 2 and (last_taps[1] - last_taps[0]) < threshold_ms:
            return True
    return False

def animation_sequence(display_fn, touch_check_fn=None):
    last_state = "idle"
    last_taps = []

    while True:
        if touch_check_fn and touch_check_fn():
            if last_state == "sleep":
                play_animation("sleep_to_idle", display_fn)
                last_state = "idle"
                continue

        if last_state == "sleep":
            play_animation("sleep", display_fn)
            continue

        if last_state in ["walking_positive", "walking_negative"]:
            play_animation("idle", display_fn)
            last_state = "idle"
            continue

        choice = random.choice(["walk_pos", "walk_neg", "sleep", "idle"])
        if choice == "walk_pos":
            play_animation("walking_positive", display_fn)
            last_state = "walking_positive"
        elif choice == "walk_neg":
            play_animation("walking_negative", display_fn)
            last_state = "walking_negative"
        elif choice == "sleep":
            play_animation("idle_to_sleep", display_fn)
            last_state = "sleep"
        else:
            play_animation("idle", display_fn)
            last_state = "idle"

def run_epaper():
    epd = EPD.EPD()
    epd.init()
    epd.Clear(0xFF)
    epd.displayPartBaseImage(epd.getbuffer(PIL.Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), 255)))

    # Initialisation tactile
    touch = TPLIB.GT1151()
    touch.gt1151_init()

    try:
        animation_sequence(
            lambda a, i: display_frame_epaper(epd, a, i),
            touch_check_fn=lambda: detect_double_tap(touch, [])
        )
    except KeyboardInterrupt:
        epd.init()
        epd.Clear(0xFF)
        epd.sleep()

def run_desktop():
    root = TK.Tk()
    root.title("Catmagotchi Preview")
    canvas = TK.Canvas(root, width=SCREEN_WIDTH * 2, height=SCREEN_HEIGHT * 2, bg='white')
    canvas.pack()
    photo_img = [None]

    try:
        animation_sequence(lambda a, i: display_frame_desktop(canvas, photo_img, a, i, root))
    except KeyboardInterrupt:
        root.destroy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Run desktop preview mode")
    args = parser.parse_args()

    if args.preview:
        run_desktop()
    else:
        run_epaper()