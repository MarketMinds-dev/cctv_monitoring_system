from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QSize

class DoorDetectionTab(QWidget):
    def __init__(self, video_processor, stream_name):
        super().__init__()
        self.video_processor = video_processor
        self.stream_name = stream_name
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Video feed
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("border: 2px solid #4C566A; background-color: #2E3440;")
        self.video_label.setFixedSize(QSize(640, 480))  # Set fixed size for video label
        layout.addWidget(self.video_label)

        # Status
        status_layout = QHBoxLayout()
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(24, 24)
        self.status_label = QLabel("Door Status: Unknown")
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        # Movement
        self.movement_label = QLabel("Movement: Unknown")
        self.movement_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.movement_label)

        # Motion Detection
        self.motion_label = QLabel("Motion: Not Detected")
        self.motion_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.motion_label)

    def update_frame(self):
        frame, detections = self.video_processor.process_frame(self.stream_name)
        if frame is not None:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        door_result = self.video_processor.results[self.stream_name]
        status = door_result['status']
        movement = door_result['movement']

        if door_result['detected']:
            color = "#A3BE8C"  # Green if detected
            icon = "🚪"
        else:
            color = "#BF616A"  # Red if not detected
            icon = "❓"

        self.status_icon.setText(icon)
        self.status_label.setText(f"Door Status: {status}")
        self.status_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")

        if movement:
            self.movement_label.setText(f"Movement: {movement}")
            self.movement_label.setStyleSheet("font-size: 14px; color: #88C0D0;")  # Blue for movement
        else:
            self.movement_label.setText("Movement: Unknown")
            self.movement_label.setStyleSheet("font-size: 14px; color: #D8DEE9;")  # Default color

        # Update motion detection label
        if "Motion Detected" in [d.split(":")[0] for d in detections]:
            self.motion_label.setText("Motion: Detected")
            self.motion_label.setStyleSheet("font-size: 14px; color: #EBCB8B;")  # Yellow for motion
        else:
            self.motion_label.setText("Motion: Not Detected")
            self.motion_label.setStyleSheet("font-size: 14px; color: #D8DEE9;")  # Default color