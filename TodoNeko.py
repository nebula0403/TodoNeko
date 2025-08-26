import sys
import os  # 新加
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QMessageBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class Pet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 获取当前脚本所在目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(base_dir, "images", "normal.png")

        # 尝试加载图片
        self.pix_normal = QPixmap(image_path)

        # 检查图片是否加载成功
        if self.pix_normal.isNull():
            QMessageBox.critical(self, "错误", f"没有找到图片: {image_path}")
            sys.exit(1)  # 退出程序

        # 显示图片
        self.label = QLabel(self)
        self.label.setPixmap(self.pix_normal)
        self.resize(self.pix_normal.size())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = Pet()
    pet.show()
    sys.exit(app.exec())
