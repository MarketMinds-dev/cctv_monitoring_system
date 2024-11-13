from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QPalette, QColor
from gui.video_tab import VideoTab
from gui.cash_drawer_tab import CashDrawerTab
from gui.employee_detection_tab import EmployeeDetectionTab
from gui.door_detection_tab import DoorDetectionTab
from gui.people_counting_tab import PeopleCountingTab
from gui.face_recognition_tab import FaceRecognitionTab
from gui.settings_tab import SettingsTab
from gui.alerts_tab import AlertsTab
from utils.video_processor import VideoProcessor

class CCTVMonitoringSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CCTV Monitoring System")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(self.get_dark_style())

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.video_processor = VideoProcessor()

        self.video_tab = VideoTab(self.video_processor)
        self.cash_drawer_tab = CashDrawerTab(self.video_processor, 'cash_drawer')
        self.employee_detection_tab = EmployeeDetectionTab(self.video_processor, 'employee_detection')
        self.door_detection_tab = DoorDetectionTab(self.video_processor, 'door_detection')
        self.people_counting_tab = PeopleCountingTab(self.video_processor, 'people_counting')
        self.face_recognition_tab = FaceRecognitionTab(self.video_processor, 'face_recognition')
        self.settings_tab = SettingsTab(self.update_camera)
        self.alerts_tab = AlertsTab()

        self.tab_widget.addTab(self.video_tab, QIcon("icons/video.png"), "Video Streams")
        self.tab_widget.addTab(self.cash_drawer_tab, QIcon("icons/cash.png"), "Cash Drawer")
        self.tab_widget.addTab(self.employee_detection_tab, QIcon("icons/employee.png"), "Employee Detection")
        self.tab_widget.addTab(self.door_detection_tab, QIcon("icons/door.png"), "Door Detection")
        self.tab_widget.addTab(self.people_counting_tab, QIcon("icons/people.png"), "People Counting")
        self.tab_widget.addTab(self.face_recognition_tab, QIcon("icons/face.png"), "Face Recognition")
        self.tab_widget.addTab(self.settings_tab, QIcon("icons/settings.png"), "Settings")
        self.tab_widget.addTab(self.alerts_tab, QIcon("icons/alert.png"), "Alerts")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_all_tabs)
        self.timer.start(30)  # Update every 30 ms

        self.alerts_tab.add_alert("System started")

        # Add dark mode toggle button
        self.dark_mode_button = QPushButton("Toggle Dark Mode")
        self.dark_mode_button.clicked.connect(self.toggle_dark_mode)
        self.layout.addWidget(self.dark_mode_button)

    def update_all_tabs(self):
        for tab in [self.video_tab, self.cash_drawer_tab, self.employee_detection_tab, self.door_detection_tab, 
                    self.people_counting_tab, self.face_recognition_tab]:
            tab.update_frame()

    def update_camera(self, stream_name, camera_url):
        success = self.video_processor.set_camera(stream_name, camera_url)
        if success:
            self.alerts_tab.add_alert(f"Camera for {stream_name} updated to {camera_url}")
        else:
            self.alerts_tab.add_alert(f"Failed to update camera for {stream_name} to {camera_url}")

    def closeEvent(self, event):
        self.video_processor.release()
        super().closeEvent(event)

    def toggle_dark_mode(self):
        if self.palette().color(QPalette.Window).lightness() > 128:
            self.setStyleSheet(self.get_dark_style())
        else:
            self.setStyleSheet(self.get_light_style())

    def get_dark_style(self):
        return """
            QMainWindow, QWidget {
                background-color: #2E3440;
                color: #ECEFF4;
            }
            QTabWidget::pane {
                border: 1px solid #4C566A;
                background-color: #3B4252;
            }
            QTabBar::tab {
                background-color: #2E3440;
                color: #ECEFF4;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3B4252;
                border-bottom: 2px solid #88C0D0;
            }
            QPushButton {
                background-color: #5E81AC;
                color: #ECEFF4;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
        """

    def get_light_style(self):
        return """
            QMainWindow, QWidget {
                background-color: #ECEFF4;
                color: #2E3440;
            }
            QTabWidget::pane {
                border: 1px solid #D8DEE9;
                background-color: #E5E9F0;
            }
            QTabBar::tab {
                background-color: #ECEFF4;
                color: #2E3440;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #E5E9F0;
                border-bottom: 2px solid #5E81AC;
            }
            QPushButton {
                background-color: #5E81AC;
                color: #ECEFF4;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
        """