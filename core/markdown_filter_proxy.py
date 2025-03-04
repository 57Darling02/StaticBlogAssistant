# 文章过滤器,递归方式查询子目录中的.md文件
from PySide6.QtCore import QSortFilterProxyModel, Qt

# 可以在这里添加需要排除的目录以优化性能
exclude_dirs = {"__pycache__", ".vitepress", "node_modules", ".git", "docs", "public", ".vscode", "dist"}
class MarkdownFilterProxy(QSortFilterProxyModel):
    def __init__(self, root_path):
        super().__init__()
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.root_path = root_path
        self.exclude_dirs = exclude_dirs


    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)
        child_path = model.filePath(index).lower()

        child_name = model.fileName(index)
        print(child_path)
        # 如果是文件：直接判断是否为 .md
        if not model.isDir(index):
            return child_name.lower().endswith(".md")

        # 如果是目录：检查是否在排除列表及根路径范围内
        if child_name in self.exclude_dirs or not child_path.startswith(self.root_path.lower()):
            return False

        # 检查目录下是否包含 .md 文件
        return self.has_markdown_in_children(model, index)

    def has_markdown_in_children(self, model, index):
        """深度优先检查目录是否包含 .md 文件"""
        # 强制加载所有子项（解决延迟加载问题）
        if model.canFetchMore(index):
            model.fetchMore(index)

        # 检查当前目录的直属文件
        for i in range(model.rowCount(index)):
            child = model.index(i, 0, index)
            if not model.isDir(child) and child.data().lower().endswith(".md"):
                return True

        # 递归检查子目录（跳过排除项）
        for i in range(model.rowCount(index)):
            child = model.index(i, 0, index)
            child_name = model.fileName(child)
            if model.isDir(child) and child_name not in self.exclude_dirs:
                # 强制加载子目录内容
                if model.canFetchMore(child):
                    model.fetchMore(child)
                if self.has_markdown_in_children(model, child):
                    return True
        return False