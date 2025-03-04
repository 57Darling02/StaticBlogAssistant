import sys
from PySide6.QtCore import QObject, Signal, QProcess,QProcessEnvironment
from  .utils import decode
from .signal_bus import SignalBus
from .settings_manager import SettingsManager
signal_bus = SignalBus.get_instance()
settings_manager = SettingsManager.get_instance()
class CommandExecutor(QObject):
    def __init__(self):
        super().__init__()
        self.current_process = None
        signal_bus.execute_command.connect(self.execute)
        signal_bus.stop_command.connect(self.stop_current_process)

    def execute(self, command):
        if self.current_process and self.current_process.state() == QProcess.Running:
            signal_bus.output_received.emit("已有命令正在运行", "error")
            return

        self.current_process = QProcess()
        """执行系统命令"""
        if self.current_process and self.current_process.state() == QProcess.Running:
            signal_bus.output_received.emit("已有命令正在运行", "error")
            return

        signal_bus.output_received.emit(f"> {command}", "input")

        self.current_process = QProcess()
        self.current_process.readyReadStandardOutput.connect(self._handle_stdout)
        self.current_process.readyReadStandardError.connect(self._handle_stderr)
        self.current_process.finished.connect(self._handle_process_finished)

        self.current_process.setWorkingDirectory(settings_manager.blog_root)

        # 继承系统环境变量
        env = QProcessEnvironment.systemEnvironment()
        # Windows下强制UTF-8输出
        if sys.platform == "win32":
            env.insert("PYTHONIOENCODING", "utf-8")
            env.insert("PYTHONUTF8", "1")
        self.current_process.setProcessEnvironment(env)
        # 根据系统设置shell
        if sys.platform == "win32":
            self.current_process.setProgram("cmd")
            self.current_process.setArguments(["/c", command])
        else:
            self.current_process.setProgram("bash")
            self.current_process.setArguments(["-c", command])
        self.current_process.start()
    def _handle_stdout(self):
        """处理标准输出"""
        raw_data = self.current_process.readAllStandardOutput().data()
        signal_bus.output_received.emit(decode(raw_data), "output")

    def _handle_stderr(self):
        """处理标准错误输出"""
        raw_data = self.current_process.readAllStandardError().data()
        signal_bus.output_received.emit(decode(raw_data), "error")
    def _handle_process_finished(self):
        """命令执行完成处理"""
        signal_bus.output_received.emit(f"\n[进程结束，退出码 {self.current_process.exitCode()}]", "system")
        self.current_process = None
    def stop_current_process(self):
        """终止当前运行的进程"""
        if self.current_process and self.current_process.state() == QProcess.Running:
            self.current_process.kill()
            signal_bus.output_received.emit("进程已被强制终止", "error")
