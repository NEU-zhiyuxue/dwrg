# Auto Clicker

A lightweight auto-clicker tool with floating window UI, using template matching to locate and click buttons automatically.

## Features

- **Floating Window UI** - Always-on-top, resizable, high DPI support
- **Template Matching** - Uses OpenCV to locate buttons on screen
- **Dual Click Method** - Priority PostMessage for game compatibility, fallback to pyautogui
- **Auto Elevation** - Automatically requests admin permissions
- **Configurable** - Adjust click interval, match threshold, repeat count
- **Log Display** - Real-time operation logs
- **Hotkey Support** - ESC to stop

## Installation

### Prerequisites

- Python 3.7+
- Windows OS

### Install Dependencies

```bash
pip install opencv-python numpy Pillow pyautogui pywin32
```

## Usage

1. Prepare your button templates:
   - Place `button1.png` (first button to click) in the `images/` folder
   - Place `button2.png` (second button to click) in the `images/` folder

2. Run the program:
   ```bash
   python auto_clicker.py
   ```
   Or double-click `run.bat`

3. Configure parameters:
   - **Click Interval**: Time between clicks (default: 1.5s)
   - **Match Threshold**: Template matching sensitivity (0.1-1.0, default: 0.8)
   - **Repeat Count**: Number of cycles (0 = infinite)

4. Click **Test** to verify template recognition

5. Click **Start** to begin auto-clicking

## Workflow

The program follows this sequence:
1. Find and click **Button1** → store coordinates
2. Find and click **Button2** → store coordinates
3. Click stored **Button1** coordinates
4. Loop: Button1 → Button2 → Button1 (repeat)

## Configuration

### Template Images

- Size: No specific requirements, but smaller images are faster
- Format: PNG (recommended)
- Note: Images should be clear screenshots of the buttons

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Click Interval | Time between each click action (seconds) | 1.5 |
| Match Threshold | How similar the match must be (0.1-1.0) | 0.8 |
| Repeat Count | Number of cycles (0 = infinite) | 0 |

## Technical Details

### Click Methods

1. **PostMessage** (Primary)
   - Sends `WM_LBUTTONDOWN`/`WM_LBUTTONUP` directly to the foreground window
   - Works with most games and applications
   - Doesn't require window focus

2. **pyautogui** (Fallback)
   - Moves mouse and performs physical click
   - Good for standard applications

### DPI Awareness

The program automatically enables high DPI awareness to ensure accurate coordinate matching on high-resolution displays.

## Notes

- Run with admin permissions for best compatibility
- Ensure template images match the actual screen content exactly
- Adjust the match threshold if recognition fails
- The ESC key can be used to stop the program at any time
- This tool is for automation purposes only, use responsibly

## License

MIT License - see [LICENSE](LICENSE) for details
