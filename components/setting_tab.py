# setting_tab.py
import os

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (QWidget, QFormLayout, QLineEdit, QPushButton,
                               QFileDialog, QTextEdit, QVBoxLayout, QScrollArea,
                               QHBoxLayout, QLabel, QMessageBox, QListWidgetItem, QListWidget)

from core import SettingsManager, SignalBus

signal_bus = SignalBus.get_instance()
settings_manager = SettingsManager.get_instance()
class SettingTab(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = settings_manager
        self.init_ui()

    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QFormLayout(content)

        # 博客根目录
        self.blog_root_edit = QLineEdit(self.settings.blog_root)
        browse_blog_btn = self.create_browse_button(
            self.blog_root_edit, directory=True)
        layout.addRow("博客根目录：", self.create_path_layout(
            self.blog_root_edit, browse_blog_btn))
        if not os.path.exists(self.settings.blog_root):
            QMessageBox.warning(self, "警告", "博客根目录未设置！")
            browse_blog_btn.clicked.emit()


        # 编辑器路径
        self.editor_edit = QLineEdit(self.settings.editor_path)
        self.editor_edit.setPlaceholderText("为空则调用默认编辑器")
        browse_editor_btn = self.create_browse_button(self.editor_edit)
        layout.addRow("编辑器路径：", self.create_path_layout(
            self.editor_edit, browse_editor_btn))

        # 默认内容
        self.content_edit = QTextEdit()
        self.content_edit.setText(self.settings.default_content)
        layout.addRow("默认内容模板：", self.content_edit)

        # 脚本命令配置
        self.commands_widget = CommandsWidget(
            self.settings.script_commands)
        layout.addRow("脚本命令：", self.commands_widget)

        # 保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_settings)
        layout.addRow(save_btn)
        reset_btn = QPushButton("恢复默认设置")
        reset_btn.clicked.connect(self.reset_settings)
        layout.addRow(reset_btn)

        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def reset_settings(self):
        confirm = QMessageBox.question(self, "确认重置", "将清除所有设置，是否继续？")
        if confirm == QMessageBox.Yes:
            self.settings.clear()
            QMessageBox.information(self, "成功", "设置已重置,重新启动程序生效(后悔药，现在点击保存还能后悔)")


    def create_path_layout(self, edit, button):
        layout = QHBoxLayout()
        layout.addWidget(edit)
        layout.addWidget(button)
        return layout

    def create_browse_button(self, target_edit, directory=False):
        btn = QPushButton("浏览...")
        btn.clicked.connect(lambda: self.browse_path(target_edit, directory))
        return btn

    def browse_path(self, target_edit, is_directory):
        if is_directory:
            path = QFileDialog.getExistingDirectory(self, "选择目录", target_edit.text())
        else:
            path, _ = QFileDialog.getOpenFileName(self, "选择文件", target_edit.text())
        if path:
            target_edit.setText(path)
            self.save_settings()

    def save_settings(self):
        self.settings.blog_root = self.blog_root_edit.text()
        self.settings.editor_path = self.editor_edit.text()
        self.settings.default_content = self.content_edit.toPlainText()
        try:
            # 获取有效命令（自动过滤空项）
            valid_commands = self.commands_widget.get_commands()

            # 更新设置
            self.settings.script_commands = valid_commands
            self.settings.save()
            QMessageBox.information(self, "成功", "配置已保存")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")


class CommandsWidget(QWidget):
    # commands_updated = Signal(dict)  # 新增数据更新信号

    def __init__(self, commands):
        super().__init__()
        self._command_map = commands.copy()
        self._original_names = set(commands.keys())  # 用于名称冲突检测
        self._current_editing_item = None  # 跟踪正在编辑的项
        self.init_ui()
        self._load_commands()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 命令列表
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemChanged.connect(self._handle_item_change)

        # 添加按钮
        self.add_btn = QPushButton("➕ 添加新命令")
        self.add_btn.clicked.connect(self._add_command)

        layout.addWidget(self.list_widget)
        layout.addWidget(self.add_btn)

    def _load_commands(self):
        """初始化加载命令列表"""
        self.list_widget.clear()
        for name, cmd in self._command_map.items():
            self._create_list_item(name, cmd)

    def _create_list_item(self, name, cmd):
        """创建单个列表项"""
        item = QListWidgetItem()
        item.setData(Qt.UserRole, name)  # 存储原始名称
        widget = self._create_item_widget(name, cmd)
        item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)

    def _create_item_widget(self, name, cmd):
        """创建项内容控件"""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # 名称输入
        name_edit = QLineEdit(name)
        name_edit.setPlaceholderText("命令名称")
        name_edit.editingFinished.connect(lambda: self._validate_name_change(name_edit, name))

        # 命令输入
        cmd_edit = QLineEdit(cmd)
        cmd_edit.setPlaceholderText("执行命令")
        cmd_edit.textChanged.connect(lambda text: self._update_command(name, text))

        # 删除按钮
        del_btn = QPushButton("🗑️")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(lambda: self._remove_command(name))

        layout.addWidget(QLabel("名称："))
        layout.addWidget(name_edit)
        layout.addWidget(QLabel("命令："))
        layout.addWidget(cmd_edit)
        layout.addWidget(del_btn)
        return widget

    def _validate_name_change(self, editor, old_name):
        """验证名称修改"""
        new_name = editor.text().strip()
        if not new_name:
            editor.setText(old_name)
            return
        if new_name == old_name:
            return

        if new_name in self._command_map:
            QMessageBox.warning(self, "名称冲突", "该名称已存在，请使用唯一名称")
            editor.setText(old_name)
        else:
            self._update_command_name(old_name, new_name)

    def _update_command_name(self, old_name, new_name):
        """更新命令名称"""
        # 更新数据
        self._command_map[new_name] = self._command_map.pop(old_name)

        # 局部更新列表项
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            if item.data(Qt.UserRole) == old_name:
                widget = self.list_widget.itemWidget(item)
                name_edit = widget.findChild(QLineEdit)
                name_edit.setText(new_name)
                item.setData(Qt.UserRole, new_name)
                break

        # self.commands_updated.emit(self.get_commands())

    def _update_command(self, name, new_cmd):
        """更新命令内容"""
        self._command_map[name] = new_cmd
        # self.commands_updated.emit(self.get_commands())

    def _add_command(self):
        """添加新命令"""
        base_name = "新命令"
        counter = 1
        while f"{base_name}{counter}" in self._command_map:
            counter += 1
        new_name = f"{base_name}{counter}"

        self._command_map[new_name] = ""
        self._create_list_item(new_name, "")
        # self.commands_updated.emit(self.get_commands())

    def _remove_command(self, name):
        """删除命令"""
        confirm = QMessageBox.question(
            self, "确认删除",
            f"确定要删除命令 '{name}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            # 查找并移除对应项
            for index in range(self.list_widget.count()):
                item = self.list_widget.item(index)
                if item.data(Qt.UserRole) == name:
                    self.list_widget.takeItem(index)
                    break
            del self._command_map[name]
            # self.commands_updated.emit(self.get_commands())

    def get_commands(self):
        """获取有效命令"""
        return {k: v for k, v in self._command_map.items() if k.strip() and v.strip()}

    def _handle_item_change(self, item):
        """处理项变化事件（用于未来扩展）"""
        pass