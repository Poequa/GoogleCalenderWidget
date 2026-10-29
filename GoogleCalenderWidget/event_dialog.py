"""
일정 추가/수정 다이얼로그
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QTextEdit, QPushButton, QDateTimeEdit, 
                            QCheckBox, QFormLayout, QMessageBox, QCalendarWidget, 
                            QComboBox, QWidget, QButtonGroup, QRadioButton, QColorDialog)
from PyQt5.QtCore import Qt, QDateTime, QRect, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QRegion, QPainterPath, QTextCharFormat, QColor, QPalette
from datetime import datetime, timedelta
import config
import theme


class EventDialog(QDialog):
    # 구글 캘린더 이벤트 색상 정의
    EVENT_COLORS = {
        "1": "#7986cb",  # 라벤더
        "2": "#33b679",  # 세이지
        "3": "#8e24aa",  # 포도
        "4": "#e67c73",  # 연분홍
        "5": "#f6bf26",  # 바나나
        "6": "#f4511e",  # 귤
        "7": "#039be5",  # 공작
        "8": "#616161",  # 흑연
        "9": "#3f51b5",  # 블루베리
        "10": "#0b8043", # 바질
        "11": "#d50000", # 토마토
    }

    # 구글 캘린더 색상 이름 정의
    EVENT_COLOR_NAMES = {
        "1": "라벤더",
        "2": "세이지",
        "3": "포도",
        "4": "연분홍",
        "5": "바나나",
        "6": "귤",
        "7": "공작",
        "8": "흑연",
        "9": "블루베리",
        "10": "바질",
        "11": "토마토",
    }

    def __init__(self, calendar_api, selected_date=None, event_data=None, parent=None):
        super().__init__(parent)
        self.calendar_api = calendar_api
        self.selected_date = selected_date  # datetime.date 객체
        self.event_data = event_data  # 기존 일정 수정 시
        self.event_id = event_data.get('id') if event_data else None
        self.custom_color_hex = None
        
        # 현재 테마 가져오기
        self.theme = theme.get_current_theme()
        
        # 타이틀바 제거 (프레임리스 윈도우)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setMinimumWidth(400)
        
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
        
        # 스타일 설정 - 테마 적용
        t = self.theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {t['card_background']};
                border-radius: 16px;
                border: 1px solid {t['border']};
            }}
            QLabel {{
                color: {t['text_primary']};
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic';
                font-size: 10pt;
            }}
            QLineEdit, QTextEdit, QDateTimeEdit {{
                background-color: {t['input_background']};
                color: {t['input_text']};
                border: 1px solid {t['input_border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic';
                font-size: 10pt;
            }}
            QLineEdit:focus, QTextEdit:focus, QDateTimeEdit:focus {{
                border: 2px solid {t['accent']};
                background-color: {t['elevated_background']};
            }}
            QLineEdit::placeholder, QTextEdit::placeholder {{
                color: {t['text_tertiary']};
            }}
            QCheckBox {{
                color: {t['text_primary']};
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic';
                font-size: 10pt;
                spacing: 8px;
            }}
            QComboBox {{
                background-color: {t['input_background']};
                color: {t['input_text']};
                border: 1px solid {t['input_border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic';
                font-size: 10pt;
            }}
            QComboBox:focus {{
                border: 2px solid {t['accent']};
                background-color: {t['elevated_background']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: none;
                background-color: transparent;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {t['text_secondary']};
                width: 0px;
                height: 0px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t['card_background']};
                color: {t['text_primary']};
                selection-background-color: {t['accent']};
                selection-color: white;
                border: 1px solid {t['border']};
                outline: none;
            }}
            QDateTimeEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: none;
                background-color: transparent;
            }}
            QDateTimeEdit::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {t['text_secondary']};
                width: 0px;
                height: 0px;
            }}
            
            /* 캘린더 위젯 스타일링 */
            QCalendarWidget QWidget {{
                background-color: {t['card_background']};
                color: {t['text_primary']};
                border: none;
            }}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {t['card_background']};
                border-bottom: 1px solid {t['border']};
            }}
            QCalendarWidget QToolButton {{
                color: {t['text_primary']};
                background-color: transparent;
                border: none;
                border-radius: 4px;
                icon-size: 18px;
                font-weight: bold;
                padding: 4px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: {t['elevated_background']};
            }}
            QCalendarWidget QToolButton::menu-indicator {{
                image: none;
            }}
            QCalendarWidget QAbstractItemView {{
                background-color: {t['input_background']};
                color: {t['text_primary']};
                selection-background-color: {t['accent']};
                selection-color: white;
                border: none;
                outline: none;
            }}
            
            /* 캘린더 헤더 (요일) */
            QCalendarWidget QHeaderView {{
                background-color: {t['card_background']};
            }}
            QCalendarWidget QHeaderView::section {{
                background-color: {t['card_background']};
                color: {t['text_primary']};
                border: none;
                font-weight: bold;
                padding: 5px;
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic';
            }}
            
            /* 캘린더 년도/월 스핀박스 */
            QCalendarWidget QSpinBox {{
                background-color: {t['input_background']};
                color: {t['text_primary']};
                border-radius: 4px;
                margin: 0px 2px;
            }}
            QCalendarWidget QSpinBox::up-button, QCalendarWidget QSpinBox::down-button {{
                width: 0px;
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
        t = self.theme
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # 제목
        title_label = QLabel("📅 일정 추가" if not self.event_data else "📅 일정 수정")
        title_label.setFont(QFont("Malgun Gothic", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {t['text_primary']}; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 폼
        form = QFormLayout()
        form.setSpacing(10)
        
        # 제목 입력
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("일정 제목을 입력하세요")
        form.addRow("제목:", self.title_input)
        
        # 종일 체크박스
        self.all_day_checkbox = QCheckBox("종일")
        self.all_day_checkbox.stateChanged.connect(self.toggle_time_edit)
        form.addRow("", self.all_day_checkbox)
        
        # 시작 날짜/시간 (분리)
        start_container = QWidget()
        start_layout = QHBoxLayout(start_container)
        start_layout.setContentsMargins(0, 0, 0, 0)
        start_layout.setSpacing(10)
        
        self.start_date = QDateTimeEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.style_calendar_popup(self.start_date)
        
        self.start_time = QComboBox()
        self.start_time.setEditable(True)
        self.populate_times(self.start_time)
        
        # 기본값: 선택된 날짜 또는 오늘
        if self.selected_date:
            start_dt = QDateTime(self.selected_date.year, self.selected_date.month, 
                               self.selected_date.day, 9, 0)  # 오전 9시
        else:
            start_dt = QDateTime.currentDateTime()
        self.start_date.setDateTime(start_dt)
        self.start_time.setCurrentText(start_dt.toString("HH:mm"))
        
        start_layout.addWidget(self.start_date, 2)
        start_layout.addWidget(self.start_time, 1)
        form.addRow("시작:", start_container)
        
        # 종료 날짜/시간 (분리)
        end_container = QWidget()
        end_layout = QHBoxLayout(end_container)
        end_layout.setContentsMargins(0, 0, 0, 0)
        end_layout.setSpacing(10)
        
        self.end_date = QDateTimeEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.style_calendar_popup(self.end_date)
        
        self.end_time = QComboBox()
        self.end_time.setEditable(True)
        self.populate_times(self.end_time)
        
        # 기본값: 시작 + 1시간
        end_dt = start_dt.addSecs(3600)
        self.end_date.setDateTime(end_dt)
        self.end_time.setCurrentText(end_dt.toString("HH:mm"))
        
        end_layout.addWidget(self.end_date, 2)
        end_layout.addWidget(self.end_time, 1)
        form.addRow("종료:", end_container)
        
        # 설명 입력
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("설명 (선택사항)")
        self.description_input.setMaximumHeight(80)
        form.addRow("설명:", self.description_input)
        
        # 위치 입력
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("위치 (선택사항)")
        form.addRow("위치:", self.location_input)
        
        # 색상 팔레트 추가
        self.color_group = QButtonGroup(self)
        color_layout = QHBoxLayout()
        color_layout.setSpacing(8)
        color_layout.setContentsMargins(0, 5, 0, 5)
        color_layout.setAlignment(Qt.AlignLeft)

        # 0. 기본 색상 (캘린더 색상) 추가
        # 현재 캘린더 ID 확인
        current_cal_id = 'primary'
        if self.event_data:
            current_cal_id = self.event_data.get('calendar_id', 'primary')
            # 이메일 형식이면 primary일 수 있음 (간소화)
        
        default_color = self.calendar_api.get_calendar_color(current_cal_id)
        
        default_btn = QRadioButton()
        default_btn.setFixedSize(24, 24)
        default_btn.setCursor(Qt.PointingHandCursor)
        default_btn.setToolTip("기본 색상")
        
        # 기본 색상 버튼 스타일 (X 표시 또는 빗금 등으로 기본값임을 표현하면 좋지만, 여기선 색상으로 표현)
        default_btn.setStyleSheet(f"""
            QRadioButton {{
                background-color: {default_color};
                border-radius: 12px;
                border: 2px solid {t['card_background']};
                outline: 1px solid {t['text_tertiary']};
            }}
            QRadioButton::indicator {{ width: 0px; height: 0px; }}
            QRadioButton:checked {{
                border: 2px solid {t['card_background']};
                outline: 2px solid {t['accent']};
                background-color: {default_color};
            }}
            QRadioButton:hover {{
                outline: 2px solid {t['text_secondary']};
            }}
        """)
        
        # ID 0은 '기본'으로 사용
        self.color_group.addButton(default_btn, 0)
        color_layout.addWidget(default_btn)

        # 색상 버튼 생성 (ID 순서대로 정렬)
        sorted_colors = sorted(self.EVENT_COLORS.items(), key=lambda x: int(x[0]))
        
        for cid, hex_code in sorted_colors:
            btn = QRadioButton()
            btn.setFixedSize(24, 24)
            btn.setCursor(Qt.PointingHandCursor)
            # 색상 이름 툴팁 설정
            btn.setToolTip(self.EVENT_COLOR_NAMES.get(cid, f"색상 {cid}"))
            
            # 스타일시트로 원형 버튼 만들기
            btn.setStyleSheet(f"""
                QRadioButton {{
                    background-color: {hex_code};
                    border-radius: 12px;
                    border: 2px solid transparent;
                }}
                QRadioButton::indicator {{
                    width: 0px;
                    height: 0px;
                }}
                QRadioButton:checked {{
                    border: 2px solid {t['text_primary']};
                    background-color: {hex_code};
                }}
                QRadioButton:hover {{
                    border: 2px solid {t['text_secondary']};
                }}
            """)
            
            self.color_group.addButton(btn, int(cid))
            color_layout.addWidget(btn)
            
        # 사용자 지정 색상 라디오 버튼 (ID: 99)
        self.custom_radio = QRadioButton()
        self.custom_radio.setFixedSize(24, 24)
        self.custom_radio.setCursor(Qt.PointingHandCursor)
        self.custom_radio.setToolTip("사용자 지정 색상")
        self.custom_radio.setVisible(False) # 처음엔 숨김
        self.custom_radio.setStyleSheet(f"""
            QRadioButton {{
                background-color: transparent;
                border-radius: 12px;
                border: 2px solid transparent;
            }}
            QRadioButton::indicator {{ width: 0px; height: 0px; }}
            QRadioButton:checked {{
                border: 2px solid {t['text_primary']};
            }}
            QRadioButton:hover {{
                border: 2px solid {t['text_secondary']};
            }}
        """)
        self.color_group.addButton(self.custom_radio, 99)
        color_layout.addWidget(self.custom_radio)

        # 사용자 지정 색상 (팔레트) 버튼
        custom_btn = QPushButton("+")
        custom_btn.setFixedSize(24, 24)
        custom_btn.setCursor(Qt.PointingHandCursor)
        custom_btn.setToolTip("색상 직접 선택")
        custom_btn.clicked.connect(self.pick_custom_color)
        custom_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px dashed {t['text_secondary']};
                border-radius: 12px;
                color: {t['text_secondary']};
                font-weight: bold;
                padding-bottom: 2px;
            }}
            QPushButton:hover {{
                background-color: {t['elevated_background']};
                border: 1px solid {t['text_primary']};
                color: {t['text_primary']};
            }}
        """)
        color_layout.addWidget(custom_btn)
        
        form.addRow("색상:", color_layout)
        
        layout.addLayout(form)
        
        # 기존 일정 데이터 로드
        if self.event_data:
            self.load_event_data()
        
        # 버튼들
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 삭제 버튼 (수정 모드일 때만)
        if self.event_data:
            delete_btn = QPushButton("🗑")
            delete_btn.setFont(QFont("Segoe UI Emoji", 12))
            delete_btn.clicked.connect(self.delete_event)
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t['elevated_background']};
                    color: #ff3b30;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 10px;
                    font-weight: bold;
                    border: 1px solid {t['border']};
                    font-family: 'Segoe UI Emoji';
                }}
                QPushButton:hover {{
                    background-color: #ff3b30;
                    color: white;
                    border: 1px solid #ff3b30;
                }}
            """)
            button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['button_secondary']};
                color: {t['text_primary']};
                border: 1px solid {t['border']};
                padding: 10px 20px;
                font-size: 10pt;
                min-width: 80px;
                border-radius: 10px;
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic';
            }}
            QPushButton:hover {{
                background-color: {t['elevated_background']};
            }}
        """)
        
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_event)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['accent']};
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 10pt;
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic';
            }}
            QPushButton:hover {{
                background-color: {t['button_primary']};
            }}
        """)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def style_calendar_popup(self, dt_edit):
        """QDateTimeEdit의 캘린더 팝업 스타일링"""
        calendar = dt_edit.calendarWidget()
        calendar.setGridVisible(False)  # 격자선 제거
        calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)  # 주차(Week Number) 제거
        calendar.setNavigationBarVisible(True)
        
        # 폰트 설정
        calendar.setFont(QFont("Malgun Gothic", 10))
        
        t = self.theme
        
        # 스타일시트 직접 적용 (배경색 강제)
        calendar.setStyleSheet(f"""
            QCalendarWidget QWidget {{
                background-color: {t['card_background']};
                color: {t['text_primary']};
            }}
            QCalendarWidget QTableView {{
                background-color: {t['input_background']};
                color: {t['text_primary']};
                selection-background-color: {t['accent']};
                selection-color: white;
                alternate-background-color: {t['elevated_background']};
            }}
            QCalendarWidget QToolButton {{
                color: {t['text_primary']};
                background-color: transparent;
                icon-size: 18px;
                border-radius: 4px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: {t['elevated_background']};
            }}
            QCalendarWidget QSpinBox {{
                background-color: {t['input_background']};
                color: {t['text_primary']};
                selection-background-color: {t['accent']};
                selection-color: white;
            }}
        """)
        
        # 팔레트 설정으로 배경색 강제 적용 (다크모드 문제 해결)
        palette = calendar.palette()
        bg_color = QColor(t['card_background'])
        text_color = QColor(t['text_primary'])
        
        palette.setColor(QPalette.Window, bg_color)
        palette.setColor(QPalette.Base, bg_color)
        palette.setColor(QPalette.Text, text_color)
        palette.setColor(QPalette.ButtonText, text_color)
        palette.setColor(QPalette.WindowText, text_color)
        calendar.setPalette(palette)
        
        # 요일 헤더 텍스트 색상 설정
        weekday_format = QTextCharFormat()
        weekday_format.setForeground(text_color)
        
        # 토요일 (파란색)
        saturday_format = QTextCharFormat()
        saturday_format.setForeground(QColor(t['saturday']))
        
        # 일요일 (빨간색)
        sunday_format = QTextCharFormat()
        sunday_format.setForeground(QColor(t['sunday']))
        
        # 평일 적용
        for day in [Qt.Monday, Qt.Tuesday, Qt.Wednesday, Qt.Thursday, Qt.Friday]:
            calendar.setWeekdayTextFormat(day, weekday_format)
            
        # 주말 적용
        calendar.setWeekdayTextFormat(Qt.Saturday, saturday_format)
        calendar.setWeekdayTextFormat(Qt.Sunday, sunday_format)
        
    def populate_times(self, combo):
        """시간 콤보박스 채우기 (15분 단위)"""
        times = []
        for h in range(24):
            for m in (0, 15, 30, 45):
                times.append(f"{h:02d}:{m:02d}")
        combo.addItems(times)
    
    def load_event_data(self):
        """기존 일정 데이터 로드"""
        if not self.event_data:
            return
        
        # 제목
        self.title_input.setText(self.event_data.get('summary', ''))
        
        # 시작/종료 시간
        start_str = self.event_data.get('start', '')
        end_str = self.event_data.get('end', '')
        
        if 'T' in start_str:
            # 시간 지정 일정
            start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            
            self.start_date.setDateTime(QDateTime(start_dt))
            self.start_time.setCurrentText(start_dt.strftime("%H:%M"))
            self.end_date.setDateTime(QDateTime(end_dt))
            self.end_time.setCurrentText(end_dt.strftime("%H:%M"))
            self.all_day_checkbox.setChecked(False)
        else:
            # 종일 일정
            start_dt = datetime.fromisoformat(start_str)
            end_dt = datetime.fromisoformat(end_str)
            
            self.start_date.setDateTime(QDateTime(start_dt))
            self.end_date.setDateTime(QDateTime(end_dt))
            self.all_day_checkbox.setChecked(True)
        
        # 설명
        self.description_input.setText(self.event_data.get('description', ''))
        
        # 위치
        self.location_input.setText(self.event_data.get('location', ''))
    
        # 색상
        color_id = self.event_data.get('colorId')
        if color_id:
            btn = self.color_group.button(int(color_id))
            if btn:
                btn.setChecked(True)
        else:
            # 색상 ID가 없으면 기본 색상(0번) 선택
            self.color_group.button(0).setChecked(True)

    def toggle_time_edit(self, state):
        """종일 체크 시 시간 표시/숨김"""
        is_all_day = (state == Qt.Checked)
        self.start_time.setVisible(not is_all_day)
        self.end_time.setVisible(not is_all_day)
    
    def pick_custom_color(self):
        """사용자 지정 색상 선택"""
        color = QColorDialog.getColor(parent=self, title="색상 선택")
        
        if color.isValid():
            self.custom_color_hex = color.name()
            
            # 커스텀 라디오 버튼 업데이트 및 선택
            self.update_custom_radio_style(self.custom_color_hex)
            self.custom_radio.setVisible(True)
            self.custom_radio.setChecked(True)

    def update_custom_radio_style(self, hex_color):
        """커스텀 라디오 버튼 스타일 업데이트"""
        t = self.theme
        self.custom_radio.setStyleSheet(f"""
            QRadioButton {{
                background-color: {hex_color};
                border-radius: 12px;
                border: 2px solid transparent;
            }}
            QRadioButton::indicator {{ width: 0px; height: 0px; }}
            QRadioButton:checked {{
                border: 2px solid {t['text_primary']};
                background-color: {hex_color};
            }}
            QRadioButton:hover {{
                border: 2px solid {t['text_secondary']};
            }}
        """)

    def find_nearest_color_id(self, target_color):
        """주어진 색상과 가장 가까운 구글 캘린더 색상 ID 찾기"""
        min_dist = float('inf')
        nearest_id = "1"
        
        r1, g1, b1 = target_color.red(), target_color.green(), target_color.blue()
        
        for cid, hex_code in self.EVENT_COLORS.items():
            c = QColor(hex_code)
            r2, g2, b2 = c.red(), c.green(), c.blue()
            
            # 유클리드 거리 계산
            dist = (r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2
            if dist < min_dist:
                min_dist = dist
                nearest_id = cid
                
        return nearest_id

    def save_event(self):
        """일정 저장"""
        # 입력 검증
        title = self.title_input.text().strip()
        if not title:
            msg = QMessageBox(self)
            msg.setWindowTitle("입력 오류")
            msg.setText("제목을 입력해주세요.")
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.button(QMessageBox.Ok).setText("확인")
            self.apply_message_box_style(msg)
            msg.exec_()
            return
        
        is_all_day = self.all_day_checkbox.isChecked()
        
        # 날짜/시간 가져오기 및 파싱
        try:
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            if is_all_day:
                start_dt = datetime.combine(start_date, datetime.min.time())
                end_dt = datetime.combine(end_date, datetime.min.time())
            else:
                # 시간 파싱
                start_time_str = self.start_time.currentText()
                end_time_str = self.end_time.currentText()
                
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                end_time = datetime.strptime(end_time_str, "%H:%M").time()
                
                start_dt = datetime.combine(start_date, start_time)
                end_dt = datetime.combine(end_date, end_time)
        except ValueError:
            msg = QMessageBox(self)
            msg.setWindowTitle("입력 오류")
            msg.setText("시간 형식이 올바르지 않습니다. (HH:mm)")
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.button(QMessageBox.Ok).setText("확인")
            self.apply_message_box_style(msg)
            msg.exec_()
            return

        # 종료가 시작보다 빠른지 확인
        if end_dt <= start_dt:
            msg = QMessageBox(self)
            msg.setWindowTitle("입력 오류")
            msg.setText("종료 시간이 시작 시간보다 빠릅니다.")
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.button(QMessageBox.Ok).setText("확인")
            self.apply_message_box_style(msg)
            msg.exec_()
            return
        
        # 날짜 형식 변환
        if is_all_day:
            start_str = start_dt.strftime('%Y-%m-%d')
            # 종일 이벤트는 종료일이 exclusive이므로 +1일
            end_dt_adjusted = end_dt + timedelta(days=1)
            end_str = end_dt_adjusted.strftime('%Y-%m-%d')
        else:
            start_str = start_dt.isoformat()
            end_str = end_dt.isoformat()
        
        description = self.description_input.toPlainText().strip()
        location = self.location_input.text().strip()
        
        # 색상 처리
        checked_id = self.color_group.checkedId()
        color_id = None
        custom_color = "" # 빈 문자열은 삭제를 의미
        
        if checked_id == 99: # 사용자 지정 색상
            if self.custom_color_hex:
                custom_color = self.custom_color_hex
                # 호환성을 위해 가장 가까운 색상 ID도 설정
                nearest_id = self.find_nearest_color_id(QColor(custom_color))
                color_id = nearest_id
        elif checked_id > 0: # 구글 기본 색상
            color_id = str(checked_id)
            custom_color = "" # 사용자 지정 색상 제거
        else: # 0번(기본) 또는 선택 안됨
            color_id = ""  # None 대신 빈 문자열 전달 (삭제 요청)
            custom_color = ""
        
        # API 호출
        if self.event_id:
            # 수정
            result = self.calendar_api.update_event(
                event_id=self.event_id,
                summary=title,
                start_datetime=start_str,
                end_datetime=end_str,
                description=description,
                location=location,
                is_all_day=is_all_day,
                color_id=color_id,
                custom_color=custom_color
            )
        else:
            # 생성
            result = self.calendar_api.create_event(
                summary=title,
                start_datetime=start_str,
                end_datetime=end_str,
                description=description,
                location=location,
                is_all_day=is_all_day,
                color_id=color_id,
                custom_color=custom_color
            )
        
        if result:
            self.accept()
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("오류")
            msg.setText("일정 저장에 실패했습니다.")
            msg.setIcon(QMessageBox.Critical)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.button(QMessageBox.Ok).setText("확인")
            self.apply_message_box_style(msg)
            msg.exec_()
    
    def delete_event(self):
        """일정 삭제"""
        if not self.event_id:
            return
        
        # 확인 대화상자
        msg = QMessageBox(self)
        msg.setWindowTitle("일정 삭제")
        msg.setText("정말로 이 일정을 삭제하시겠습니까?")
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.button(QMessageBox.Yes).setText("예")
        msg.button(QMessageBox.No).setText("아니오")
        msg.setDefaultButton(QMessageBox.No)
        
        self.apply_message_box_style(msg)
        reply = msg.exec_()
        
        if reply == QMessageBox.Yes:
            success = self.calendar_api.delete_event(self.event_id)
            if success:
                self.accept()
            else:
                error_msg = QMessageBox(self)
                error_msg.setWindowTitle("오류")
                error_msg.setText("일정 삭제에 실패했습니다.")
                error_msg.setIcon(QMessageBox.Critical)
                error_msg.setStandardButtons(QMessageBox.Ok)
                error_msg.button(QMessageBox.Ok).setText("확인")
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
