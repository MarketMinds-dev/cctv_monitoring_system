from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout

class SettingsTab(QWidget):
    def __init__(self, update_camera_callback):
        super().__init__()
        self.update_camera_callback = update_camera_callback
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        form_layout = QFormLayout()
        
        streams = ['cash_drawer', 'employee_detection', 'door_detection', 'people_counting', 'face_recognition']
        
        self.input_fields = {}
        for stream in streams:
            label = QLabel(f"{stream.replace('_', ' ').title()} Camera URL:")
            input_field = QLineEdit()
            update_button = QPushButton(f"Update {stream.replace('_', ' ').title()} Camera")
            
            update_button.clicked.connect(lambda checked, s=stream: self.update_camera(s))
            
            form_layout.addRow(label, input_field)
            form_layout.addRow(update_button)
            form_layout.addRow(QLabel())  # Empty label for spacing
            
            self.input_fields[stream] = input_field

        layout.addLayout(form_layout)

    def update_camera(self, stream_name):
        camera_url = self.input_fields[stream_name].text()
        self.update_camera_callback(stream_name, camera_url)