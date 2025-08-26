import sys
import os
import json
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QMessageBox, QPushButton, QListWidget, QListWidgetItem, QInputDialog
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer, QSize

MAX_WIDTH = 200
MAX_HEIGHT = 200
TODO_FILE = "todo.json"

class Pet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 获取当前脚本所在目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # 图片列表（摇尾巴动画）
        self.images = [
            os.path.join(base_dir, "images", "normal.png"),
            os.path.join(base_dir, "images", "shake.png"),
            os.path.join(base_dir, "images", "happy.png")
        ]
        
        # 加载所有图片并缩放到最大尺寸
        self.pixmaps = []
        for path in self.images:
            pix = QPixmap(path)
            if pix.isNull():
                QMessageBox.critical(self, "错误", f"没有找到图片: {path}")
                sys.exit(1)
            # 限制大小，保持纵横比
            if pix.width() > MAX_WIDTH or pix.height() > MAX_HEIGHT:
                pix = pix.scaled(MAX_WIDTH, MAX_HEIGHT, 
                                 Qt.AspectRatioMode.KeepAspectRatio, 
                                 Qt.TransformationMode.SmoothTransformation)
            self.pixmaps.append(pix)

        self.current_index = 0
        self.label = QLabel(self)
        self.label.setPixmap(self.pixmaps[self.current_index])
        self.resize(self.pixmaps[0].width(), self.pixmaps[0].height() + 50)  # 给按钮留空间

        # 定时器：每 2 秒切换图片
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.timer.start(1500)
        self.showing_happy = False

        # 鼠标拖动变量
        self.old_pos = None
        # TodoNeko按钮
        self.todo_button = QPushButton("📝 TodoNeko", self)
        self.todo_button.setGeometry(0, self.pixmaps[0].height(), self.pixmaps[0].width(), 40)
        self.todo_button.clicked.connect(self.toggle_todo)

        # 待办事项窗口
        self.todo_window = None
        self.todo_items = []
        self.load_todo()

    # 摇尾巴
    def next_frame(self):
        if self.showing_happy:
            return
        self.current_index = 1 - self.current_index  # 0 ↔ 1
        self.label.setPixmap(self.pixmaps[self.current_index])
    
    # 鼠标拖动
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event):
        self.old_pos = None

     # 切换 Todo 窗口显示/隐藏
    def toggle_todo(self):
        if self.todo_window is None:
            self.create_todo_window()
            self.todo_window.show()
        else:
            if self.todo_window.isVisible():
                self.todo_window.hide()
            else:
                self.todo_window.show()


    # 创建 Todo 窗口
    def create_todo_window(self):
        self.todo_window = QWidget(flags=Qt.WindowType.Window)
        self.todo_window.setWindowTitle("TodoNeko List")
        self.todo_window.setGeometry(self.x() + self.width(), self.y(), 300, 400)
    
        # 点击 X 只隐藏窗口
        def on_close(event):
            event.ignore()
            self.todo_window.hide()
        self.todo_window.closeEvent = on_close


        self.list_widget = QListWidget(self.todo_window)
        self.list_widget.setGeometry(10, 10, 280, 300)
        self.list_widget.itemChanged.connect(self.todo_item_checked)

        # 加载已有待办事项
        for text, checked in self.todo_items:
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)

        # 添加按钮
        add_btn = QPushButton("添加", self.todo_window)
        add_btn.setGeometry(10, 320, 130, 40)
        add_btn.clicked.connect(self.add_todo_item)

        # 删除按钮
        del_btn = QPushButton("删除", self.todo_window)
        del_btn.setGeometry(160, 320, 130, 40)
        del_btn.clicked.connect(self.delete_todo_item)

        self.todo_window.show()

    # 添加待办事项
    def add_todo_item(self):
        text, ok = QInputDialog.getText(self, "添加待办事项", "请输入内容:")
        if ok and text.strip():
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)
            self.todo_items.append((text, False))
            self.save_todo()

    # 删除待办事项
    def delete_todo_item(self):
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            self.todo_items = [(t, c) for t, c in self.todo_items if t != item.text()]
            self.list_widget.takeItem(self.list_widget.row(item))
        self.save_todo()

    # 勾选事件
    def todo_item_checked(self, item):
        self.todo_items = []
        for index in range(self.list_widget.count()):
            it = self.list_widget.item(index)
            self.todo_items.append((it.text(), it.checkState() == Qt.CheckState.Checked))
        self.save_todo()

    # 保存/读取
    def save_todo(self):
        with open(TODO_FILE, "w", encoding="utf-8") as f:
            json.dump(self.todo_items, f, ensure_ascii=False)

    def load_todo(self):
        if os.path.exists(TODO_FILE):
            with open(TODO_FILE, "r", encoding="utf-8") as f:
                self.todo_items = json.load(f)
        else:
            self.todo_items = []

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = Pet()
    pet.show()
    sys.exit(app.exec())
