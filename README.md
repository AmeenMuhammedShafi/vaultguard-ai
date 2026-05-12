# VaultGuard AI - Advanced Access Control Systems

**Two complementary AI-powered access control solutions for secure facilities management.**

---

## 🏗️ Project Overview

VaultGuard AI contains two distinct access control systems:

### 1. **Face Recognition** - Dual-Person Biometric Authorization
- Enrolls employees via face capture
- Two-person sequential authentication required
- Person counting during entry window
- Tailgating detection
- **Location:** `face-recognition/`

### 2. **Strong Room AI** - YOLO-Based Occupancy Monitoring
- Real-time person detection via YOLOv8
- Occupancy state tracking (VALID, WARNING, ALERT)
- Violation detection when occupancy violates policies
- Lightweight and fast inference
- **Location:** `strong-room-ai/`

---

## 📁 Workspace Structure

```
virtuosoft/
├── face-recognition/          # Biometric dual-person access control
│   ├── main.py
│   ├── enrollment/
│   ├── auth/
│   ├── core/
│   ├── database/
│   └── README.md
│
├── strong-room-ai/            # YOLO-based occupancy monitoring
│   ├── main.py
│   ├── auth/
│   ├── database/
│   └── README.md
│
└── README.md                  # This file
```

---

## 🚀 Quick Start

### Face Recognition System
```bash
cd face-recognition

# Step 1: Enroll employees (one-time)
python enrollment/enroll_employee.py

# Step 2: Run access control
python main.py
```

### Strong Room AI System
```bash
cd strong-room-ai

# Run YOLO-based person detection
python main.py
```

---

## 🔧 Installation

### Requirements
- Python 3.9+
- OpenCV (`cv2`)
- NumPy
- DeepFace
- Ultralytics YOLO

### Setup Virtual Environment
```bash
python -m venv .venv-1
source .venv-1/Scripts/activate  # Windows
# or
source .venv-1/bin/activate      # macOS/Linux

pip install opencv-python numpy deepface ultralytics
```

---

## 📊 System Comparison

| Feature | Face Recognition | Strong Room AI |
|---------|------------------|----------------|
| Detection Method | Face-based biometrics | YOLO person detection |
| Authentication | DeepFace embeddings | Real-time counting |
| Capacity Control | Dual-person requirement | Occupancy limits |
| Use Case | Secure entry authorization | Room occupancy monitoring |
| Speed | 1-5ms per face | 30-50ms per frame |
| Scalability | 100+ employees | Unlimited occupancy |

---

## 🔐 Security Features

### Face Recognition
- Liveness detection (anti-spoofing)
- Duplicate authentication prevention
- Embedding-based matching (no image storage)
- Tailgating detection
- Entry window validation

### Strong Room AI
- Real-time violation alerts
- Configurable occupancy thresholds
- Persistent tracking across frames
- Visual state indicators (color-coded)

---

## 📝 Configuration

Each system has its own configuration in their respective directories. See individual READMEs:
- [Face Recognition README](face-recognition/README.md)
- [Strong Room AI README](strong-room-ai/README.md)

---

## 🛠️ Architecture Highlights

### Production-Grade Design
- **Modular code** - Separate concerns (detection, embedding, storage)
- **Precomputed embeddings** - Fast inference (no model loading per frame)
- **Persistent tracking** - Centroid-based ID assignment
- **Error handling** - Graceful fallbacks and logging

### Performance
- Face detection: 0.6-0.8ms per face (OpenCV DNN)
- Embedding extraction: 50-100ms (DeepFace, first load)
- Embedding matching: 1-5ms (cosine similarity)
- Person tracking: 20-30ms (YOLO)

---

## 📦 Dependencies

### Face Recognition
```
opencv-python>=4.5.0
numpy>=1.20.0
deepface>=0.0.75
```

### Strong Room AI
```
opencv-python>=4.5.0
numpy>=1.20.0
ultralytics>=8.0.0
torch>=1.9.0
```

---

## 🔄 Workflow Examples

### Face Recognition: Full Cycle
1. Employee A authenticates with face
2. Employee B authenticates with face
3. Door unlocks for 2 minutes
4. Camera monitors entry window
5. System counts actual vs expected persons
6. Detects any unauthorized entries (tailgating)
7. Door locks after window closes

### Strong Room AI: Active Monitoring
1. YOLO detects persons in frame
2. Tracks person IDs across frames
3. Counts active occupants
4. VALID: Exactly 2 persons
5. WARNING: != 2 persons for <1 second
6. ALERT: != 2 persons for >1 second

---

## 🐛 Troubleshooting

### Camera Issues
```bash
# Test camera access
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

### Model Files Missing
- Ensure `deploy.prototxt` and `.caffemodel` files are in project root
- Files are searched up the directory tree automatically

### DeepFace/YOLO Models
- First run downloads large models (~1GB combined)
- Models cached in `~/.deepface` and `~/.yolo`

---

## 📄 License

All projects in VaultGuard AI are part of the unified access control platform.

---

## 👤 Authors & Contributors

VaultGuard AI Development Team

---

## 📞 Support

For issues or questions, refer to individual project READMEs or check system logs for detailed error messages.
