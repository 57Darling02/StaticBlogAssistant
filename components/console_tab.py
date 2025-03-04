import re
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from core import SignalBus,CommandExecutor
signal_bus = SignalBus.get_instance()
class ConsoleWidget(QWidget):
    command_triggered = Signal(str)
    def __init__(self):
        super().__init__()
        """初始化控制台标签页"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 输出区域
        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("""
                        QPlainTextEdit {
                            background-color: #1E1E1E;
                            color: #D4D4D4;
                            font-family: Consolas;
                            font-size: 10pt;
                        }
                    """)

        # 输入区域
        self.console_input = QPlainTextEdit()
        self.console_input.setMaximumHeight(60)
        self.console_input.setStyleSheet("""
                        QPlainTextEdit {
                            background-color: #252526;
                            color: #CCCCCC;
                            border-top: 1px solid #383838;
                            font-family: Consolas;
                            font-size: 10pt;
                        }
                    """)
        self.console_input.keyPressEvent = self._console_input_key_handler

        # 载入
        layout.addWidget(self.console_output, 3)
        layout.addWidget(self.console_input, 1)

        self._append_console("欢迎使用StaticBlogAssistant！", "system")
        self._append_console(f"", "system")


        # 初始化进程
        self.current_process = None
        self.command_history = []
        self.history_index = -1
        self.command_executor = CommandExecutor()
        # 信号连接
        signal_bus.output_received.connect(self._append_console)

    def _console_input_key_handler(self, event):
        """处理控制台输入框的键盘事件"""
        # 回车执行命令
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not event.modifiers():
            command = self.console_input.toPlainText().strip()
            if command:
                self.command_history.append(command)
                self.history_index = len(self.command_history)
                signal_bus.execute_command.emit(command)
                self.console_input.clear()
            return
        # 终止进程处理（Ctrl+C 或 ESC）
        if event.key() == Qt.Key_Escape or (event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C):
            signal_bus.stop_command.emit()
            self.console_input.clear()
            return
        # 上下箭头切换历史命令
        if event.key() == Qt.Key_Up:
            if self.command_history:
                self.history_index = max(0, self.history_index - 1)
                self._show_history_command()
        elif event.key() == Qt.Key_Down:
            if self.command_history:
                self.history_index = min(len(self.command_history), self.history_index + 1)
                self._show_history_command()
        else:
            QPlainTextEdit.keyPressEvent(self.console_input, event)  # 显式调用父类方法

    def _show_history_command(self):
        """显示历史命令"""
        if 0 <= self.history_index < len(self.command_history):
            self.console_input.setPlainText(self.command_history[self.history_index])
    def clear_console(self):
        """清空控制台"""
        self.console_output.clear()

    def _append_console(self, text, msg_type="output"):
        """添加格式化输出"""
        cursor = self.console_output.textCursor()
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        clean_text = ansi_escape.sub('', text)
        # 类型颜色映射
        colors = {
            "input": "#569CD6",  # 蓝色
            "output": "#D4D4D4",  # 白色
            "error": "#F44747",  # 红色
            "system": "#43B581"  # 绿色
        }

        # 添加HTML格式内容
        html = f'<span style="color:{colors.get(msg_type, "#FFFFFF")}">{clean_text}</span>'
        cursor.insertHtml(html + "<br>")

        # 自动滚动到底部
        self.console_output.ensureCursorVisible()