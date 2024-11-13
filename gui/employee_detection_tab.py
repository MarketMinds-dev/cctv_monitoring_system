from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer

class EmployeeDetectionTab(QWidget):
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
        layout.addWidget(self.video_label)

        # Status
        status_layout = QHBoxLayout()
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(24, 24)
        self.status_label = QLabel("Employee Status: Present")
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        # Timer
        self.timer_label = QLabel("Time since last detection: 0 minutes")
        self.timer_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.timer_label)

        self.minutes_passed = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(60000)  # Update every minute

    def update_frame(self):
        frame, detections = self.video_processor.process_frame(self.stream_name)
        if frame is not None:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        is_present = self.video_processor.results[self.stream_name]
        status = "Present" if is_present else "Absent"
        color = "#A3BE8C" if is_present else "#BF616A"  # Green if present, red if absent
        icon = "👤" if is_present else "❓"
        self.status_icon.setText(icon)
        self.status_label.setText(f"Employee Status: {status}")
        self.status_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")

        if is_present:
            self.minutes_passed = 0
        self.update_timer()

    def update_timer(self):
        self.minutes_passed += 1
        self.timer_label.setText(f"Time since last detection: {self.minutes_passed} minutes")
        if self.minutes_passed >= 10:
            self.timer_label.setStyleSheet("font-size: 14px; color: #BF616A;")
        else:
            self.timer_label.setStyleSheet("font-size: 14px; color: #D8DEE9;")