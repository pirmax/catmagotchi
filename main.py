import os
import sys
import time
import random
from PIL import Image

# Add the paths to the libraries
# Ensure the paths are correct based on your directory structure
# This is a placeholder. Adjust the paths as necessary.
BASE_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(BASE_DIR, 'libs', 'waveshare'))
from epd2in13_V3 import EPD
from gt1151 import GT1151

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
    img = Image.open(path).convert('RGB')  # convert to RGB safely
    img = img.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)  # ensure full size
    grayscale = img.convert('L')

    # Simplified threshold: anything darker than 200 is black
    def threshold(x):
        return 0 if x < 200 else 255

    bw = grayscale.point(threshold, '1')

    print(f"Loaded {animation_name} frame {frame_index} → size={bw.size}, mode={bw.mode}")
    return bw

def display_frame_epaper(epd, animation_name, frame_index):
    frame = load_frame(animation_name, frame_index)
    epd.displayPartial(epd.getbuffer(frame))

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
    epd = EPD()
    epd.init(0)
    epd.Clear(0xFF)
    epd.displayPartBaseImage(epd.getbuffer(Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), 255)))

    # Test de l'animation
    frame = load_frame("idle", 0)
    epd.displayPartial(epd.getbuffer(frame))
    time.sleep(2)

    # Initialisation tactile
    touch = GT1151()
    touch.GT_Init()

    try:
        last_taps = []

        animation_sequence(
            lambda a, i: display_frame_epaper(epd, a, i),
            touch_check_fn=lambda: detect_double_tap(touch, last_taps)
        )
    except KeyboardInterrupt:
        epd.init(1)
        epd.Clear(0xFF)
        epd.sleep()

if __name__ == "__main__":
    run_epaper()