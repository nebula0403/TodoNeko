import os
import json
import sys
from pathlib import Path

# 获取当前脚本所在目录
BASE_DIR = Path(__file__).resolve().parent

# 兼容导入PySide6
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                  QLabel, QLineEdit, QPushButton, QComboBox, QListWidget,
                                  QListWidgetItem, QCheckBox, QToolButton, QStatusBar, QMessageBox)
from PySide6.QtGui import QPixmap, QPainter, QPalette, QColor

# 启用高DPI支持
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# 表情文件路径配置
EMOTION_FILES = {
    "normal": str(BASE_DIR / "assets" / "pet" / "normal.png"),
    "happy": str(BASE_DIR / "assets" / "pet" / "happy.png"),
    "curious": str(BASE_DIR / "assets" / "pet" / "curious.png"),
    "blink": str(BASE_DIR / "assets" / "pet" / "wink.png"),
}


# 默认模板
DEFAULT_TEMPLATES = ["喝水", "休息眼睛", "站起来活动一下", "查看日程"]

class PetWidget(QLabel):
    """宠物表情显示组件"""
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setScaledContents(False)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setToolTip("点击或按空格键切换表情")
        
        # 表情图片缓存
        self.pixmap_cache = {}
        self.current_emotion = "normal"
        self.previous_emotion = "normal"
        
        # 加载所有表情图片
        self.load_all_emotions()
        
        # 设置默认表情
        self.setEmotion("normal")
    
    def load_all_emotions(self):
        """预加载所有表情图片"""
        for emotion, path in EMOTION_FILES.items():
            pixmap = QPixmap()
            if pixmap.load(path):
                self.pixmap_cache[emotion] = pixmap
            else:
                print(f"警告: 无法加载表情图片: {path}")
        
        # 确保至少有一个默认表情
        if "normal" not in self.pixmap_cache:
            # 创建默认的占位图
            self.pixmap_cache["normal"] = self.create_placeholder_pixmap()
    
    def create_placeholder_pixmap(self):
        """创建占位图片"""
        pixmap = QPixmap(200, 200)
        pixmap.fill(Qt.lightGray)
        painter = QPainter(pixmap)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "表情图片\n未找到")
        painter.end()
        return pixmap
    
    def setEmotion(self, emotion_name):
        """设置当前表情"""
        if emotion_name in self.pixmap_cache:
            self.current_emotion = emotion_name
            self.updatePixmap()
            return True
        elif emotion_name == "normal" and "normal" not in self.pixmap_cache:
            self.current_emotion = "normal"
            self.pixmap_cache["normal"] = self.create_placeholder_pixmap()
            self.updatePixmap()
            return True
        return False
    
    def getEmotion(self):
        """获取当前表情"""
        return self.current_emotion
    
    def setHappyTemporarily(self, duration_ms=1500):
        """临时设置为开心表情，然后恢复"""
        self.previous_emotion = self.current_emotion
        self.setEmotion("happy")
        
        # 设置定时器恢复之前的状态
        QtCore.QTimer.singleShot(duration_ms, self.restorePreviousEmotion)
    
    def restorePreviousEmotion(self):
        """恢复之前的状态，除非中途被手动切换"""
        if self.current_emotion == "happy":
            self.setEmotion(self.previous_emotion)
    
    def updatePixmap(self):
        """更新显示的图片"""
        if self.current_emotion in self.pixmap_cache:
            pixmap = self.pixmap_cache[self.current_emotion]
            if not pixmap.isNull():
                # 缩放图片以适应标签大小，保持宽高比
                scaled_pixmap = pixmap.scaled(
                    self.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.setPixmap(scaled_pixmap)
    
    def resizeEvent(self, event):
        """重写resize事件，调整图片大小"""
        super().resizeEvent(event)
        self.updatePixmap()
    
    def mousePressEvent(self, event):
        """点击事件 - 切换表情"""
        if event.button() == Qt.LeftButton:
            self.cycleEmotion()
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        """键盘事件 - 空格或回车切换表情"""
        if event.key() in (Qt.Key_Space, Qt.Key_Return):
            self.cycleEmotion()
            self.clicked.emit()
        super().keyPressEvent(event)
    
    def cycleEmotion(self):
        """循环切换表情"""
        emotions = list(EMOTION_FILES.keys())
        if not emotions:
            return
            
        current_index = emotions.index(self.current_emotion) if self.current_emotion in emotions else 0
        next_index = (current_index + 1) % len(emotions)
        self.setEmotion(emotions[next_index])

class TodoItemWidget(QWidget):
    """待办项自定义组件"""
    toggled = Signal(bool)
    deleted = Signal()
    
    def __init__(self, text, done=False, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # 复选框
        self.checkbox = QCheckBox(text)
        self.checkbox.setChecked(done)
        self.checkbox.stateChanged.connect(self.onStateChanged)
        self.updateTextStyle(done)
        layout.addWidget(self.checkbox)
        
        # 删除按钮
        self.delete_btn = QToolButton()
        self.delete_btn.setText("×")
        self.delete_btn.setToolTip("删除此项")
        self.delete_btn.clicked.connect(self.deleteItem)
        layout.addWidget(self.delete_btn)
        
        self.setLayout(layout)
    
    def onStateChanged(self, state):
        """复选框状态改变"""
        checked = state == Qt.Checked
        self.updateTextStyle(checked)
        self.toggled.emit(checked)
    
    def updateTextStyle(self, done):
        """更新文本样式"""
        font = self.checkbox.font()
        font.setStrikeOut(done)
        self.checkbox.setFont(font)
        
        palette = self.checkbox.palette()
        color = palette.color(QPalette.WindowText)
        color = QColor(color)
        color.setAlpha(128 if done else 255)
        palette.setColor(QPalette.WindowText, color)
        self.checkbox.setPalette(palette)
    
    def deleteItem(self):
        """删除此项"""
        self.deleted.emit()
    
    def text(self):
        """获取文本"""
        return self.checkbox.text()
    
    def isChecked(self):
        """是否已勾选"""
        return self.checkbox.isChecked()

class TodoListWidget(QListWidget):
    """待办列表组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
    
    def add_todo(self, title, done=False):
        """添加待办项"""
        # 检查是否已存在（忽略前后空格和大小写）
        cleaned_title = title.strip()
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget and widget.text().strip().lower() == cleaned_title.lower():
                return False  # 已存在
        
        # 创建新项
        item = QListWidgetItem(self)
        widget = TodoItemWidget(cleaned_title, done)
        
        # 连接信号
        widget.toggled.connect(lambda checked, i=item: self.onItemToggled(i, checked))
        widget.deleted.connect(lambda: self.remove_item(item))
        
        item.setSizeHint(widget.sizeHint())
        self.setItemWidget(item, widget)
        
        return True
    
    def remove_item(self, item):
        """删除项"""
        row = self.row(item)
        if row >= 0:
            self.takeItem(row)
    
    def onItemToggled(self, item, checked):
        """项状态改变"""
        # 可以在这里添加额外处理
        pass
    
    def get_all_todos(self):
        """获取所有待办项"""
        todos = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget:
                todos.append({
                    "title": widget.text(),
                    "done": widget.isChecked()
                })
        return todos
    
    def clear_all(self):
        """清空所有项"""
        self.clear()

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("桌面宠物待办事项")
        self.setMinimumSize(640, 420)
        self.resize(900, 600)
        
        # 数据文件路径
        self.data_dir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppDataLocation)
        if not self.data_dir:
            self.data_dir = os.path.expanduser("~/.DeskPetTodo")
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        self.data_file = os.path.join(self.data_dir, "data.json")
        
        # 初始化UI
        self.initUI()
        
        # 加载数据
        self.loadData()
    
    def initUI(self):
        """初始化用户界面"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧宠物区域
        self.pet_widget = PetWidget()
        main_layout.addWidget(self.pet_widget, 1)
        
        # 右侧待办区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        self.template_combo = QComboBox()
        self.template_combo.addItems(DEFAULT_TEMPLATES)
        self.template_combo.setToolTip("选择常用待办模板")
        input_layout.addWidget(self.template_combo)
        
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("输入新的待办事项...")
        self.input_line.returnPressed.connect(self.addTodo)
        input_layout.addWidget(self.input_line)
        
        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self.addTodo)
        input_layout.addWidget(self.add_btn)
        
        right_layout.addLayout(input_layout)
        
        # 待办列表
        self.todo_list = TodoListWidget()
        right_layout.addWidget(self.todo_list)
        
        main_layout.addWidget(right_widget, 2)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 连接信号
        self.pet_widget.clicked.connect(self.onPetClicked)
        self.template_combo.currentTextChanged.connect(self.onTemplateSelected)
    
    def onPetClicked(self):
        """宠物被点击"""
        self.status_bar.showMessage("宠物表情已切换", 2000)
    
    def onTemplateSelected(self, text):
        """模板被选择"""
        self.input_line.setText(text)
        self.input_line.setFocus()
    
    def addTodo(self):
        """添加待办项"""
        text = self.input_line.text().strip()
        if not text:
            self.status_bar.showMessage("待办内容不能为空", 3000)
            return
        
        if self.todo_list.add_todo(text):
            self.input_line.clear()
            self.status_bar.showMessage(f"已添加: {text}", 3000)
            self.saveData()
        else:
            self.status_bar.showMessage(f"待办已存在: {text}", 3000)
    
    def onItemToggled(self, item, checked):
        """待办项状态改变"""
        widget = self.todo_list.itemWidget(item)
        if widget and checked:
            self.pet_widget.setHappyTemporarily(1500)
            self.status_bar.showMessage("完成了一项任务!", 2000)
        
        self.saveData()
    
    def loadData(self):
        """加载数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 加载待办事项
                todos = data.get("todos", [])
                for todo in todos:
                    self.todo_list.add_todo(todo["title"], todo["done"])
                
                # 加载上次的表情
                last_emotion = data.get("lastEmotion", "normal")
                self.pet_widget.setEmotion(last_emotion)
                
                self.status_bar.showMessage(f"已加载 {len(todos)} 个待办事项", 3000)
            else:
                self.status_bar.showMessage("欢迎使用桌面宠物待办事项工具", 3000)
        except Exception as e:
            self.status_bar.showMessage(f"加载数据时出错: {str(e)}", 5000)
            print(f"加载错误: {e}")
    
    def saveData(self):
        """保存数据"""
        try:
            data = {
                "todos": self.todo_list.get_all_todos(),
                "lastEmotion": self.pet_widget.getEmotion()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.status_bar.showMessage(f"保存数据时出错: {str(e)}", 5000)
            print(f"保存错误: {e}")
    
    def closeEvent(self, event):
        """关闭事件 - 保存数据"""
        self.saveData()
        event.accept()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("桌面宠物待办事项")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("个人使用")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()