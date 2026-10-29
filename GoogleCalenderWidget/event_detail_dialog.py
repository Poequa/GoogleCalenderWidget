"""
일정 상세 보기 다이얼로그
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QFrame, QMessageBox, QGridLayout)
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QRegion, QPainterPath
from datetime import datetime
import config
import theme


class EventDetailDialog(QDialog):
    def __init__(self, event_data, calendar_api, parent=None):
        super().__init__(parent)
        self.event_data = event_data
        self.calendar_api = calendar_api
        self.action = None  # 'edit', 'delete', None
        
        # 현재 테마 가져오기
        self.theme = theme.get_current_theme()
        
        # 타이틀바 제거 (프레임리스 윈도우)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setMinimumWidth(450)
        
        # 설정된 투명도 적용
        current_opacity = config.settings.get('widget_opacity', 0.9)
        target_opacity = 1.0 if current_opacity >= 1.0 else 0.95
        self.setWindowOpacity(0.0)
        
        # 등장 애니메이션
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(target_opacity)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()
        
        # 드래그 위한 변수
        self.dragging = False
        self.drag_position = None
        
        # 테마에 따른 스타일 설정
        t = self.theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {t['card_background']};
                border-radius: 8px;
            }}
            QLabel {{
                color: {t['text_primary']};
            }}
        """)
        
        self.init_ui()
        
        # 둥근 모서리 적용
        self.apply_rounded_corners()
    
    def apply_rounded_corners(self, radius=12):
        """둥근 모서리 적용"""
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(0, 0, rect.width(), rect.height(), radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
    
    def resizeEvent(self, event):
        """크기 변경 시 마스크 업데이트"""
        super().resizeEvent(event)
        self.apply_rounded_corners()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 상단 툴바 (구글 캘린더 스타일)
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # 본문 컨테이너
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 10, 30, 30)
        
        # 제목
        title_label = QLabel(self.event_data.get('summary', '(제목 없음)'))
        title_label.setFont(QFont("Malgun Gothic", 18, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.theme['text_primary']};")
        title_label.setWordWrap(True)
        content_layout.addWidget(title_label)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {self.theme['separator']}; border: none;")
        content_layout.addWidget(line)
        
        # 상세 정보 (그리드 레이아웃)
        info_layout = QGridLayout()
        info_layout.setSpacing(15)
        info_layout.setColumnStretch(1, 1)
        
        # 날짜/시간
        clock_icon = QLabel("🕒")
        clock_icon.setFont(QFont("Segoe UI Emoji", 14))
        clock_icon.setStyleSheet("background: transparent; font-family: 'Segoe UI Emoji';")
        info_layout.addWidget(clock_icon, 0, 0, Qt.AlignTop)
        
        datetime_text = self.format_datetime()
        datetime_label = QLabel(datetime_text)
        datetime_label.setFont(QFont("Malgun Gothic", 11))
        datetime_label.setStyleSheet(f"color: {self.theme['text_primary']};")
        datetime_label.setWordWrap(True)
        info_layout.addWidget(datetime_label, 0, 1)
        
        row = 1
        
        # 위치 (있을 경우)
        location = self.event_data.get('location', '')
        if location:
            location_icon = QLabel("📍")
            location_icon.setFont(QFont("Segoe UI Emoji", 14))
            location_icon.setStyleSheet("background: transparent; font-family: 'Segoe UI Emoji';")
            info_layout.addWidget(location_icon, row, 0, Qt.AlignTop)
            
            location_label = QLabel(location)
            location_label.setFont(QFont("Malgun Gothic", 11))
            location_label.setStyleSheet(f"color: {self.theme['text_primary']};")
            location_label.setWordWrap(True)
            info_layout.addWidget(location_label, row, 1)
            row += 1
        
        # 설명 (있을 경우)
        description = self.event_data.get('description', '')
        if description:
            desc_icon = QLabel("📝")
            desc_icon.setFont(QFont("Segoe UI Emoji", 14))
            desc_icon.setStyleSheet("background: transparent; font-family: 'Segoe UI Emoji';")
            info_layout.addWidget(desc_icon, row, 0, Qt.AlignTop)
            
            desc_label = QLabel(description)
            desc_label.setFont(QFont("Malgun Gothic", 11))
            desc_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label, row, 1)
        
        content_layout.addLayout(info_layout)
        content_layout.addStretch()
        
        layout.addLayout(content_layout)
        
        self.setLayout(layout)
    
    def create_toolbar(self):
        """상단 툴바 생성"""
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        
        t = self.theme
        # 배경색을 투명하게 하여 일체감 부여
        toolbar.setStyleSheet("background-color: transparent;")
        
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(15, 10, 15, 0)
        toolbar_layout.setSpacing(8)
        
        # 왼쪽 공간
        toolbar_layout.addStretch()
        
        # 버튼 공통 스타일
        btn_style = f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {t['elevated_background']};
            }}
        """
        
        # 수정 버튼
        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("수정")
        edit_btn.setFixedSize(36, 36)
        edit_btn.setFont(QFont("Segoe UI Emoji", 14))
        edit_btn.clicked.connect(self.edit_event)
        edit_btn.setStyleSheet(btn_style + "QPushButton { font-family: 'Segoe UI Emoji'; }")
        toolbar_layout.addWidget(edit_btn)
        
        # 삭제 버튼
        delete_btn = QPushButton("🗑️")
        delete_btn.setToolTip("삭제")
        delete_btn.setFixedSize(36, 36)
        delete_btn.setFont(QFont("Segoe UI Emoji", 14))
        delete_btn.clicked.connect(self.delete_event)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                padding: 4px;
                font-family: 'Segoe UI Emoji';
            }}
            QPushButton:hover {{
                background-color: #ffebee;
                color: #d32f2f;
            }}
        """)
        toolbar_layout.addWidget(delete_btn)
        
        # 닫기 버튼
        close_btn = QPushButton("✕")
        close_btn.setToolTip("닫기")
        close_btn.setFixedSize(36, 36)
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 18px;
                font-size: 16px;
                font-weight: bold;
                color: {t['text_secondary']};
            }}
            QPushButton:hover {{
                background-color: {t['separator']};
                color: {t['text_primary']};
            }}
        """)
        toolbar_layout.addWidget(close_btn)
        
        toolbar.setLayout(toolbar_layout)
        return toolbar
    
    def format_datetime(self):
        """날짜/시간 포맷팅"""
        start_str = self.event_data.get('start', '')
        end_str = self.event_data.get('end', '')
        
        try:
            if 'T' in start_str:
                # 시간 지정 일정
                start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                
                # 같은 날인지 확인
                if start_dt.date() == end_dt.date():
                    return f"{start_dt.strftime('%Y년 %m월 %d일 (%a)')} · {start_dt.strftime('%p %I:%M')} - {end_dt.strftime('%p %I:%M')}"
                else:
                    return f"{start_dt.strftime('%Y년 %m월 %d일 %p %I:%M')} - {end_dt.strftime('%m월 %d일 %p %I:%M')}"
            else:
                # 종일 일정
                start_dt = datetime.fromisoformat(start_str)
                end_dt = datetime.fromisoformat(end_str)
                
                # 하루 일정인지 여러 날인지
                if start_dt.date() == end_dt.date():
                    return f"{start_dt.strftime('%Y년 %m월 %d일 (%a)')} · 종일"
                else:
                    return f"{start_dt.strftime('%Y년 %m월 %d일')} - {end_dt.strftime('%m월 %d일')} · 종일"
        except Exception as e:
            print(f"날짜 포맷 오류: {e}")
            return f"{start_str} - {end_str}"
    
    def edit_event(self):
        """일정 수정"""
        self.action = 'edit'
        self.accept()
    
    def delete_event(self):
        """일정 삭제"""
        # 확인 대화상자
        msg = QMessageBox(self)
        msg.setWindowTitle("일정 삭제")
        msg.setText("정말로 이 일정을 삭제하시겠습니까?")
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        self.apply_message_box_style(msg)
        
        reply = msg.exec_()
        
        if reply == QMessageBox.Yes:
            event_id = self.event_data.get('id')
            if event_id:
                success = self.calendar_api.delete_event(event_id)
                if success:
                    self.action = 'delete'
                    self.accept()
                else:
                    error_msg = QMessageBox(self)
                    error_msg.setWindowTitle("오류")
                    error_msg.setText("일정 삭제에 실패했습니다.")
                    error_msg.setIcon(QMessageBox.Critical)
                    self.apply_message_box_style(error_msg)
                    error_msg.exec_()

    def apply_message_box_style(self, msg):
        """메시지 박스 스타일 적용"""
        msg.setWindowFlags(msg.windowFlags() | Qt.FramelessWindowHint)
        msg.setFont(QFont("Malgun Gothic", 10))
        
        # 투명도 설정
        current_opacity = config.settings.get('widget_opacity', 0.9)
        target_opacity = 1.0 if current_opacity >= 1.0 else 0.95
        msg.setWindowOpacity(0.0)
        
        t = self.theme
        
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
        
        # 버튼 스타일 강제 적용
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
        
        # 둥근 모서리 마스킹
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
    
    def accept(self):
        """확인 (저장) 시 애니메이션 후 닫기"""
        self.animate_close(lambda: self.done(QDialog.Accepted))

    def reject(self):
        """취소 (닫기) 시 애니메이션 후 닫기"""
        self.animate_close(lambda: self.done(QDialog.Rejected))

    def animate_close(self, callback):
        """닫기 애니메이션"""
        self.anim_close = QPropertyAnimation(self, b"windowOpacity")
        self.anim_close.setDuration(200)
        self.anim_close.setStartValue(self.windowOpacity())
        self.anim_close.setEndValue(0.0)
        self.anim_close.setEasingCurve(QEasingCurve.InCubic)
        self.anim_close.finished.connect(callback)
        self.anim_close.start()
    
    def mousePressEvent(self, event):
        """마우스 클릭 시 드래그 시작"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """마우스 이동 시 윈도우 이동"""
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """마우스 떼 때 드래그 종료"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
