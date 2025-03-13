"""
此程序为DM_pickup.py文件的UI版
基本不会更新，记得改version
"""

import sys
import requests
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal, QThread

version = "v1.0（by Lqw 2025）"


class MonitorWorker(QObject):
    update_log = pyqtSignal(str)
    found_quota = pyqtSignal(str, int)
    error_occurred = pyqtSignal(str)

    def __init__(self, url_list, interval):
        super().__init__()
        self.url_list = url_list
        self.interval = interval
        self._is_running = True

    def request_info(self, share_parameter):
        headers = {
            'origin': 'https://apph5.5idream.net',
            'referer': 'https://apph5.5idream.net/share/activity?share=E3FC243F08B44E61AA7E6758487AF594',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        }
        data = {'share': share_parameter}
        response = requests.post(
            'https://apph5.5idream.net/apih5/share/content',
            headers=headers,
            data=data
        )
        return response.json()['data']['activity']

    def run(self):
        count = 0
        while self._is_running:
            try:
                for url in self.url_list:
                    if not self._is_running:
                        return

                    share_param = url.split('share=')[1]
                    activity = self.request_info(share_param)

                    name = activity['activityName']
                    joined = int(activity['joinNum'])
                    max_num = activity['joinmaxnum']

                    # 处理不限名额的情况
                    quota = "不限" if max_num == "不限" else int(max_num) - joined

                    if count % (60 // self.interval) == 0:
                        self.update_log.emit(f"[监控中]：{name} 当前{joined}/{max_num}")

                    if quota != "不限" and quota > 0:
                        self.found_quota.emit(name, quota)
                        return

                count += 1
                QThread.sleep(self.interval)

            except Exception as e:
                self.error_occurred.emit(f"错误: {str(e)}")
                QThread.sleep(5)

    def stop(self):
        self._is_running = False


class DreamSnifferUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupStyles()
        self.monitor_thread = None
        self.worker = None
        self.alarm_timer = QTimer()  # 报警定时器

    def initUI(self):
        self.setWindowTitle('到梦空间捡漏程序')
        self.setGeometry(300, 300, 800, 500)

        # 创建堆叠窗口
        self.stacked = QStackedWidget()
        self.page1 = QWidget()
        self.page2 = QWidget()

        self.setupPage1()
        self.setupPage2()

        self.stacked.addWidget(self.page1)
        self.stacked.addWidget(self.page2)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.stacked)
        self.setLayout(main_layout)

    def setupPage1(self):
        layout = QVBoxLayout()

        title = QLabel("到梦空间捡漏助手")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.input_box = QTextEdit()
        self.input_box.setAcceptRichText(False)
        self.input_box.setPlaceholderText("此程序通过持续监测“到梦空间”活动名额实现捡漏操作，有名额时将发声提示\n\n"
                                          "每行输入一个活动分享链接...,例如：\n"
                                          "https://apph5.5idream.net/share/activity?share=478A452384481DEDAA7E6758487AF594")
        layout.addWidget(self.input_box)

        time_layout = QHBoxLayout()
        time_label = QLabel("监测间隔:")
        self.time_spin = QSpinBox()
        self.time_spin.setRange(5, 60)
        self.time_spin.setSuffix(" 秒")
        self.time_spin.setValue(10)
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_spin)
        time_layout.addStretch()

        version_label = QLabel(version)
        version_label.setStyleSheet("""
        QLabel {
            color: #323232;
            padding: 10px;
            font-size: 12px;
            background: transparent;
            }
        """)
        time_layout.addWidget(version_label)

        self.start_btn = QPushButton("启动监控")
        self.start_btn.clicked.connect(self.start_monitoring)

        layout.addLayout(time_layout)
        layout.addWidget(self.start_btn)
        self.page1.setLayout(layout)

    def setupPage2(self):
        layout = QVBoxLayout()

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setPlaceholderText("监控日志将显示在这里...")

        self.stop_btn = QPushButton("停止监测")
        self.stop_btn.clicked.connect(self.stop_monitoring)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.stop_btn)

        layout.addWidget(self.output_box)
        layout.addLayout(btn_layout)
        self.page2.setLayout(layout)

    def setupStyles(self):
        self.setStyleSheet("""
            /* 保持原有样式 */
            QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a1a, stop:1 #4a4a4a); color: #fff; }
            QLabel { font: bold 20px; color: #00ff9d; padding: 10px; }
            QTextEdit, QSpinBox { 
                background: rgba(255,255,255,0.1); 
                border: 2px solid #00ff9d;
                border-radius: 8px; 
                padding: 10px;
                font-size: 14px; 
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00ff9d, stop:1 #00cc7a);
                border: none;
                border-radius: 15px;
                color: #1a1a1a;
                padding: 12px 24px;
                font: bold 14px;
                min-width: 120px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00cc7a, stop:1 #00ff9d); }
        """)

    def start_monitoring(self):
        urls = self.input_box.toPlainText().strip().split('\n')
        if not urls:
            QMessageBox.warning(self, "警告", "请输入至少一个活动链接！")
            return

        self.stacked.setCurrentIndex(1)
        self.output_box.clear()

        # 创建监控线程
        self.monitor_thread = QThread()
        self.worker = MonitorWorker(
            url_list=urls,
            interval=self.time_spin.value()
        )
        self.worker.moveToThread(self.monitor_thread)

        # 连接信号
        self.worker.update_log.connect(self.append_log)
        self.worker.found_quota.connect(self.on_quota_found)
        self.worker.error_occurred.connect(self.append_log)
        self.monitor_thread.started.connect(self.worker.run)
        self.monitor_thread.finished.connect(self.monitor_thread.deleteLater)

        self.monitor_thread.start()
        self.append_log("开始监测...")

    def stop_monitoring(self):
        self.alarm_timer.stop()
        if self.worker:
            self.worker.stop()
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.quit()
            self.monitor_thread.wait()
        self.stacked.setCurrentIndex(0)
        self.append_log("监测已停止")

    def append_log(self, text):
        self.output_box.append(f"▶ {text}")
        self.output_box.verticalScrollBar().setValue(
            self.output_box.verticalScrollBar().maximum()
        )

    def on_quota_found(self, name, quota):
        self.append_log(f"⚠️ 检测到名额！{name} 剩余 {quota} 个位置")
        # 添加报警逻辑（如系统通知音）
        self.alarm_timer.timeout.connect(QApplication.beep)
        self.alarm_timer.start(3000)  # 每隔3秒发出一次响声


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DreamSnifferUI()
    window.show()
    sys.exit(app.exec_())
