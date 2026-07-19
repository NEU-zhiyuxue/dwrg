# -*- coding: utf-8 -*-
"""
Auto Clicker - 悬浮窗自动点击脚本
流程：识别【按钮1.png】并点击 -> 识别【按钮2.png】并点击 -> 存储两坐标 ->
      循环：按钮1-按钮2-按钮1 (重复)
"""
import os
import sys
import time
import threading
import ctypes
from ctypes import windll


def elevate():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable,
        ' '.join(f'"{arg}"' for arg in sys.argv),
        None, 1
    )
    return False


if not elevate():
    sys.exit(0)


try:
    windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        windll.user32.SetProcessDPIAware()
    except Exception:
        pass


import cv2
import numpy as np
from PIL import ImageGrab
import win32api
import win32con
import win32gui
import tkinter as tk
from tkinter import ttk, scrolledtext


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "images")
BTN1_IMG = os.path.join(IMG_DIR, "button1.png")
BTN2_IMG = os.path.join(IMG_DIR, "button2.png")


def get_target_hwnd(title_keyword=""):
    """查找目标窗口句柄（按标题关键字匹配，为空时返回前台窗口）"""
    if not title_keyword:
        return win32gui.GetForegroundWindow()

    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title_keyword in title:
                extra.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else None


def screen_to_client(hwnd, screen_x, screen_y):
    """屏幕坐标转窗口客户区坐标"""
    client_point = win32gui.ScreenToClient(hwnd, (int(screen_x), int(screen_y)))
    return client_point


def click(x: int, y: int):
    """在屏幕坐标 (x, y) 模拟鼠标左键单击"""
    hwnd = get_target_hwnd()
    if hwnd:
        try:
            client_x, client_y = screen_to_client(hwnd, x, y)
            lparam = win32api.MAKELONG(client_x, client_y)
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
            time.sleep(0.08)
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
            return
        except Exception:
            pass

    import pyautogui
    pyautogui.moveTo(int(x), int(y), duration=0)
    pyautogui.click(clicks=1, interval=0.05)


class ImageMatcher:

    def __init__(self):
        self.btn1_template = None
        self.btn2_template = None
        self.btn1_coord = None
        self.btn2_coord = None

    @staticmethod
    def _load(path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Template not found: {path}")
        data = np.fromfile(path, dtype=np.uint8)
        if data.size == 0:
            raise ValueError(f"Empty file: {path}")
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Cannot decode image: {path}")
        return img

    def load_templates(self):
        self.btn1_template = self._load(BTN1_IMG)
        self.btn2_template = self._load(BTN2_IMG)

    @staticmethod
    def grab_screen():
        shot = ImageGrab.grab(all_screens=True)
        return cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)

    def find(self, template, threshold: float = 0.8):
        screen = self.grab_screen()
        h, w = template.shape[:2]
        sh, sw = screen.shape[:2]
        if h > sh or w > sw:
            return None, 0.0
        res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val >= threshold:
            center = (max_loc[0] + w // 2, max_loc[1] + h // 2)
            return center, float(max_val)
        return None, float(max_val)

    def find_btn1(self, threshold=0.8):
        coord, score = self.find(self.btn1_template, threshold)
        if coord:
            self.btn1_coord = coord
        return coord, score

    def find_btn2(self, threshold=0.8):
        coord, score = self.find(self.btn2_template, threshold)
        if coord:
            self.btn2_coord = coord
        return coord, score


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Auto Clicker")
        self.root.geometry("460x560")
        self.root.minsize(380, 460)
        self.root.attributes("-topmost", True)
        self.root.bind("<Escape>", lambda e: self.stop())

        self.running = False
        self.thread: threading.Thread | None = None
        self.matcher = ImageMatcher()
        self.topmost_var = tk.BooleanVar(value=True)
        self.interval_var = tk.StringVar(value="1.5")
        self.threshold_var = tk.StringVar(value="0.8")
        self.repeat_var = tk.StringVar(value="0")

        self._build_ui()
        try:
            self.matcher.load_templates()
            self.log("Templates loaded: button1.png, button2.png")
        except Exception as e:
            self.log(f"Failed to load templates: {e}")

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except Exception:
            pass

        ctrl = ttk.LabelFrame(self.root, text="Control Panel", padding=10)
        ctrl.pack(fill="x", padx=10, pady=(10, 6))

        ttk.Label(ctrl, text="Click Interval (s):").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(ctrl, textvariable=self.interval_var, width=8).grid(row=0, column=1, sticky="w", pady=4, padx=(4, 12))

        ttk.Label(ctrl, text="Match Threshold:").grid(row=0, column=2, sticky="w", pady=4)
        ttk.Entry(ctrl, textvariable=self.threshold_var, width=8).grid(row=0, column=3, sticky="w", pady=4, padx=(4, 0))

        ttk.Label(ctrl, text="Repeat Count (0=infinite):").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(ctrl, textvariable=self.repeat_var, width=8).grid(row=1, column=1, sticky="w", pady=4, padx=(4, 12))

        ttk.Checkbutton(ctrl, text="Always On Top", variable=self.topmost_var,
                        command=self._toggle_topmost).grid(row=1, column=2, columnspan=2, sticky="w")

        btn = ttk.Frame(ctrl)
        btn.grid(row=2, column=0, columnspan=4, pady=(8, 0))
        self.start_btn = ttk.Button(btn, text="Start", width=10, command=self.start)
        self.start_btn.pack(side="left", padx=4)
        self.stop_btn = ttk.Button(btn, text="Stop", width=10, command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=4)
        self.test_btn = ttk.Button(btn, text="Test", width=10, command=self.test_recognize)
        self.test_btn.pack(side="left", padx=4)

        coord_frame = ttk.LabelFrame(self.root, text="Coordinates", padding=8)
        coord_frame.pack(fill="x", padx=10, pady=4)
        self.btn1_coord_lbl = ttk.Label(coord_frame, text="Button1: Not detected", foreground="#0066cc")
        self.btn1_coord_lbl.pack(anchor="w")
        self.btn2_coord_lbl = ttk.Label(coord_frame, text="Button2: Not detected", foreground="#009933")
        self.btn2_coord_lbl.pack(anchor="w")
        self.status_lbl = tk.Label(coord_frame, text="● Stopped", fg="#888", anchor="w")
        self.status_lbl.pack(anchor="w", pady=(4, 0))

        log_frame = ttk.LabelFrame(self.root, text="Log", padding=4)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap="word", font=("Consolas", 9),
                                                  bg="#1e1e1e", fg="#d4d4d4", insertbackground="#d4d4d4")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="normal")

    def _toggle_topmost(self):
        self.root.attributes("-topmost", self.topmost_var.get())

    def log(self, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        self.root.after(0, lambda: self._append_log(line))

    def _append_log(self, line: str):
        self.log_text.insert("end", line)
        self.log_text.see("end")

    def _set_status(self, running: bool):
        if running:
            self.status_lbl.config(text="● Running", fg="#cc3300")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
        else:
            self.status_lbl.config(text="● Stopped", fg="#888")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")

    def _update_coords(self):
        if self.matcher.btn1_coord:
            self.btn1_coord_lbl.config(text=f"Button1: {self.matcher.btn1_coord}")
        if self.matcher.btn2_coord:
            self.btn2_coord_lbl.config(text=f"Button2: {self.matcher.btn2_coord}")

    def _parse_params(self):
        try:
            interval = float(self.interval_var.get())
            threshold = float(self.threshold_var.get())
            repeat = int(self.repeat_var.get())
            if interval < 0.05:
                raise ValueError("Interval too small")
            if not 0.1 <= threshold <= 1.0:
                raise ValueError("Threshold must be 0.1~1.0")
            return interval, threshold, repeat
        except ValueError as e:
            self.log(f"Invalid params: {e}")
            return None

    def start(self):
        if self.running:
            return
        params = self._parse_params()
        if params is None:
            return
        interval, threshold, repeat = params
        self.running = True
        self._set_status(True)
        self.log("=" * 40)
        self.log(f"Started | Interval {interval}s | Threshold {threshold} | Repeat {'∞' if repeat == 0 else repeat}")
        self.thread = threading.Thread(target=self._run_loop,
                                       args=(interval, threshold, repeat), daemon=True)
        self.thread.start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.log("Stopping...")
        self._set_status(False)

    def test_recognize(self):
        if self.running:
            self.log("Cannot test while running")
            return

        def _task():
            try:
                self.matcher.load_templates()
                c1, s1 = self.matcher.find_btn1(float(self.threshold_var.get()))
                c2, s2 = self.matcher.find_btn2(float(self.threshold_var.get()))
                self.root.after(0, self._update_coords)
                if c1:
                    self.log(f"【Button1】Found: {c1} (score {s1:.3f})")
                else:
                    self.log(f"【Button1】Not found (max score {s1:.3f})")
                if c2:
                    self.log(f"【Button2】Found: {c2} (score {s2:.3f})")
                else:
                    self.log(f"【Button2】Not found (max score {s2:.3f})")
            except Exception as e:
                self.log(f"Test error: {e}")

        threading.Thread(target=_task, daemon=True).start()

    def _wait(self, seconds: float) -> bool:
        end = time.time() + seconds
        while time.time() < end:
            if not self.running:
                return False
            time.sleep(0.05)
        return self.running

    def _run_loop(self, interval: float, threshold: float, repeat: int):
        try:
            self.log(">>> Step 1: Find Button1")
            coord, score = self.matcher.find_btn1(threshold)
            if not coord:
                self.log(f"Button1 not found, max score {score:.3f}")
                return
            self.log(f"Button1 found at {coord} (score {score:.3f}), clicking")
            self.root.after(0, self._update_coords)
            click(*coord)
            if not self._wait(interval):
                return

            self.log(">>> Step 2: Find Button2")
            coord, score = self.matcher.find_btn2(threshold)
            if not coord:
                self.log(f"Button2 not found, max score {score:.3f}")
                return
            self.log(f"Button2 found at {coord} (score {score:.3f}), clicking")
            self.root.after(0, self._update_coords)
            click(*coord)
            if not self._wait(interval):
                return

            if self.matcher.btn1_coord:
                self.log(f">>> Step 3: Click stored Button1 at {self.matcher.btn1_coord}")
                click(*self.matcher.btn1_coord)
                if not self._wait(interval):
                    return

            cycle = 0
            while self.running:
                if repeat != 0 and cycle >= repeat:
                    self.log(f"Reached {repeat} cycles, stopping")
                    break
                cycle += 1
                self.log(f"=== Cycle {cycle} ===")

                if not self.matcher.btn1_coord:
                    self.log("No Button1 coordinate, stopping")
                    break
                self.log(f"Click Button1 {self.matcher.btn1_coord}")
                click(*self.matcher.btn1_coord)
                if not self._wait(interval):
                    break

                coord, score = self.matcher.find_btn2(threshold)
                if coord:
                    self.log(f"Click Button2 {coord} (score {score:.3f})")
                    self.root.after(0, self._update_coords)
                    click(*coord)
                elif self.matcher.btn2_coord:
                    self.log(f"Button2 not found (score {score:.3f}), using stored {self.matcher.btn2_coord}")
                    click(*self.matcher.btn2_coord)
                else:
                    self.log("Cannot locate Button2, stopping")
                    break
                if not self._wait(interval):
                    break

                if not self.matcher.btn1_coord:
                    break
                self.log(f"Click Button1 {self.matcher.btn1_coord}")
                click(*self.matcher.btn1_coord)
                if not self._wait(interval):
                    break

        except Exception as e:
            self.log(f"Error: {e}")
        finally:
            self.running = False
            self.root.after(0, lambda: self._set_status(False))
            self.log("Stopped")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
