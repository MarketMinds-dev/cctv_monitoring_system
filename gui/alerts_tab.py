from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt5.QtCore import QDateTime

class AlertsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.alerts_list = QListWidget()
        self.alerts_list.setStyleSheet("background-color: #3B4252; color: #ECEFF4;")
        layout.addWidget(self.alerts_list)

    def add_alert(self, message):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        item = QListWidgetItem(f"{timestamp} - {message}")
        self.alerts_list.insertItem(0, item)  # Add new alerts at the top
        self.alerts_list.scrollToTop()