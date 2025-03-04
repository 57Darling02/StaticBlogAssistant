from PySide6.QtCore import QObject, Signal
class SignalBus(QObject):
    """
    全局信号总线（单例模式）
    """
    _instance = None

    settings_changed = Signal() # 配置变更触发
    message_sent = Signal(str)
    status_updated = Signal(str)
    execute_command = Signal(str)
    output_received = Signal(str, str)  # (text, type)
    process_finished = Signal(int)  # exit_code
    stop_command = Signal()




    def __new__(cls):
        if not isinstance(cls._instance, cls):
            cls._instance = super().__new__(cls)
        return cls._instance
    @classmethod
    def get_instance(cls):
        """静态方法获取单例实例"""
        if not cls._instance:
            cls._instance = cls()
        return cls._instance