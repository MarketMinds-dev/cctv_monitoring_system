from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

class FaceRecognitionTab(QWidget):
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

        # Recognized employees list
        self.title_label = QLabel("Recognized Employees")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)

        self.employee_list = QListWidget()
        self.employee_list.setStyleSheet("background-color: #3B4252; color: #ECEFF4;")
        layout.addWidget(self.employee_list)

    def update_frame(self):
        frame, detections = self.video_processor.process_frame(self.stream_name)
        if frame is not None:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        employees = self.video_processor.results[self.stream_name]
        self.employee_list.clear()
        for employee in employees:
            item = QListWidgetItem(f"{employee['name']} - {employee['time']}")
            self.employee_list.addItem(item)