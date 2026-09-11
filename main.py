"""Application entry point; all task execution lives outside the window."""
import sys

from PySide6.QtWidgets import QApplication

from logger import setup_logger
from config import get_config
from styles import apply_theme
from workbench import Workbench


MainWindow = Workbench


def main():
    setup_logger()
    app = QApplication(sys.argv)
    app.setApplicationName("SkyDreamBox")
    app.setOrganizationName("SkyDreamBox")
    app.setStyle("Fusion")
    apply_theme(app, get_config().get("theme", "light"))
    if len(sys.argv) == 3 and sys.argv[1] == "--verify-install":
        from diagnostics import InstallationCheck
        check = InstallationCheck(app, sys.argv[2])
        return app.exec()
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
