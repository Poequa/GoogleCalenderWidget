"""
캘린더 위젯 메인 UI
"""
import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTabWidget, QMessageBox, QSystemTrayIcon,
                            QMenu, QAction, QApplication)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QPainter, QRegion, QPainterPath
import win32gui
import win32con
import config
import theme
from google_calendar_api import GoogleCalendarAPI
from list_view import ListView
from calendar_view import CalendarView
from settings_dialog import SettingsDialog


class CalendarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.calendar_api = GoogleCalendarAPI()
        self.dragging = False
        self.drag_position = QPoint()
        
        self.init_ui()
        self.setup_system_tray()  # 시스템 트레이 설정
        self.apply_settings()
        self.setup_desktop_widget()
        self.setup_timer()
        
        # 초기 데이터 로드
        self.refresh_current_view()
        
    def init_ui(self):
        """UI 초기화"""
        # 윈도우 설정
        self.setWindowTitle('Calendar Desktop Widget')
        self.resize_widget()
        
        # 투명도 및 프레임 제거
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnBottomHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 헤더
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)
        
        # 탭 위젯 (목록/달력 전환)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                background-color: #3a3a3a;
                color: white;
                padding: 8px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4285f4;
            }
            QTabBar::tab:hover {
                background-color: #357ae8;
            }
        """)
        
        # 달력 뷰 (먼저)
        self.calendar_view = CalendarView(self.calendar_api)
        self.tab_widget.addTab(self.calendar_view, "📅 달력")
        
        # 목록 뷰 (나중)
        self.list_view = ListView(self.calendar_api)
        self.tab_widget.addTab(self.list_view, "📋 목록")
        
        # 기본 뷰 설정
        default_view = config.settings.get('default_view', 'calendar')
        if default_view == 'calendar':
            self.tab_widget.setCurrentIndex(0)  # 달력 = 0
        else:
            self.tab_widget.setCurrentIndex(1)  # 목록 = 1
        
        main_layout.addWidget(self.tab_widget)
        
        self.setLayout(main_layout)
    
    def create_header(self):
        """헤더 생성"""
        header_layout = QVBoxLayout()
        
        # 상단 버튼들
        button_layout = QHBoxLayout()
        
        # 타이틀
        title_label = QLabel("📅 Calendar Widget")
        title_label.setFont(QFont("Malgun Gothic", 14, QFont.Bold))
        button_layout.addWidget(title_label)
        
        button_layout.addStretch()
        
        # 설정 버튼
        settings_btn = QPushButton("⚙️")
        settings_btn.setToolTip("설정")
        settings_btn.clicked.connect(self.open_settings)
        settings_btn.setMaximumWidth(35)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
                font-size: 14px;
                font-family: 'Segoe UI Emoji';
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        button_layout.addWidget(settings_btn)
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("새로고침")
        refresh_btn.clicked.connect(self.refresh_current_view)
        refresh_btn.setMaximumWidth(35)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
                font-size: 14px;
                font-family: 'Segoe UI Emoji';
            }
            QPushButton:hover {
                background-color: #357ae8;
            }
        """)
        button_layout.addWidget(refresh_btn)
        
        header_layout.addLayout(button_layout)
        
        return header_layout
    
    def create_tray_icon(self):
        """트레이 아이콘 생성 (텍스트 기반)"""
        # 32x32 픽셀 아이콘 생성
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 배경 원
        painter.setBrush(QColor("#4285f4"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        
        # 텍스트 (📅 이모지 대신 간단한 텍스트)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Malgun Gothic", 14, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "C")
        
        painter.end()
        
        return QIcon(pixmap)
    
    def setup_system_tray(self):
        """시스템 트레이 설정"""
        # 트레이 아이콘 생성
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.create_tray_icon())
        self.tray_icon.setToolTip("Calendar Widget")
        
        # 트레이 메뉴 생성
        tray_menu = QMenu(self)
        
        # 보이기/숨기기
        show_action = QAction("🔼 위젯 보이기", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("🔽 위젯 숨기기", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        # 새로고침
        refresh_action = QAction("🔄 새로고침", self)
        refresh_action.triggered.connect(self.refresh_current_view)
        tray_menu.addAction(refresh_action)
        
        # 설정
        settings_action = QAction("⚙️ 설정", self)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)
        
        tray_menu.addSeparator()
        
        # 종료
        quit_action = QAction("❌ 종료", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # 더블클릭으로 보이기/숨기기
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 트레이 아이콘 표시
        self.tray_icon.show()
        
        # 시작 시 알림
        self.tray_icon.showMessage(
            "Calendar Widget",
            "백그라운드에서 실행 중입니다.\n트레이 아이콘을 우클릭하여 메뉴를 여세요.",
            QSystemTrayIcon.Information,
            3000
        )
    
    def tray_icon_activated(self, reason):
        """트레이 아이콘 클릭 이벤트"""
        if reason == QSystemTrayIcon.DoubleClick:
            # 더블클릭: 보이기/숨기기 토글
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def quit_application(self):
        """프로그램 종료"""
        msg = QMessageBox(self)
        msg.setWindowTitle('종료 확인')
        msg.setText('Calendar Widget을 종료하시겠습니까?')
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.button(QMessageBox.Ok).setText("확인")
        msg.button(QMessageBox.Cancel).setText("취소")
        msg.setDefaultButton(QMessageBox.Cancel)
        
        # 통일된 스타일 적용
        self.apply_message_box_style(msg)
        
        reply = msg.exec_()
        
        if reply == QMessageBox.Ok:
            self.tray_icon.hide()
            QApplication.quit()
    
    def closeEvent(self, event):
        """창 닫기 이벤트 (X 버튼)"""
        # 창을 닫아도 트레이로 숨김 (종료하지 않음)
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Calendar Widget",
            "백그라운드에서 계속 실행 중입니다.\n종료하려면 트레이 메뉴에서 '종료'를 선택하세요.",
            QSystemTrayIcon.Information,
            2000
        )
    
    def resize_widget(self):
        """위젯 크기 조절"""
        width = config.settings.get('widget_width', 1000)
        height = config.settings.get('widget_height', 900)
        pos_x = config.settings.get('widget_position_x', 50)
        pos_y = config.settings.get('widget_position_y', 50)
        
        self.setGeometry(pos_x, pos_y, width, height)
    
    def apply_settings(self):
        """설정 적용"""
        # 투명도
        opacity = config.settings.get('widget_opacity', 0.9)
        self.setWindowOpacity(opacity)
        
        # 테마 색상
        colors = config.settings.get_theme_colors()
        
        # 배경색
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(colors['background']))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        # 텍스트 색상 전역 적용
        self.setStyleSheet(f"""
            QWidget {{
                color: {colors['text']};
            }}
            QLabel {{
                color: {colors['text']};
            }}
        """)
        
        # 트레이 메뉴 스타일 업데이트
        if hasattr(self, 'tray_icon') and self.tray_icon.contextMenu():
            t = theme.get_current_theme()
            self.tray_icon.contextMenu().setStyleSheet(f"""
                QMenu {{
                    background-color: {t['card_background']};
                    border: 1px solid {t['border']};
                    border-radius: 8px;
                    padding: 5px;
                }}
                QMenu::item {{
                    color: {t['text_primary']};
                    padding: 8px 20px;
                    border-radius: 4px;
                    font-family: 'Apple SD Gothic Neo', 'Malgun Gothic';
                    font-size: 10pt;
                }}
                QMenu::item:selected {{
                    background-color: {t['accent']};
                    color: white;
                }}
                QMenu::separator {{
                    height: 1px;
                    background: {t['separator']};
                    margin: 5px 10px;
                }}
            """)
    
    def open_settings(self):
        """설정 다이얼로그 열기"""
        dialog = SettingsDialog(self.calendar_api, self)
        if dialog.exec_():
            # 설정이 변경되었으면 자동 재시작
            self.restart_application()

    def restart_application(self):
        """프로그램 재시작"""
        # 트레이 아이콘 숨기기 (잔상 방지)
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        
        # 현재 프로세스를 새로운 프로세스로 교체
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    def refresh_current_view(self):
        """현재 탭의 뷰 새로고침"""
        current_index = self.tab_widget.currentIndex()
        if current_index == 0:  # 달력 뷰
            self.calendar_view.refresh()
        else:  # 목록 뷰
            self.list_view.load_events()
    
    def setup_desktop_widget(self):
        """바탕화면에 위젯 고정"""
        try:
            # 현재 윈도우 핸들
            hwnd = int(self.winId())
            
            # Progman 윈도우 찾기 (바탕화면)
            progman = win32gui.FindWindow("Progman", None)
            
            # WorkerW 생성 트리거
            win32gui.SendMessageTimeout(
                progman,
                0x052C,  # WM_SPAWN_WORKER
                0, 0,
                win32con.SMTO_NORMAL,
                1000
            )
            
            # WorkerW 찾기
            def enum_windows_callback(hwnd_enum, _):
                shell_dll = win32gui.FindWindowEx(hwnd_enum, 0, "SHELLDLL_DefView", None)
                if shell_dll:
                    worker = win32gui.FindWindowEx(0, hwnd_enum, "WorkerW", None)
                    if worker:
                        # 내 윈도우를 WorkerW의 자식으로 설정
                        win32gui.SetParent(hwnd, worker)
                        return False
                return True
            
            win32gui.EnumWindows(enum_windows_callback, None)
            
        except Exception as e:
            print(f"바탕화면 고정 실패: {e}")
            print("일반 창으로 표시됩니다.")
    
    def setup_timer(self):
        """자동 업데이트 타이머"""
        update_interval = config.settings.get('update_interval', 5)
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_current_view)
        self.timer.start(update_interval * 60 * 1000)  # 분 -> 밀리초
    
    def restart_timer(self):
        """타이머 재시작 (설정 변경 시)"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        self.setup_timer()
    
    def mousePressEvent(self, event):
        """마우스 클릭 - 드래그 시작"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        """마우스 이동 - 드래그"""
        if self.dragging:
            new_pos = event.globalPos() - self.drag_position
            self.move(new_pos)
            # 위치 저장
            config.settings.set('widget_position_x', new_pos.x())
            config.settings.set('widget_position_y', new_pos.y())
    
    def mouseReleaseEvent(self, event):
        """마우스 릴리즈 - 드래그 종료"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
    
    def resizeEvent(self, event):
        """창 크기 변경 시 둥근 모서리 적용"""
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        super().resizeEvent(event)

    def apply_message_box_style(self, msg):
        """메시지 박스에 통일된 스타일 적용 (테마에 따라)"""
        # 타이틀바 제거
        msg.setWindowFlags(msg.windowFlags() | Qt.FramelessWindowHint)
        msg.setFont(QFont("Malgun Gothic", 10))
        
        # 투명도 설정 (100%일 때만 불투명, 그 외엔 95%)
        current_opacity = config.settings.get('widget_opacity', 0.9)
        target_opacity = 1.0 if current_opacity >= 1.0 else 0.95
        msg.setWindowOpacity(0.0)
        
        t = theme.get_current_theme()
        
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {t['background']};
                border-radius: 16px;
                border: 1px solid {t['border']};
            }}
            QMessageBox QLabel {{
                color: {t['text_primary']};
                font-size: 11pt;
                padding: 20px;
                min-width: 320px;
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic';
            }}
            QMessageBox QPushButton {{
                background-color: {t['accent']};
                color: white;
                border: none;
                padding: 5px 12px;
                font-size: 9pt;
                font-weight: 600;
                min-width: 60px;
                min-height: 28px;
                border-radius: 5px;
                margin: 5px;
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic';
            }}
            QMessageBox QPushButton:hover {{
                background-color: {t['button_primary']};
            }}
        """)
        
        # 버튼 스타일 강제 적용 (일부 환경 호환성)
        for button in msg.buttons():
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t['accent']};
                    color: white;
                    border: none;
                    padding: 5px 12px;
                    font-size: 9pt;
                    font-weight: 600;
                    min-width: 60px;
                    min-height: 28px;
                    border-radius: 5px;
                    font-family: 'Apple SD Gothic Neo', 'Malgun Gothic';
                }}
                QPushButton:hover {{
                    background-color: {t['button_primary']};
                }}
            """)
        
        # 둥근 모서리 마스킹 (각진 배경 제거)
        original_resize = msg.resizeEvent
        def resize_event(event):
            path = QPainterPath()
            path.addRoundedRect(0, 0, msg.width(), msg.height(), 16, 16)
            region = QRegion(path.toFillPolygon().toPolygon())
            msg.setMask(region)
            original_resize(event)
        msg.resizeEvent = resize_event
        
        # 등장 애니메이션
        anim = QPropertyAnimation(msg, b"windowOpacity", msg)
        anim.setDuration(250)
        anim.setStartValue(0.0)
        anim.setEndValue(target_opacity)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        
        # 퇴장 애니메이션 (done 메서드 오버라이딩)
        original_done = msg.done
        def animate_close(r):
            anim_out = QPropertyAnimation(msg, b"windowOpacity", msg)
            anim_out.setDuration(200)
            anim_out.setStartValue(msg.windowOpacity())
            anim_out.setEndValue(0.0)
            anim_out.setEasingCurve(QEasingCurve.InCubic)
            anim_out.finished.connect(lambda: original_done(r))
            anim_out.start()
            msg.anim_out = anim_out
        msg.done = animate_close
