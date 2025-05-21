# 🐱 Catmagotchi

A minimalist animated cat running on a Raspberry Pi Zero 2 WH with a 2.13" Waveshare Touch e-Paper display (250×122).  
The cat idles, walks, sleeps, and reacts over time with smooth transitions and a cozy e-ink aesthetic.

---

## 🧰 Requirements

- Raspberry Pi Zero 2 WH (or any Pi with GPIO and Python 3)
- Waveshare 2.13" Touch e-Paper display (250×122)
- Raspberry Pi OS (Bookworm or Bullseye recommended)
- Python 3.9+
- A set of `.png` animation frames exported from `.gif` files

Directory structure:

catmagotchi/
├── animations/
│   ├── idle/
│   ├── sleep/
│   └── …
├── lib/
│   └── waveshare_epd/
├── main.py
├── requirements.txt
└── README.md

---

## ⚙️ Installation (on Raspberry Pi)

### 1. Update and install system packages

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-pil python3-pil.imagetk python3-numpy python3-spidev python3-tk git
```

> Pillow, NumPy and SPI support are installed via APT for performance and compatibility reasons.

### 2. Clone the Waveshare e-Paper driver

```bash
git clone https://github.com/waveshare/e-Paper
cd e-Paper/RaspberryPi_JetsonNano/python
```

Instead of installing the driver with setup.py, copy it manually to the project:

```bash
mkdir -p ~/catmagotchi/lib
cp -r lib/waveshare_epd ~/catmagotchi/lib/
```

### 3. Add Python dependencies (for desktop preview only)

If you’re using the preview mode on macOS or a Linux desktop:

```bash
pip3 install -r requirements.txt --break-system-packages
```

Or use a virtualenv:

```bash
python3 -m venv cat-env
source cat-env/bin/activate
pip install -r requirements.txt
```

### 4. Run the project

To run on the e-Paper display:

```bash
cd ~/catmagotchi
python3 main.py
```

To run desktop preview mode (for development on macOS/Linux):

```bash
python3 main.py --preview
```

## 📦 requirements.txt (provided)

```
Pillow
spidev
numpy
```

Note: numpy, spidev, and pillow are preferably installed via apt for best performance on Raspberry Pi.

## 🧠 Future plans

- Add touch support (wake, play, feed)
- Integrate a basic UI with bubbles or reactions
- Trigger behaviors based on time of day or sensors

## 🐾 Credits

Built with ❤️ and Python by Maxence Rose, inspired by Tamagotchis, e-ink magic, and cozy low-power interfaces.