import sys
import logging
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QPushButton, QShortcut
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon, QPalette, QKeySequence
from gui.video_tab import VideoTab
from gui.cash_drawer_tab import CashDrawerTab
from gui.employee_detection_tab import EmployeeDetectionTab
from gui.door_detection_tab import DoorDetectionTab
from gui.people_counting_tab import PeopleCountingTab
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
        self.settings_tab = SettingsTab(self.update_camera, self.set_feature_active)
        self.alerts_tab = AlertsTab()

        self.tab_widget.addTab(self.video_tab, QIcon("icons/video.png"), "Video Streams")
        self.tab_widget.addTab(self.cash_drawer_tab, QIcon("icons/cash.png"), "Cash Drawer")
        self.tab_widget.addTab(self.employee_detection_tab, QIcon("icons/employee.png"), "Employee Detection")
        self.tab_widget.addTab(self.door_detection_tab, QIcon("icons/door.png"), "Door Detection")
        self.tab_widget.addTab(self.people_counting_tab, QIcon("icons/people.png"), "People Counting")
        self.tab_widget.addTab(self.settings_tab, QIcon("icons/settings.png"), "Settings")
        self.tab_widget.addTab(self.alerts_tab, QIcon("icons/alert.png"), "Alerts")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_active_tab)
        self.timer.start(30)  # Update every 30 ms

        self.alerts_tab.add_alert("System started")

        # Add dark mode toggle button
        self.dark_mode_button = QPushButton("Toggle Dark Mode")
        self.dark_mode_button.clicked.connect(self.toggle_dark_mode)
        self.layout.addWidget(self.dark_mode_button)

        # Set up logging
        logging.basicConfig(filename='cctv_system.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Add keyboard shortcut for dark mode toggle
        self.dark_mode_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self.dark_mode_shortcut.activated.connect(self.toggle_dark_mode)

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def update_active_tab(self):
        current_tab = self.tab_widget.currentWidget()
        if hasattr(current_tab, 'update_frame'):
            current_tab.update_frame()

    def on_tab_changed(self, index):
        current_tab = self.tab_widget.widget(index)
        if hasattr(current_tab, 'activate'):
            current_tab.activate()

    def update_camera(self, stream_name, camera_url):
        success = self.video_processor.set_camera(stream_name, camera_url)
        if success:
            self.alerts_tab.add_alert(f"Camera for {stream_name} updated to {camera_url}")
            logging.info(f"Camera updated: {stream_name} - {camera_url}")
        else:
            self.alerts_tab.add_alert(f"Failed to update camera for {stream_name} to {camera_url}")
            logging.error(f"Failed to update camera: {stream_name} - {camera_url}")
        return success

    def closeEvent(self, event):
        self.video_processor.release()
        super().closeEvent(event)

    def toggle_dark_mode(self):
        if self.palette().color(QPalette.Window).lightness() > 128:
            self.setStyleSheet(self.get_dark_style())
            logging.info("Dark mode enabled")
        else:
            self.setStyleSheet(self.get_light_style())
            logging.info("Light mode enabled")

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

    def set_feature_active(self, feature_name, is_active):
        self.video_processor.set_feature_active(feature_name, is_active)
        self.alerts_tab.add_alert(f"Feature '{feature_name}' {'activated' if is_active else 'deactivated'}")