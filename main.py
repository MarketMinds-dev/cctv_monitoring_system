import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import CCTVMonitoringSystem

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CCTVMonitoringSystem()
    window.show()
    sys.exit(app.exec_())