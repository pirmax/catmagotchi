import os
import sys
import time
import argparse
import random
from PIL import Image, ImageDraw, ImageTk
import tkinter as tk

SCREEN_WIDTH = 250
SCREEN_HEIGHT = 122
FRAME_DELAY = 0.5
LINE_HEIGHT = 1

# Configuration des animations
ANIMATIONS = {
    "idle": {"frames": 5, "duration": 20},
    "idle_to_sleep": {"frames": 8, "duration": None},
    "sleep": {"frames": 3, "duration": 40},
    "sleep_to_idle": {"frames": 8, "duration": None},
    "walking_positive": {"frames": 8, "duration": 10},
    "walking_negative": {"frames": 8, "duration": 10},
}

def load_frame(animation_name, frame_index):
    path = f"animations/{animation_name}/frame_{frame_index}.png"
    img = Image.open(path).convert('L')  # grayscale

    # Convert pixels sombres (chat) en noir, clairs (fond) en blanc
    bw = img.point(lambda x: 255 if x > 128 else 0, '1')  # fond blanc, chat noir

    centered = Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), 255)  # fond blanc
    img_w, img_h = bw.size
    pos_x = (SCREEN_WIDTH - img_w) // 2
    pos_y = (SCREEN_HEIGHT - img_h) // 2
    centered.paste(bw, (pos_x, pos_y))

    return centered

# ----- EPAPER MODE -----
def display_frame_epaper(epd, animation_name, frame_index):
    frame = load_frame(animation_name, frame_index)
    epd.display(epd.getbuffer(frame))

# ----- DESKTOP MODE -----
def display_frame_desktop(canvas, photo_img, animation_name, frame_index, root):
    frame = load_frame(animation_name, frame_index)
    display = frame.convert('L')
    tk_img = ImageTk.PhotoImage(display.resize((SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2)))
    photo_img[0] = tk_img
    canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
    root.update()

# ----- PLAYER -----
def play_animation(animation_name, display_fn):
    config = ANIMATIONS[animation_name]
    frame_count = config["frames"]
    total_duration = config["duration"]

    if total_duration is None:
        for i in range(frame_count):
            display_fn(animation_name, i)
            time.sleep(FRAME_DELAY)
    else:
        loops = int(total_duration / (FRAME_DELAY * frame_count))
        for _ in range(loops):
            for i in range(frame_count):
                display_fn(animation_name, i)
                time.sleep(FRAME_DELAY)

# ----- RANDOM LOGIC -----
def animation_sequence(display_fn):
    last_state = "idle"

    while True:
        if last_state == "sleep":
            play_animation("sleep_to_idle", display_fn)
            last_state = "idle"
            continue

        if last_state in ["walking_positive", "walking_negative"]:
            play_animation("idle", display_fn)
            last_state = "idle"
            continue

        # From idle, choose next
        choice = random.choice(["walk_pos", "walk_neg", "sleep", "idle"])
        if choice == "walk_pos":
            play_animation("walking_positive", display_fn)
            last_state = "walking_positive"
        elif choice == "walk_neg":
            play_animation("walking_negative", display_fn)
            last_state = "walking_negative"
        elif choice == "sleep":
            play_animation("idle_to_sleep", display_fn)
            play_animation("sleep", display_fn)
            last_state = "sleep"
        else:
            play_animation("idle", display_fn)
            last_state = "idle"

# ----- RUN EPAPER MODE -----
def run_epaper():
    sys.path.append("lib")
    from waveshare_epd import epd2in13_V3
    epd = epd2in13_V3.EPD()
    epd.init()
    epd.Clear(0xFF)
    try:
        animation_sequence(lambda a, i: display_frame_epaper(epd, a, i))
    except KeyboardInterrupt:
        epd.init()
        epd.Clear(0xFF)
        epd.sleep()

# ----- RUN DESKTOP PREVIEW -----
def run_desktop():
    root = tk.Tk()
    root.title("Catmagotchi Desktop Preview")
    canvas = tk.Canvas(root, width=SCREEN_WIDTH*2, height=SCREEN_HEIGHT*2, bg='white')
    canvas.pack()
    photo_img = [None]

    try:
        animation_sequence(lambda a, i: display_frame_desktop(canvas, photo_img, a, i, root))
    except KeyboardInterrupt:
        root.destroy()

# ----- ENTRY POINT -----
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Run desktop preview mode")
    args = parser.parse_args()

    if args.preview:
        run_desktop()
    else:
        run_epaper()