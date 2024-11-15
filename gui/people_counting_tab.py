from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QProgressBar
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

class PeopleCountingTab(QWidget):
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
        self.video_label.setFixedSize(640, 480)  # Set fixed size for the video label
        layout.addWidget(self.video_label)

        # Total count
        self.total_label = QLabel("Total People: 0")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.total_label)

        # Male count
        male_layout = QHBoxLayout()
        self.male_label = QLabel("Male: 0")
        self.male_progress = QProgressBar()
        self.male_progress.setStyleSheet("QProgressBar::chunk { background-color: #5E81AC; }")
        male_layout.addWidget(self.male_label)
        male_layout.addWidget(self.male_progress)
        layout.addLayout(male_layout)

        # Female count
        female_layout = QHBoxLayout()
        self.female_label = QLabel("Female: 0")
        self.female_progress = QProgressBar()
        self.female_progress.setStyleSheet("QProgressBar::chunk { background-color: #B48EAD; }")
        female_layout.addWidget(self.female_label)
        female_layout.addWidget(self.female_progress)
        layout.addLayout(female_layout)

    def update_frame(self):
        frame, detections = self.video_processor.process_frame(self.stream_name)
        if frame is not None:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(640, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_label.setPixmap(scaled_pixmap)

        counts = self.video_processor.results[self.stream_name]
        total = counts['male'] + counts['female']
        self.total_label.setText(f"Total People: {total}")
        self.male_label.setText(f"Male: {counts['male']}")
        self.female_label.setText(f"Female: {counts['female']}")
        
        if total > 0:
            male_percentage = (counts['male'] / total) * 100
            female_percentage = (counts['female'] / total) * 100
            self.male_progress.setValue(int(male_percentage))
            self.female_progress.setValue(int(female_percentage))
        else:
            self.male_progress.setValue(0)
            self.female_progress.setValue(0)