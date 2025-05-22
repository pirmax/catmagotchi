import sys
import time
import argparse
import random
from PIL import Image, ImageTk
import tkinter as tk

# Screen resolution for the 2.13" Waveshare e-paper display
SCREEN_WIDTH = 250
SCREEN_HEIGHT = 122
FRAME_DELAY = 0.5  # Seconds between frames
LINE_HEIGHT = 1

# Animation configuration: number of frames and total duration (in seconds)
ANIMATIONS = {
    "idle": {"frames": 5, "duration": 10},
    "idle_to_sleep": {"frames": 8, "duration": None},
    "sleep": {"frames": 3, "duration": 15},
    "sleep_to_idle": {"frames": 8, "duration": None},
    "walking_positive": {"frames": 8, "duration": 5},
    "walking_negative": {"frames": 8, "duration": 5},
}

# --- LOAD AND PREPARE FRAME ---
def load_frame(animation_name, frame_index):
    path = f"animations/{animation_name}/frame_{frame_index}.png"

    # Load image as RGB, ignore transparency, convert to grayscale
    img = Image.open(path).convert('RGB')
    grayscale = img.convert('L')

    # Custom thresholding to extract black & white version of the cat
    def threshold(x):
        # Background (almost black) becomes white (invisible)
        # Bright details like eyes stay white
        # Midtones (cat body) become black
        if x < 20:
            return 255  # Treat as white (background)
        elif x > 190:
            return 255  # Eyes and light highlights → white
        else:
            return 0    # Cat body and darker parts → black

    bw = grayscale.point(threshold, '1')  # Convert to 1-bit black & white image

    # Center the image on a blank white canvas matching the screen size
    centered = Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), 255)
    pos_x = (SCREEN_WIDTH - bw.width) // 2
    pos_y = (SCREEN_HEIGHT - bw.height) // 2
    centered.paste(bw, (pos_x, pos_y))

    return centered

# --- DISPLAY FRAME ON EPAPER ---
def display_frame_epaper(epd, animation_name, frame_index):
    frame = load_frame(animation_name, frame_index)
    epd.displayPartial(epd.getbuffer(frame))  # Partial refresh to avoid flicker

# --- DISPLAY FRAME ON DESKTOP PREVIEW ---
def display_frame_desktop(canvas, photo_img, animation_name, frame_index, root):
    frame = load_frame(animation_name, frame_index)
    display = frame.convert('L')  # Convert back to grayscale for display
    tk_img = ImageTk.PhotoImage(display.resize((SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2)))
    photo_img[0] = tk_img
    canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
    root.update()

# --- PLAY ONE ANIMATION CYCLE ---
def play_animation(animation_name, display_fn):
    config = ANIMATIONS[animation_name]
    frame_count = config["frames"]
    total_duration = config["duration"]

    if total_duration is None:
        # Play once, frame by frame
        for i in range(frame_count):
            display_fn(animation_name, i)
            time.sleep(FRAME_DELAY)
    else:
        # Loop the animation enough to fill total_duration
        loops = int(total_duration / (FRAME_DELAY * frame_count))
        for _ in range(loops):
            for i in range(frame_count):
                display_fn(animation_name, i)
                time.sleep(FRAME_DELAY)

# --- CHOOSE RANDOMLY WHAT THE CAT DOES NEXT ---
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

        # Randomly pick the next action
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

# --- START EPAPER MODE ---
def run_epaper():
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
    from waveshare_epd import epd2in13_V3
    epd = epd2in13_V3.EPD()
    epd.init()
    epd.Clear(0xFF)  # Full white screen clear
    # Set a blank white base image to prepare for partial updates
    epd.displayPartBaseImage(epd.getbuffer(Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), 255)))
    try:
        animation_sequence(lambda a, i: display_frame_epaper(epd, a, i))
    except KeyboardInterrupt:
        epd.init()
        epd.Clear(0xFF)
        epd.sleep()

# --- START DESKTOP PREVIEW MODE (FOR DEV ON MAC/LINUX) ---
def run_desktop():
    root = tk.Tk()
    root.title("Catmagotchi Desktop Preview")
    canvas = tk.Canvas(root, width=SCREEN_WIDTH*2, height=SCREEN_HEIGHT*2, bg='white')
    canvas.pack()
    photo_img = [None]  # Used to keep reference to the image

    try:
        animation_sequence(lambda a, i: display_frame_desktop(canvas, photo_img, a, i, root))
    except KeyboardInterrupt:
        root.destroy()

# --- ENTRY POINT ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Run desktop preview mode instead of e-paper mode")
    args = parser.parse_args()

    if args.preview:
        run_desktop()
    else:
        run_epaper()