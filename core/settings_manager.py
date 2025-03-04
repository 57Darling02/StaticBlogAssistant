# settings_manager.py
from PySide6.QtCore import QSettings, QObject
import os
import base64
organization = "57Darling02"
application = "StaticBlogAssistant"
from .signal_bus import SignalBus
signal_bus = SignalBus()

default_default_content = """---
title: $TITLE$
date: $TIME$
---
# 欢迎使用StaticBlogAssistant！
StaticBlogAssistant是一个静态博客辅助工具，能够自定义脚本并快捷执行。自定义编辑器如果有时间再做
$TITLE$将会替换成文件名
$TIME$将会替换成当前时间
"""

default_scripts_content = {
    "vitepress初始化项目": "npm init",
    "vitepress打包": "npm run docs:build",
    "vitepress本地预览": "npm run docs:dev",
    "vitepress调试": "npm run docs:dev",
    "github部署": "git add . && git commit -m \"update\" && git push",
    "Hexo初始化项目": "hexo init",
    "Hexo清理并生成": "hexo cl && hexo g",
    "Hexo本地预览": "hexo server",
    "Hexo部署到GitHub": "hexo deploy",
}

class SettingsManager(QObject):
    _instance = None
    @classmethod
    def get_instance(cls):
        """静态方法获取单例实例"""
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    def __init__(self):
        super().__init__()
        self.settings = QSettings(organization, application)
        self._blog_root = "D:/myCode/Vue/VitePress-js"
        self._editor_path = ""
        self._default_content = ""
        self._script_commands = {}
        self.load()
    def clear(self):
        self.settings.clear()
    @property
    def blog_root(self):
        return self._blog_root

    @blog_root.setter
    def blog_root(self, value):
        if os.path.exists(value):
            self._blog_root = value
        else:
            raise ValueError("Invalid blog root path.")

    @property
    def editor_path(self):
        return self._editor_path

    @editor_path.setter
    def editor_path(self, value):
        self._editor_path = value
    @property
    def default_content(self):
        return self._default_content

    @default_content.setter
    def default_content(self, value):
        self._default_content = value
    @property
    def script_commands(self):
        return self._script_commands.copy()
    @script_commands.setter
    def script_commands(self, value):
        self._script_commands = value

    def load(self):
        # 博客根目录
        blog_root = self.settings.value("blog_root_path", "")
        self._blog_root = blog_root if blog_root else "D:/myCode/Vue/VitePress-js"

        # 编辑器路径
        self._editor_path = self.settings.value("editor_path", "")

        # 默认内容（Base64解码）
        encoded_content = self.settings.value("default_content", "")
        self._default_content = base64.b64decode(encoded_content).decode("utf-8") if encoded_content else default_default_content

        # 脚本命令
        self._script_commands = self.settings.value("script_commands", default_scripts_content)

    def save(self):
        self.settings.setValue("blog_root_path", self._blog_root)
        self.settings.setValue("editor_path", self._editor_path)
        self.settings.setValue("default_content",
                               base64.b64encode(self._default_content.encode("utf-8")).decode())
        self.settings.setValue("script_commands", self._script_commands)
        signal_bus.settings_changed.emit()

    def update_script_command(self, name, command):
        self._script_commands[name] = command

    def remove_script_command(self, name):
        if name in self._script_commands:
            del self._script_commands[name]