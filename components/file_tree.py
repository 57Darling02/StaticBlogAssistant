import os
import subprocess
import re
import shutil
from datetime import datetime

from PySide6.QtCore import QDir, QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QTreeView, QFileSystemModel, QMenu, QMessageBox, QApplication

from core.utils import lord_model
from core import MarkdownFilterProxy, SettingsManager, SignalBus

signal_bus = SignalBus.get_instance()
settings_manager = SettingsManager.get_instance()



class FileTreeWidget(QTreeView):
    def __init__(self):
        super().__init__()
        self.settings = SettingsManager.get_instance()
        """初始化文件树模型"""
        self.source_model = QFileSystemModel()
        self.source_model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot | QDir.Hidden)

        self.proxy_model = MarkdownFilterProxy(self.settings.blog_root)
        self.proxy_model.setSourceModel(self.source_model)

        self.setModel(self.proxy_model)
        self.source_model.setRootPath(self.settings.blog_root)

        # 初始加载根路径
        self.source_model.directoryLoaded.connect(self._update_root_index)
        signal_bus.settings_changed.connect(self._update_root_index)
        # 隐藏其他列并设置宽度
        for column in range(1, 4):
            self.setColumnHidden(column, True)
        self.setColumnWidth(0, 180)

        #设置自定义菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # 加载响应事件
        # 双击
        self.doubleClicked.connect(self._handle_double_click)
        # 右键
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _update_root_index(self):
        """更新根目录索引"""
        self.proxy_model = MarkdownFilterProxy(self.settings.blog_root)
        self.proxy_model.setSourceModel(self.source_model)
        self.setModel(self.proxy_model)
        root_index = self.source_model.index(self.settings.blog_root)
        self.setRootIndex(self.proxy_model.mapFromSource(root_index))
        self.source_model.setRootPath(self.settings.blog_root)

    """                  处理事件逻辑                    """
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        proxy_index = self.indexAt(pos)
        if not proxy_index.isValid():
            return
        # 转换索引并获取路径
        source_index = self.proxy_model.mapToSource(proxy_index)
        self._current_context_path = self.source_model.filePath(source_index)
        # 创建菜单
        menu = QMenu()

        add_page = menu.addAction("🖊 新增文章")
        add_page.triggered.connect(self._add_page)

        # 打开所在文件夹
        open_folder_action = menu.addAction("📂 在资源管理器中显示")
        open_folder_action.triggered.connect(self._reveal_in_explorer)

        # 删除操作
        delete_action = menu.addAction("🗑️ 删除")
        delete_action.triggered.connect(self._delete_selected_item)

        # 扩展：可添加更多操作
        copy_path_action = menu.addAction("📋 复制路径")
        copy_path_action.triggered.connect(self._copy_path_to_clipboard)
        copy_path_action = menu.addAction("🔄 刷新")
        copy_path_action.triggered.connect(self._update_root_index)
        menu.exec(self.viewport().mapToGlobal(pos))

    def _reveal_in_explorer(self):
        """在文件资源管理器中显示"""
        if hasattr(self, "_current_context_path"):
            QDesktopServices.openUrl(QUrl.fromLocalFile(
                os.path.dirname(self._current_context_path)
            ))

    def _handle_double_click(self, proxy_index):
        """双击打开文件或文件夹"""

        source_index = self.proxy_model.mapToSource(proxy_index)
        path = self.source_model.filePath(source_index)
        self.open_in_editor(path)

    def open_in_editor(self, path):
        if os.path.isfile(path):
            if os.path.exists(settings_manager.editor_path):
                subprocess.Popen([settings_manager.editor_path, path])
            else:
                # 未配置编辑器时使用系统默认方式
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
                signal_bus.output_received.emit("未配置编辑器，使用系统默认程序打开", "warning")

    def _add_page(self):
        """在选中目录创建新文章"""
        if hasattr(self, "_current_context_path"):
            target_dir = os.path.dirname(self._current_context_path) \
                if os.path.isfile(self._current_context_path) \
                else self._current_context_path
            # 弹出输入对话框
            from PySide6.QtWidgets import QInputDialog
            title, ok = QInputDialog.getText(
                self,
                "新建文章",
                "请输入文章标题：",
                text="未命名文章"
            )

            if not ok:
                return  # 用户取消输入

            # 生成安全文件名

            safe_name = re.sub(r'[\\/*?:"<>|]', "", title.strip())  # 去除非法字符
            if not safe_name:
                safe_name = datetime.now().strftime("新建文章-%Y%m%d%H%M.md")

            counter = 1
            base_name = safe_name
            while os.path.exists(os.path.join(target_dir, f"{safe_name}.md")):
                safe_name = f"{base_name}-{counter}"
                counter += 1

            full_path = os.path.join(target_dir, f"{safe_name}.md")

            # 创建文件并写入初始内容
            with open(full_path, 'w', encoding='utf-8') as f:
                content = lord_model(title,settings_manager.default_content)
                print(content)
                f.write(content)

            # 刷新文件树
            self.source_model.setRootPath(self.settings.blog_root)
            signal_bus.output_received.emit(f"已创建新文章：{full_path}", "system")
            self.open_in_editor(full_path)


    def _copy_path_to_clipboard(self):
        """复制完整路径到剪贴板"""
        if hasattr(self, "_current_context_path"):
            QApplication.clipboard().setText(self._current_context_path)

    def _delete_selected_item(self):
        """删除选中项"""
        if not hasattr(self, "_current_context_path"):
            return

        path = self._current_context_path
        confirm = QMessageBox.question(
            self,
            "确认删除",
            f"确定要永久删除以下项目吗？\n{path}",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                # 删除目录或文件
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "删除失败",
                    f"无法删除：{str(e)}",
                    QMessageBox.Ok
                )

