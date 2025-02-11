from PyQt5.QtCore import Qt, QRect, QEvent
from PyQt5.QtWidgets import QWidget, QApplication, QLineEdit, QScrollArea, QVBoxLayout, QLabel, QComboBox, QSystemTrayIcon, QMenu, QAction, QPushButton
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPixmap, QIntValidator, QIcon
from plyer import notification

from Worktime import WorktimeSection
from Breaktime import BreaktimeSection
from Breakinterval import BreakIntervalSection
from WristPosition import WristPositionSection
from ReminderSection import ReminderSection
from TimeInput import InputTime
from ReminderMessage import ReminderWidget
from Audio import Audio
from Camera import Camera
import sys


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.pushButton = QPushButton()
        self.pushButton.clicked.connect(lambda: self.show_hide())

        # Set up main window
        self.main_window()

        # Disable maximized window
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

        """
            Initializing camera styles
        """
        self.camera_label = QLabel(self)
        self.camera_label.setGeometry(self.width() - 425, 355, 400, 300)
        self.camera_label.setStyleSheet("background-color: #AAAE8E;")

        # Dropdown box for choosing camera 
        self.camera_selection = QComboBox(self)
        self.camera_selection.setStyleSheet("background-color: #f3f1ec; border-radius: 3px;")
        self.camera_selection.setGeometry(1000, 300, 175, 25)
        self.camera_selection.addItem("Choose a camera") 
        self.camera_selection.addItems(["Camera 1", "Camera 2", "Camera 3"])

        # Map the cameras to index 
        self.camera_map = {"Camera 1": 0, "Camera 2": 1, "Camera 3": 2}
        self.camera_selection.currentIndexChanged.connect(self.select_camera)

        # Calling the camera class 
        self.camera = Camera()
        self.camera.image_data.connect(self.update_camera_image)

        # Start camera
        self.camera.start()

        """
            Initializing time inputs for break time 
            and break interval 
        """
        # Time Input Class 
        self.break_handler = InputTime(self)
        self.timer = self.startTimer(1000)

        # Break Time Input
        self.user_input_break = QLineEdit(self)
        self.user_input_break.setGeometry(355, 195, 50, 30)
        self.user_input_break.setStyleSheet("background-color: #f3f1ec; border: none; color: #303030; font-size: 14px;")
        self.user_input_break.setValidator(QIntValidator())

        # Break Interval Input
        self.user_input_interval = QLineEdit(self)
        self.user_input_interval.setGeometry(565, 195, 50, 30)
        self.user_input_interval.setStyleSheet(
            "background-color: #f3f1ec; border: none; color: #303030; font-size: 14px;")
        self.user_input_interval.setValidator(QIntValidator())

        self.user_input_break.returnPressed.connect(self.validate_inputs)
        self.user_input_interval.returnPressed.connect(self.validate_inputs)

        self.break_time = 0
        self.break_interval = 0
        self.original_break_time = 0
        self.original_break_interval = 0
        self.total_break_interval = 0
        self.total_work_time = 0
        self.break_interval_active = False
        self.initial_run = True

        self.set_break_interval()
        self.start_timer()

        """ This section is for notification functionalities
            of the software 
        """

        # Store Notification message
        self.notification_message = ""
        self.notification_container = False
        self.notifications = []

        # Notification Scroll Area
        self.notification_scroll_area = QScrollArea(self)
        self.notification_scroll_area.setGeometry(325, 420, 390, 160)
        self.notification_scroll_area.setWidgetResizable(True)
        self.notification_scroll_area.setStyleSheet("background-color: white; border: black;")

        self.notification_container_widget = QWidget()
        self.notification_scroll_area.setWidget(self.notification_container_widget)

        self.notification_layout = QVBoxLayout(self.notification_container_widget)
        self.notification_layout.setAlignment(Qt.AlignTop)
        self.notification_layout.setSpacing(10)

        # Audio initialization 
        self.audio = Audio(self)
    
    """
        This function is responsible for showing and hiding 
        the window. This is is necessary because of the background 
        running feature of the software. 
    """
    def show_hide(self):
        if self.isVisible():
            action_show_hide.setText("Show Window")
            self.hide()
        else:
            action_show_hide.setText("Hide Window")
            self.showNormal()

    """
        This function is for the mainwindow 
    """

    def main_window(self):
        self.setWindowTitle("Don't Wrist It")
        self.setStyleSheet("background-color: #f3f1ec; border-radius: 20px;")
        self.setFixedSize(1200, 720)

    def paintEvent(self, event):
        painter = QPainter(self)

        # LEFT PANE
        pen = QPen(QColor("#e8e7e7"), 0)
        painter.setPen(pen)
        painter.setBrush(QColor("#e8e7e7"))
        painter.drawRect(0, 0, 80, self.height())

        # CAMERA PANE
        painter.setBrush(QColor("#828E82"))
        painter.drawRect(self.width() - 450, 0, 450, self.height())

        # Logo
        if not hasattr(self, 'logo_pixmap'):
            self.logo_pixmap = QPixmap("./images/logo.png")

        image_logo_x = self.width() - 450 + (450 - self.logo_pixmap.width()) // 2
        painter.drawPixmap(image_logo_x, -70, self.logo_pixmap)

        # --- Don't Wrist It Title---
        font_title = QFont()
        font_title.setPointSize(14)
        painter.setFont(font_title)
        painter.setPen(QColor("#303030"))
        painter.drawText(105, 38, 450, 270, Qt.AlignLeft, "DON'T WRIST IT")

        # Tagline
        font_title = QFont()
        font_title.setPointSize(9)
        painter.setFont(font_title)
        painter.setPen(QColor("#6A6969"))
        painter.drawText(105, 71, 450, 270, Qt.AlignLeft, "Prevent Carpal Tunnel Syndrome")

        # Text under the logo
        font_title2 = QFont()
        font_title2.setPointSize(13)
        painter.setFont(font_title2)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(self.width() - 450, 100, 450, 270, Qt.AlignCenter, "DON'T WRIST IT")

        # --- Worktime display section ---
        worktime_section = WorktimeSection(painter, self.width(), self.height())
        worktime_section.paint_worktime()

        # Display Total Work Time
        font_counter = QFont()
        font_counter.setPointSize(10)
        painter.setFont(font_counter)
        painter.setPen(QColor("#303030"))
        painter.drawText(140, 200, 150, 30, Qt.AlignLeft, "Total Work Time:")
        painter.drawText(180, 240, 150, 30, Qt.AlignLeft, f"{self.format_time(self.total_work_time)}")

        # --- Break time display section ---
        breaktime_section = BreaktimeSection(painter, self.width(), self.height())
        breaktime_section.paint_breaktime()

        # Display Break Time Counter
        font_counter = QFont()
        font_counter.setPointSize(10)
        painter.setFont(font_counter)
        painter.setPen(QColor("#303030"))
        painter.drawText(333, 240, 150, 30, Qt.AlignLeft, f"Time left: {self.format_time(self.break_time)}")

        # --- Break interval display section ---
        breakint_section = BreakIntervalSection(painter, self.width(), self.height())
        breakint_section.paint_break_interval()

        # Display Break Interval Counter
        font_counter.setPointSize(10)  # Set a smaller font size
        painter.setFont(font_counter)
        painter.setPen(QColor("#303030"))
        painter.drawText(545, 240, 150, 30, Qt.AlignLeft, f"Interval left: {self.format_time(self.break_interval)}")

        # --- Wrist Position ---
        wristposition_section = WristPositionSection(painter, self.width(), self.height())
        
        # Displaying correct and incorrect positions of the hands 
        hands_detected = self.camera.hands_detect 
        correct_position = self.camera.correct_position
        wristposition_section.paint_wristposition(hands_detected, correct_position)
        
        # --- Reminder Section ---
        reminder_section = ReminderSection(painter, self.width(), self.height())
        reminder_section.paint_reminder()

        # --- Camera Section ---
        font_desc = QFont()
        font_desc.setPointSize(10)
        painter.setFont(font_desc)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(self.width() - 430, 305, 450, self.height(), Qt.AlignLeft, "Setting-up your Camera")

        rect = QRect(self.width() - 430, 330, 410, 350)
        painter.setPen(QPen(QColor("#FFFFFF"), 1))
        painter.setBrush(QColor("#AAAE8E"))
        painter.drawRoundedRect(rect, 5, 5)

        # If the user is incorrect for 5 minutes, the holder will have different color 
        if not self.camera.audio_holder:
            self.audio.audio_container_correct(painter)
            self.audio.audio_holder(painter)
        else:
            self.audio.audio_container_incorrect(painter)
            self.audio.audio_holder(painter)

    """
        This function is responsible for break time and
        break interval counter, and total work time  
    """

    def timerEvent(self, event):
        if event.timerId() == self.timer:
            if self.break_interval_active:
                if self.break_interval > 0:
                    self.break_interval -= 1

                    if self.break_interval == 0:
                        self.break_interval_active = False
                        self.break_time = self.original_break_time
                        self.show_notification("Take a Break!", "Do Wrist Exercises!")

            else:
                if self.break_time > 0:
                    self.break_time -= 1

                    if self.break_time == 0:
                        self.break_interval_active = True
                        self.total_work_time += self.original_break_interval  # Add to total work time
                        self.break_interval = self.original_break_interval
                        self.show_notification("Break Time Over", "Back to work!")

        self.update()

    def closeEvent(self, event):
        #self.camera.stop()
        window.hide()
        action_show_hide.setText("Show Window")
        event.accept()

    def set_break_time(self):
        self.break_handler.set_break_time()

    def set_break_interval(self):
        self.break_handler.set_break_interval()

    def format_time(self, seconds):
        return self.break_handler.format_time(seconds)

    def validate_inputs(self):
        self.break_handler.validate_inputs()

    def start_timer(self):
        self.break_handler.start_timer()

    def show_notification(self, title, message):
        notification.notify(
            title=title,
            message=message,
            app_name="Don't Wrist It",
            timeout=10
        )

        self.notifications.append(message)
        self.notification_container = True
        self.update()

        notification_widget = ReminderWidget(message, font_height=10)
        self.notification_layout.addWidget(notification_widget)
        self.notification_container = True
        self.notification_scroll_area.verticalScrollBar().setValue(
            self.notification_scroll_area.verticalScrollBar().maximum()
        )

    def select_camera(self, index):
        if hasattr(self, 'camera'):
            self.camera.stop()

        # selecting the camera from the UI 
        selected_cam = self.camera_selection.currentText()
        index = self.camera_map.get(selected_cam, -1)
        if index != -1:
            self.camera = Camera(index)
            self.camera.image_data.connect(self.update_camera_image)
            self.camera.start()

    def update_camera_image(self, image):
        pixmap = QPixmap.fromImage(image)
        self.camera_label.setPixmap(pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio))

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.hide()
                event.ignore()
            else:
                self.show()
        super().changeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    #Setting System Tray Icon
    tray = QSystemTrayIcon(QIcon(u"./images/logo.png"))
    menu = QMenu()

    #Show and Hide Application
    action_show_hide = QAction("Hide Window")
    action_show_hide.triggered.connect(lambda: window.show_hide())
    menu.addAction(action_show_hide)

    #Full Exit
    Exit = QAction("Exit")
    Exit.triggered.connect(lambda: app.exit())
    menu.addAction(Exit)

    #Setting ToolTips, Context Menu & Show Tray Icon
    tray.setToolTip("Don't Wrist It")
    tray.setContextMenu(menu)
    tray.show()

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())