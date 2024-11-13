from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget
from PyQt5.QtCore import QDateTime

class ResultsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.results_list = QListWidget()
        layout.addWidget(self.results_list)
        self.setLayout(layout)

    def add_result(self, result):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.results_list.addItem(f"{timestamp}: {result}")
        self.results_list.scrollToBottom()