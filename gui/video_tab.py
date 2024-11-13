from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

class VideoTab(QWidget):
    def __init__(self, video_processor):
        super().__init__()
        self.video_processor = video_processor
        layout = QGridLayout()
        self.setLayout(layout)

        self.video_labels = {}
        streams = ['cash_drawer', 'employee_detection', 'door_detection', 'people_counting', 'face_recognition']
        
        for i, stream in enumerate(streams):
            label = QLabel()
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("border: 2px solid #4C566A; background-color: #2E3440;")
            layout.addWidget(label, i // 3, i % 3)
            self.video_labels[stream] = label

    def update_frame(self):
        for stream, label in self.video_labels.items():
            frame, _ = self.video_processor.process_frame(stream)
            if frame is not None:
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                label.setText(f"No feed for {stream}")