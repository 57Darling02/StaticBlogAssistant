from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt
from core import SettingsManager, SignalBus

signal_bus = SignalBus.get_instance()


class CommandsButtonWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = SettingsManager.get_instance()
        self._init_ui()
        signal_bus.settings_changed.connect(self._update_commands)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        # 使用QListWidget替代原有布局
        self.commands_list = QListWidget()
        self.commands_list.itemClicked.connect(self._on_item_clicked)
        self.commands_list.setStyleSheet("""
            QListWidget {
                border: none;
                outline: 0;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
        """)
        self.main_layout.addWidget(self.commands_list)

        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新命令列表")
        self.refresh_btn.clicked.connect(self._update_commands)
        self.main_layout.addWidget(self.refresh_btn)

        self._update_commands()

    def _on_item_clicked(self, item):
        """列表项点击事件处理"""
        command = item.data(Qt.UserRole)  # 从数据角色获取命令
        signal_bus.execute_command.emit(command)

    def _update_commands(self):
        """更新命令列表"""
        self.commands_list.clear()
        for name, cmd in self.settings.script_commands.items():
            item = QListWidgetItem(f"⚡ {name}")
            item.setData(Qt.UserRole, cmd)  # 将命令存储在数据角色中
            item.setFlags(item.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.commands_list.addItem(item)