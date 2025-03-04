import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QSplitter, QTabWidget, QLabel
)
from components import ConsoleWidget, SettingTab, FileTreeWidget, CommandsButtonWidget
from core import SettingsManager, SignalBus

signal_bus = SignalBus.get_instance()
settings_manager = SettingsManager.get_instance()
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("StaticBlogAssistant")
        self.resize(1024, 768)

        # 居中窗口
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen_geometry.width() - self.width()) // 2,
            (screen_geometry.height() - self.height()) // 2
        )

        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 水平分割器
        content_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(content_splitter)

        # 左侧文件树
        self.file_tree = FileTreeWidget()
        content_splitter.addWidget(self.file_tree)

        # 右侧标签页
        self.workspace_tabs = QTabWidget()
        content_splitter.addWidget(self.workspace_tabs)

        # 添加标签页
        self.setting_tab = SettingTab()
        self.console_widget = ConsoleWidget()
        self.doc_tab = CommandsButtonWidget()

        self.workspace_tabs.addTab(self.doc_tab, "脚本")
        self.workspace_tabs.addTab(self.console_widget, "终端")
        self.workspace_tabs.addTab(self.setting_tab, "设置")

        # 分割比例
        content_splitter.setSizes([400, 800])

        # 全局样式
        self.setStyleSheet("""
            QPushButton {
                border-radius: 10px;
                padding: 5px 12px;
                background: white;
                color: black;
                border: 1px solid rgba(255,255,255,0.1);
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QTextEdit, QPlainTextEdit {
                border-radius: 10px;
                border: 2px solid #CCCCCC;
                padding: 5px;
                background: white;
            }
            QTabWidget::pane {
                border-radius: 12px;
                border: 1px solid #AAAAAA;
                margin: 5px;
            }
            QTreeView {
                border-radius: 12px;
                border: 1px solid #AAAAAA;
                margin: 5px;
                background: #FFFFFF;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())