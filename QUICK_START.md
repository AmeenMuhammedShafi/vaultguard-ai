# Quick Start Guide - VaultGuard AI with Improvements

## Overview

This guide walks through running the enhanced VaultGuard AI system with all new features:
- ✅ Doorway line crossing detection
- ✅ Event logging with snapshots
- ✅ Frame skipping optimization
- ✅ Web dashboard

---

## Prerequisites

### System Requirements
- Python 3.8+
- Webcam / USB camera
- 4GB RAM (8GB+ recommended for GPU)
- Optional: NVIDIA GPU (for faster YOLO inference)

### Installation

```bash
# Navigate to workspace
cd c:\Users\acer\Desktop\virtuosoft

# Create/activate virtual environment
python -m venv .venv-1
.venv-1\Scripts\activate  # Windows
source .venv-1/bin/activate  # macOS/Linux

# Install dependencies
pip install -r face-recognition/requirements.txt
```

---

## Running the Full System

### Option 1: Main System Only (No Dashboard)

```bash
cd c:\Users\acer\Desktop\virtuosoft
python face-recognition/main.py
```

**What happens:**
1. PHASE 1: Enroll or authenticate 2 people
   - Press SPACE to authenticate
   - Need 2 different authorized users
   
2. PHASE 2: Entry window opens
   - Door unlocks for 10 seconds
   - People walk through
   - System counts entries using:
     - YOLO person detection
     - Doorway line crossing
     - Persistent tracking
   
3. Entry verification
   - Compares actual crossings vs expected
   - Logs event to `logs/events.jsonl`
   - Saves snapshot on violations

**Output files:**
```
logs/
├── events.jsonl          # All events
└── snapshots/            # Violation images
```

### Option 2: Main System + Web Dashboard (Recommended)

Create a new file `face-recognition/run_with_dashboard.py`:

```python
import threading
import time
from main import DualPersonAccessControlDemo
from dashboard.app import run_dashboard

# Start dashboard in background thread
print("\n🚀 Starting web dashboard...")
dashboard_thread = threading.Thread(
    target=run_dashboard, 
    kwargs={'host': '0.0.0.0', 'port': 5000, 'debug': False}
)
dashboard_thread.daemon = True
dashboard_thread.start()

# Wait for dashboard to start
time.sleep(2)
print("\n📊 Dashboard ready at: http://localhost:5000")
print("=" * 70)

# Run main system
demo = DualPersonAccessControlDemo()
demo.demo_interactive()
```

Then run:

```bash
cd face-recognition
python run_with_dashboard.py
```

---

## Using the Web Dashboard

### Access Dashboard

1. **Open in browser:**
   ```
   http://localhost:5000
   ```

2. **What you see:**
   - 🟢 System status indicator
   - 📊 Statistics (total events, valid entries, tailgating count)
   - 📹 Live camera feed
   - 📋 Recent event history
   - 💾 Export button

### Dashboard Features

**Real-Time Statistics:**
- Total events logged
- Successful entries
- Tailgating/violation count
- Overall success rate

**Event History:**
- Last 10 events with full details
- Timestamp, authorized IDs, entry count
- Visual badges (VALID, VIOLATION, TAILGATING)
- Event snapshots available

**Data Export:**
- Click "Export as CSV" button
- Downloads all events with metadata
- Compatible with Excel, Tableau, etc.

---

## Configuration

### Adjust Doorway Line Position

Edit `face-recognition/core/access_control.py`:

```python
# In __init__ method:
self.doorway_detector = DoorwayLineCrossingDetector(line_y=300)
#                                                         ^^^
# Change this value based on camera height
# Lower value = line closer to bottom
# Higher value = line closer to top
```

### Enable/Disable Frame Skipping

In `face-recognition/main.py`, `run_entry_phase()` method:

```python
display_frame, result = self.access_control.process_entry_frame(
    frame,
    frame_skip=2  # Change to 1 for all frames, 3 for more skip
)
```

Frame skip values:
- `1` = Process every frame (most accurate, slower)
- `2` = Process every 2nd frame (balanced)
- `3` = Process every 3rd frame (fastest, may miss entries)

### Change Dashboard Port

Edit `run_with_dashboard.py`:

```python
dashboard_thread = threading.Thread(
    target=run_dashboard, 
    kwargs={'host': '0.0.0.0', 'port': 8080}  # Changed to 8080
)
```

---

## Testing the System

### Test 1: Basic Enrollment & Authentication

```bash
python face-recognition/main.py

# Menu: Select option 1 (Run full access control cycle)
# Enroll 2 employees:
#   - ALICE_001 (3 face captures)
#   - BOB_002 (3 face captures)
# Then authenticate both
```

### Test 2: Entry Window with Doorway Line

```bash
# After authentication, 2 people walk through doorway
# Observe:
# - Green line drawn on video
# - Crossing count increases as people cross line
# - People loitering near line don't count
```

### Test 3: Event Logging

```bash
# Check logs directory
ls -la logs/events.jsonl

# View last event
tail -1 logs/events.jsonl | python -m json.tool
```

### Test 4: Dashboard Visualization

```bash
# Open http://localhost:5000
# Walk through doorway
# Observe statistics update in real-time
# Take snapshot on violation (3+ people)
# Export CSV
```

---

## Common Issues & Troubleshooting

### Issue: "YOLO model not found"
```
Error: Model yolov8m.pt not found
```

**Solution:**
```bash
# Download model explicitly
pip install ultralytics
python -c "from ultralytics import YOLO; YOLO('yolov8m.pt')"
```

### Issue: "No camera detected"
```
ERROR: Could not open camera!
```

**Solution:**
```bash
# Check camera exists
# Windows: Camera app should work
# Linux: ls /dev/video*

# Try different camera index
cv2.VideoCapture(1)  # Instead of 0
```

### Issue: "Dashboard won't load"
```
Connection refused on http://localhost:5000
```

**Solution:**
```bash
# Check Flask is running in separate window
python -m dashboard.app

# Check port is available
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows
```

### Issue: "Doorway line in wrong place"

**Solution:**
```python
# Adjust line_y in access_control.py
# line_y = 300  # Try 250, 350, etc based on camera angle
```

### Issue: "Frame drops during entry"

**Solution:**
```python
# Increase frame_skip to reduce processing
frame_skip=3  # Instead of 1 or 2
```

---

## Understanding the Event Log

### Event Structure

```json
{
    "event_id": "20250513_142301_456",
    "timestamp": "2025-05-13T14:23:01.456789",
    "authorized_ids": ["ALICE_001", "BOB_002"],
    "expected_count": 2,
    "actual_count": 2,
    "is_valid": true,
    "tailgating": false,
    "snapshot": "snapshots/20250513_142301_456.jpg",
    "metadata": {
        "detection_method": "YOLO",
        "frame_skip": 1,
        "duration": 45.2
    }
}
```

### Reading Events

```bash
# Last event
tail -1 logs/events.jsonl | python -m json.tool

# All events from today
grep "2025-05-13" logs/events.jsonl

# Count violations
grep '"is_valid": false' logs/events.jsonl | wc -l

# Count tailgating
grep '"tailgating": true' logs/events.jsonl | wc -l
```

---

## Performance Tuning

### For Low-End Hardware

```python
# Use smaller YOLO model
self.yolo_model = YOLO("yolov8n.pt")  # nano instead of medium

# Skip more frames
frame_skip=3

# Reduce video resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
```

### For High-Performance Setup

```python
# Use larger YOLO model
self.yolo_model = YOLO("yolov8x.pt")  # extra-large

# Process every frame
frame_skip=1

# Increase resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
```

---

## File Structure

```
virtuosoft/
├── face-recognition/
│   ├── main.py                          # Main entry point
│   ├── requirements.txt                 # Dependencies
│   │
│   ├── core/
│   │   ├── access_control.py            # Main controller (improved)
│   │   ├── doorway_detector.py          # NEW: Line crossing detection
│   │   ├── event_logger.py              # NEW: Event persistence
│   │   ├── authentication_terminal.py
│   │   ├── entry_window.py
│   │   ├── person_tracker.py
│   │   └── body_counter.py
│   │
│   ├── auth/
│   │   ├── face_detector.py
│   │   ├── embedding_matcher.py
│   │   └── liveness.py
│   │
│   ├── enrollment/
│   │   └── enroll_employee.py
│   │
│   ├── database/
│   │   └── embeddings_store.py
│   │
│   ├── dashboard/                       # NEW: Web dashboard
│   │   ├── app.py
│   │   ├── __init__.py
│   │   ├── README.md
│   │   └── templates/
│   │       └── dashboard.html
│   │
│   └── logs/                            # NEW: Event logs
│       ├── events.jsonl
│       └── snapshots/
│
└── IMPROVEMENTS.md                      # Detailed changes document
```

---

## Next Steps

### After Basic Testing
1. ✅ Enroll more employees
2. ✅ Adjust doorway line position for your setup
3. ✅ Optimize frame_skip for your hardware
4. ✅ Archive old events regularly

### For Production Deployment
1. Move model weights to `models/` directory
2. Set up automated event backup
3. Configure dashboard security (authentication)
4. Deploy on secure server with HTTPS
5. Integrate with building security system

### Advanced Features (Future)
- Multi-camera support
- Real-time email alerts
- Analytics dashboard
- Machine learning models for behavior analysis

---

## Support Resources

- **IMPROVEMENTS.md** - Detailed explanation of all changes
- **face-recognition/README.md** - Original system documentation
- **face-recognition/dashboard/README.md** - Dashboard API reference
- **logs/events.jsonl** - Event audit trail

---

## Conclusion

You now have:
✅ Reliable person counting (doorway line detection)
✅ Auditable events (persistent logging)
✅ Fast processing (frame skipping)
✅ Professional monitoring (web dashboard)

Happy secure processing! 🔐

