from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QCheckBox, QGroupBox

class SettingsTab(QWidget):
    def __init__(self, update_camera_callback, set_feature_active_callback):
        super().__init__()
        self.update_camera_callback = update_camera_callback
        self.set_feature_active_callback = set_feature_active_callback
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Camera Settings
        camera_group = QGroupBox("Camera Settings")
        camera_layout = QFormLayout()
        camera_group.setLayout(camera_layout)

        streams = ['cash_drawer', 'employee_detection', 'door_detection', 'people_counting']
        
        self.input_fields = {}
        for stream in streams:
            label = QLabel(f"{stream.replace('_', ' ').title()} Camera URL:")
            input_field = QLineEdit()
            update_button = QPushButton(f"Update {stream.replace('_', ' ').title()} Camera")
            
            update_button.clicked.connect(lambda checked, s=stream: self.update_camera(s))
            
            camera_layout.addRow(label, input_field)
            camera_layout.addRow(update_button)
            camera_layout.addRow(QLabel())  # Empty label for spacing
            
            self.input_fields[stream] = input_field

        layout.addWidget(camera_group)

        # Feature Toggles
        feature_group = QGroupBox("Feature Toggles")
        feature_layout = QVBoxLayout()
        feature_group.setLayout(feature_layout)

        self.feature_toggles = {}
        for stream in streams:
            checkbox = QCheckBox(f"Enable {stream.replace('_', ' ').title()}")
            checkbox.toggled.connect(lambda checked, s=stream: self.toggle_feature(s, checked))
            feature_layout.addWidget(checkbox)
            self.feature_toggles[stream] = checkbox

        layout.addWidget(feature_group)

    def update_camera(self, stream_name):
        camera_url = self.input_fields[stream_name].text()
        success = self.update_camera_callback(stream_name, camera_url)
        if success:
            print(f"Camera for {stream_name} updated successfully")
        else:
            print(f"Failed to update camera for {stream_name}")

    def toggle_feature(self, stream_name, is_active):
        self.set_feature_active_callback(stream_name, is_active)

    def set_camera_url(self, stream_name, url):
        self.input_fields[stream_name].setText(url)

    def set_feature_active(self, stream_name, is_active):
        self.feature_toggles[stream_name].setChecked(is_active)