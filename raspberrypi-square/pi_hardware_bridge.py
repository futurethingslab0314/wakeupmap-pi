#!/usr/bin/env python3
"""
WakeUpMap Square - Raspberry Pi hardware bridge.

Reads:
- GPIO18 button
- GPIO22/23/24/25 4-position band switch
- MCP3008 CH0 potentiometer over SPI

Pushes state into the square browser UI through Selenium.
"""

import os
import time
import threading
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger("pi_hardware_bridge")

BUTTON_PIN = int(os.getenv("BUTTON_PIN", "18"))
SWITCH_PINS = [22, 23, 24, 25]
POTI_CHANNEL = int(os.getenv("POTI_CHANNEL", "0"))
WEBSITE_URL = os.getenv("WEBSITE_URL", "http://127.0.0.1:3000")
DEBUG_BROWSER = os.getenv("DEBUG_BROWSER", "false").lower() in ("1", "true", "yes", "on")
POLL_INTERVAL = float(os.getenv("BRIDGE_POLL_INTERVAL", "0.08"))
DEBOUNCE_SECONDS = float(os.getenv("BRIDGE_DEBOUNCE_SECONDS", "0.35"))


def load_env_file():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


load_env_file()

try:
    import pigpio
except Exception as exc:
    pigpio = None
    logger.warning("pigpio unavailable: %s", exc)

try:
    import spidev
except Exception as exc:
    spidev = None
    logger.warning("spidev unavailable: %s", exc)


def get_chromedriver_path():
    candidates = [
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/opt/homebrew/bin/chromedriver",
        "/snap/bin/chromium.chromedriver",
        "chromedriver",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def build_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    if DEBUG_BROWSER:
        options.add_argument("--window-size=1280,800")
        options.add_argument("--window-position=50,50")
    else:
        options.add_argument("--window-size=800,480")
        options.add_argument("--window-position=0,0")
        options.add_argument("--start-fullscreen")
        options.add_argument("--kiosk")
        options.add_argument("--hide-scrollbars")

    chromedriver_path = get_chromedriver_path()
    if chromedriver_path:
        from selenium.webdriver.chrome.service import Service

        return webdriver.Chrome(service=Service(chromedriver_path), options=options)
    return webdriver.Chrome(options=options)


def read_mcp3008(spi):
    if spi is None:
        return None
    # MCP3008 single-ended read on channel 0-7
    channel = max(0, min(7, POTI_CHANNEL))
    start = 1
    single_ended = 1
    command = [start, (single_ended << 7) | (channel << 4), 0]
    resp = spi.xfer2(command)
    return ((resp[1] & 3) << 8) | resp[2]


class HardwareBridge:
    def __init__(self):
        self.driver = None
        self.pi = None
        self.spi = None
        self.stop_event = threading.Event()
        self.last_button_press = 0.0
        self.last_switch_state = None
        self.last_pot_bucket = None
        self.last_heartbeat = 0.0

    def setup(self):
        self.driver = build_driver()
        self.driver.get(WEBSITE_URL)
        time.sleep(2)

        if pigpio:
            self.pi = pigpio.pi()
            if not self.pi.connected:
                raise RuntimeError("Unable to connect to pigpiod")
            self.pi.set_mode(BUTTON_PIN, pigpio.INPUT)
            self.pi.set_pull_up_down(BUTTON_PIN, pigpio.PUD_UP)
            for pin in SWITCH_PINS:
                self.pi.set_mode(pin, pigpio.INPUT)
                self.pi.set_pull_up_down(pin, pigpio.PUD_UP)

        if spidev:
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)
            self.spi.max_speed_hz = 1_000_000
            self.spi.mode = 0

    def js(self, script):
        try:
            self.driver.execute_script(script)
        except Exception as exc:
            logger.warning("JS execution failed: %s", exc)

    def read_switch_position(self):
        if not self.pi:
            return None
        # Each switch position pulls one pin LOW.
        for index, pin in enumerate(SWITCH_PINS):
            if self.pi.read(pin) == 0:
                return index
        return None

    def poll_button(self):
        if not self.pi:
            return
        pressed = self.pi.read(BUTTON_PIN) == 0
        now = time.time()
        if pressed and (now - self.last_button_press) >= DEBOUNCE_SECONDS:
            self.last_button_press = now
            logger.info("button pressed")
            self.js("if (window.startTheDay) { window.startTheDay(); }")

    def poll_switch(self):
        position = self.read_switch_position()
        if position is None or position == self.last_switch_state:
            return
        self.last_switch_state = position
        logger.info("band switch position: %s", position)
        self.js(f"if (window.setBandSwitchPosition) {{ window.setBandSwitchPosition({position}); }}")

    def poll_pot(self):
        value = read_mcp3008(self.spi)
        if value is None:
            return
        bucket = int(round((value / 1023) * 4))
        bucket = max(0, min(4, bucket))
        if bucket == self.last_pot_bucket:
            return
        self.last_pot_bucket = bucket
        # Map bucket to zoom change; 0/1 = zoom out, 3/4 = zoom in
        if bucket in (0, 1):
            self.js("if (window.navigateZoom) { window.navigateZoom('out'); }")
        elif bucket in (3, 4):
            self.js("if (window.navigateZoom) { window.navigateZoom('in'); }")

    def run(self):
        self.setup()
        logger.info("hardware bridge started")
        while not self.stop_event.is_set():
            self.poll_button()
            self.poll_switch()
            self.poll_pot()
            if time.time() - self.last_heartbeat > 30:
                self.last_heartbeat = time.time()
                logger.info("bridge alive")
            time.sleep(POLL_INTERVAL)

    def shutdown(self):
        self.stop_event.set()
        try:
            if self.spi:
                self.spi.close()
        except Exception:
            pass
        try:
            if self.pi:
                self.pi.stop()
        except Exception:
            pass
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    bridge = HardwareBridge()
    try:
        bridge.run()
    except KeyboardInterrupt:
        pass
    finally:
        bridge.shutdown()


if __name__ == "__main__":
    main()
