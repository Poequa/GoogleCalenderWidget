"""
iOS 캘린더 스타일 월별 뷰
"""
import calendar
import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QGridLayout, QFrame, QScrollArea, QApplication,
                            QGraphicsDropShadowEffect, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QFont, QCursor, QColor, QRegion, QPainterPath
from event_dialog import EventDialog
from event_detail_dialog import EventDetailDialog
import theme
import config


class ClickableFrame(QFrame):
    """클릭 가능한 프레임 - 수동 호버 효과"""
    clicked = pyqtSignal(str)  # date_str 전달
    
    def __init__(self, date_str, parent=None):
        super().__init__(parent)
        self.date_str = date_str
        self.is_today = False
        self.theme = None
        self.setCursor(QCursor(Qt.PointingHandCursor))
    
    def set_style(self, theme, is_today):
        """스타일 설정"""
        self.theme = theme
        self.is_today = is_today
        self.update_style(False)
    
    def update_style(self, hovered):
        """스타일 업데이트 - 항상 둥근 모서리 유지"""
        if not self.theme:
            return
        
        t = self.theme
        if self.is_today:
            if hovered:
                bg_color = t['accent']
            else:
                bg_color = t['today']
        else:
            if hovered:
                bg_color = t['elevated_background']
            else:
                bg_color = t['card_background']
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: none;
                border-radius: 18px;
                padding: 3px;
            }}
        """)
    
    def enterEvent(self, event):
        """마우스 진입 - 둥근 모서리 유지"""
        self.update_style(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """마우스 나감 - 둥근 모서리 유지"""
        self.update_style(False)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.date_str)
            event.accept()
        else:
            super().mousePressEvent(event)


class ClickableEventContainer(QFrame):
    """클릭 가능한 이벤트 컨테이너"""
    clicked = pyqtSignal(dict)  # event_data 전달
    
    def __init__(self, event_data, parent=None):
        super().__init__(parent)
        self.event_data = event_data
        self.setCursor(QCursor(Qt.PointingHandCursor))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.event_data)
            event.accept()
        else:
            super().mousePressEvent(event)


class ClickableLabel(QLabel):
    """클릭 가능한 라벨 (일정용)"""
    clicked = pyqtSignal(dict)  # event_data 전달
    
    def __init__(self, text, event_data, parent=None):
        super().__init__(text, parent)
        self.event_data = event_data
        self.setCursor(QCursor(Qt.PointingHandCursor))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.event_data)
            event.accept()
        else:
            super().mousePressEvent(event)


class ClickableMoreContainer(QFrame):
    """+N개 더보기 버튼"""
    clicked = pyqtSignal(str)  # date_str 전달
    
    def __init__(self, date_str, parent=None):
        super().__init__(parent)
        self.date_str = date_str
        self.setCursor(QCursor(Qt.PointingHandCursor))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.date_str)
            event.accept()
        else:
            super().mousePressEvent(event)


class DayEventsDialog(QDialog):
    """해당 날짜의 모든 일정을 보여주는 팝업"""
    def __init__(self, date_str, events, calendar_view, parent=None):
        super().__init__(parent)
        self.date_str = date_str
        self.events = events
        self.calendar_view = calendar_view
        self.calendar_api = calendar_view.calendar_api
        self.theme = theme.get_current_theme()
        
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFixedWidth(280)
        
        # 투명도 및 애니메이션
        current_opacity = config.settings.get('widget_opacity', 0.9)
        target_opacity = 1.0 if current_opacity >= 1.0 else 0.95
        self.setWindowOpacity(0.0)
        
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(target_opacity)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()
        
        self.init_ui()
        self.apply_rounded_corners()

    def init_ui(self):
        t = self.theme
        self.setStyleSheet(f"background-color: {t['card_background']}; border-radius: 12px; border: 1px solid {t['border']};")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 일정 목록 (스크롤)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(0, 0, 5, 0) # 스크롤바 여백 확보
        
        for event in self.events:
            # CalendarView의 create_event_item 로직 재사용하여 아이템 생성
            item = self.calendar_view.create_event_item(event, is_today=False)
            item.setMinimumHeight(34) # 아이템 최소 높이 보장
            content_layout.addWidget(item)
            
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        
        # [수정] 높이 계산 및 고정 (아이템 개수 * 높이 + 여백)
        # 아이템(34px) + 간격(5px) = 약 39px
        total_content_height = len(self.events) * 39 + 10
        
        # 최소 60px ~ 최대 300px 사이로 높이 고정
        fixed_height = min(max(total_content_height, 60), 300)
        scroll.setFixedHeight(fixed_height)
        
        layout.addWidget(scroll)
        
        self.setLayout(layout)

    def apply_rounded_corners(self):
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def resizeEvent(self, event):
        """크기가 변경될 때 마스크(둥근 모서리) 업데이트"""
        self.apply_rounded_corners()
        super().resizeEvent(event)

class CalendarView(QWidget):
    # 구글 캘린더 이벤트 색상 매핑
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

    def __init__(self, calendar_api, parent=None):
        super().__init__(parent)
        self.calendar_api = calendar_api
        self.current_year = datetime.datetime.now().year
        self.current_month = datetime.datetime.now().month
        self.events_by_date = {}
        self.event_colors_map = self.EVENT_COLORS.copy()
        self.colors_loaded = False
        
        # 현재 테마 가져오기
        self.theme = theme.get_current_theme()
        
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 헤더 (월 표시 + 이전/다음 버튼)
        header_layout = QHBoxLayout()
        
        prev_btn = QPushButton("◀")
        prev_btn.clicked.connect(self.prev_month)
        prev_btn.setMaximumWidth(40)
        prev_btn.setMaximumHeight(40)
        prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['button_primary']};
                color: white;
                border: none;
                padding: 5px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent']};
            }}
        """)
        
        self.month_label = QLabel()
        self.month_label.setFont(QFont("Malgun Gothic", 14, QFont.Bold))
        self.month_label.setAlignment(Qt.AlignCenter)
        self.month_label.setStyleSheet(f"color: {self.theme['text_primary']};")
        
        next_btn = QPushButton("▶")
        next_btn.clicked.connect(self.next_month)
        next_btn.setMaximumWidth(40)
        next_btn.setMaximumHeight(40)
        next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['button_primary']};
                color: white;
                border: none;
                padding: 5px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent']};
            }}
        """)
        
        today_btn = QPushButton("📅 오늘")
        today_btn.clicked.connect(self.go_to_today)
        today_btn.setMaximumWidth(80)
        today_btn.setMaximumHeight(40)
        today_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['elevated_background']};
                color: {self.theme['text_primary']};
                border: 1px solid {self.theme['border']};
                padding: 8px 15px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.theme['button_primary']};
                color: white;
                border: none;
            }}
        """)
        
        header_layout.addWidget(prev_btn)
        header_layout.addWidget(self.month_label, 1)
        header_layout.addWidget(today_btn)
        header_layout.addWidget(next_btn)
        
        layout.addLayout(header_layout)
        
        # 요일 헤더
        weekday_layout = QHBoxLayout()
        weekday_layout.setSpacing(8)
        weekdays = ['일', '월', '화', '수', '목', '금', '토']
        for i, day in enumerate(weekdays):
            label = QLabel(day)
            label.setAlignment(Qt.AlignCenter)
            label.setFont(QFont("Malgun Gothic", 10, QFont.Bold))
            if i == 0:  # 일요일
                label.setStyleSheet(f"color: {self.theme['sunday']}; padding: 8px;")
            elif i == 6:  # 토요일
                label.setStyleSheet(f"color: {self.theme['saturday']}; padding: 8px;")
            else:
                label.setStyleSheet(f"color: {self.theme['text_secondary']}; padding: 8px;")
            weekday_layout.addWidget(label)
        
        layout.addLayout(weekday_layout)
        
        # 캘린더 그리드 (스크롤 가능) - 배경 검은색
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {self.theme['background']};
            }}
            QScrollBar:vertical {{
                width: 8px;
                background: transparent;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.theme['text_tertiary']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.theme['text_secondary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        calendar_widget = QWidget()
        calendar_widget.setStyleSheet(f"background-color: {self.theme['background']};")
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(8)
        calendar_widget.setLayout(self.calendar_grid)
        
        scroll.setWidget(calendar_widget)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
        
        # 초기 캘린더 렌더링
        self.render_calendar()
    
    def prev_month(self):
        """이전 달로 이동"""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.render_calendar()
    
    def next_month(self):
        """다음 달로 이동"""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.render_calendar()
    
    def go_to_today(self):
        """오늘 날짜로 이동"""
        now = datetime.datetime.now()
        self.current_year = now.year
        self.current_month = now.month
        self.render_calendar()
    
    def load_events(self):
        """이벤트 로드"""
        try:
            if not self.calendar_api.service:
                self.calendar_api.authenticate()
            
            # 색상 정보 로드 (최초 1회)
            if not self.colors_loaded:
                colors_data = self.calendar_api.get_colors()
                if colors_data and 'event' in colors_data:
                    for cid, cdata in colors_data['event'].items():
                        # API에서 가져온 색상으로 업데이트
                        self.event_colors_map[cid] = cdata['background']
                self.colors_loaded = True

            self.events_by_date = self.calendar_api.get_events_for_month(
                self.current_year, self.current_month
            )
            
        except Exception as e:
            print(f"이벤트 로드 실패: {e}")
            self.events_by_date = {}

    def get_contrast_text_color(self, hex_color):
        """배경색에 따라 검정/흰색 텍스트 색상 반환 (가독성 확보)"""
        if not hex_color or not hex_color.startswith('#'):
            return 'white'
        
        # HEX -> RGB 변환
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # 휘도(Luminance) 계산 공식
        luminance = (0.299 * r + 0.587 * g + 0.114 * b)
        
        # 밝으면(128 이상) 검정색, 어두우면 흰색 텍스트
        return 'black' if luminance > 128 else 'white'
    
    def get_hover_color(self, bg_color):
        """배경색의 호버 색상(더 밝게/진하게) 반환"""
        if bg_color.startswith('rgba'):
            try:
                # rgba(r, g, b, a) 파싱
                content = bg_color[5:-1]
                parts = [x.strip() for x in content.split(',')]
                r, g, b = parts[0], parts[1], parts[2]
                a = float(parts[3])
                
                # 투명도 증가 (더 잘 보이게)
                new_a = min(1.0, a + 0.15)
                return f"rgba({r}, {g}, {b}, {new_a})"
            except:
                return bg_color
        elif bg_color.startswith('#'):
            c = QColor(bg_color)
            # 밝게 만들기 (115%)
            return c.lighter(115).name()
        else:
            return bg_color

    def render_calendar(self):
        """캘린더 렌더링"""
        # 월 레이블 업데이트
        self.month_label.setText(f"{self.current_year}년 {self.current_month}월")
        
        # 이벤트 로드
        self.load_events()
        
        # 기존 그리드 지우기
        for i in reversed(range(self.calendar_grid.count())):
            self.calendar_grid.itemAt(i).widget().deleteLater()
        
        # 달력 데이터 생성
        calendar.setfirstweekday(calendar.SUNDAY)
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        today = datetime.date.today()
        
        # 날짜 셀 생성
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    # 빈 셀
                    empty_label = QLabel("")
                    self.calendar_grid.addWidget(empty_label, week_num, day_num)
                else:
                    # 날짜 셀
                    date_str = f"{self.current_year:04d}-{self.current_month:02d}-{day:02d}"
                    cell = self.create_date_cell(day, date_str, day_num, 
                                                 today.year == self.current_year and
                                                 today.month == self.current_month and
                                                 today.day == day)
                    self.calendar_grid.addWidget(cell, week_num, day_num)
    
    def create_date_cell(self, day, date_str, weekday, is_today):
        """iOS 스타일 날짜 셀 생성"""
        cell = ClickableFrame(date_str)
        cell.setFrameShape(QFrame.NoFrame)
        cell.setMinimumHeight(95)
        
        # 수동 호버 효과 설정 (둥근 모서리 유지)
        cell.set_style(self.theme, is_today)
        
        # 클릭 이벤트 연결
        cell.clicked.connect(self.on_date_clicked)
        
        t = self.theme
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        if is_today:
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(0, 122, 255, 80))
            shadow.setOffset(0, 4)
        else:
            shadow.setBlurRadius(8)
            shadow.setColor(QColor(0, 0, 0, 20))
            shadow.setOffset(0, 2)
        
        cell.setGraphicsEffect(shadow)
        
        # 날짜를 위로, 일정을 아래로 배치
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 1)
        layout.setSpacing(1)
        
        # 날짜 라벨 - 왼쪽 위에 배치
        day_label = QLabel(str(day))
        day_label.setFont(QFont("Malgun Gothic", 12, QFont.Bold))
        day_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # 날짜 라벨 색상
        padding_style = "padding: 0px 0 0 2px;"
        bg_style = "background-color: transparent;"
        if is_today:
            day_label.setStyleSheet(f"color: white; {padding_style} {bg_style}")
        elif weekday == 0:  # 일요일
            day_label.setStyleSheet(f"color: {t['sunday']}; {padding_style} {bg_style}")
        elif weekday == 6:  # 토요일
            day_label.setStyleSheet(f"color: {t['saturday']}; {padding_style} {bg_style}")
        else:
            day_label.setStyleSheet(f"color: {t['text_primary']}; {padding_style} {bg_style}")
        
        layout.addWidget(day_label)
        
        # 일정 표시 (최대 4개까지 표시 가능하도록)
        events = self.events_by_date.get(date_str, [])
        for i, event in enumerate(events[:5]):  # 4개까지 표시
            if i < 4:
                # 휴일 여부 확인 (calendar_id에 'holiday'가 포함되어 있으면 휴일로 간주)
                is_holiday = 'holiday' in event.get('calendar_id', '')
                color_id = event.get('colorId')
                custom_color = event.get('customColor')
                
                # 스타일 결정
                if is_today:
                    if is_holiday:
                        bg_color = 'rgba(255, 255, 255, 0.35)'
                        text_color = 'white'
                    elif custom_color:
                        bg_color = custom_color
                        text_color = self.get_contrast_text_color(custom_color)
                    elif color_id and color_id in self.event_colors_map:
                        bg_hex = self.event_colors_map[color_id]
                        bg_color = bg_hex
                        text_color = self.get_contrast_text_color(bg_hex)
                    else:
                        bg_color = 'rgba(255, 255, 255, 0.2)'
                        text_color = 'rgba(255, 255, 255, 0.95)'
                else:
                    if is_holiday:
                        # 테마의 sunday 색상(빨강) 활용
                        c = QColor(t['sunday'])
                        bg_color = f"rgba({c.red()}, {c.green()}, {c.blue()}, 0.15)"
                        text_color = t['sunday']
                    elif custom_color:
                        bg_color = custom_color
                        text_color = self.get_contrast_text_color(custom_color)
                    elif color_id and color_id in self.event_colors_map:
                        bg_hex = self.event_colors_map[color_id]
                        bg_color = bg_hex
                        text_color = self.get_contrast_text_color(bg_hex)
                    else:
                        bg_color = 'rgba(0, 122, 255, 0.12)'
                        text_color = t['text_secondary']

                # 호버 색상 계산
                hover_color = self.get_hover_color(bg_color)

                # 일정을 동그란 박스로 표시 (전체 클릭 가능)
                event_container = ClickableEventContainer(event)
                event_container.clicked.connect(self.on_event_clicked)
                event_container.setStyleSheet(f"""
                    QFrame {{
                        background-color: {bg_color};
                        border-radius: 8px;
                        padding: 1px 4px;
                        margin: 0px 0px;
                    }}
                    QFrame:hover {{
                        background-color: {hover_color};
                    }}
                """)
                event_layout = QHBoxLayout()
                event_layout.setContentsMargins(0, 0, 0, 0)
                event_layout.setSpacing(0)
                
                event_label = QLabel(f"{event['summary'][:13]}")
                event_label.setFont(QFont("Malgun Gothic", 8))
                event_label.setStyleSheet(f"color: {text_color}; background: transparent;")
                event_label.setWordWrap(False)
                # 마우스 이벤트가 컨테이너로 전달되도록 설정
                event_label.setAttribute(Qt.WA_TransparentForMouseEvents)
                
                event_layout.addWidget(event_label)
                event_container.setLayout(event_layout)
                layout.addWidget(event_container)
            elif i == 4:
                # "+N개 더" 표시
                if is_today:
                    bg_color = 'rgba(255, 255, 255, 0.15)'
                    hover_color = 'rgba(255, 255, 255, 0.30)'
                else:
                    bg_color = 'rgba(0, 122, 255, 0.08)'
                    hover_color = 'rgba(0, 122, 255, 0.23)'
                
                more_container = ClickableMoreContainer(date_str)
                more_container.clicked.connect(self.on_more_clicked)
                more_container.setStyleSheet(f"""
                    ClickableMoreContainer {{
                        background-color: {bg_color};
                        border-radius: 8px;
                        padding: 1px 4px;
                        margin: 0px 0px;
                    }}
                    ClickableMoreContainer:hover {{
                        background-color: {hover_color};
                    }}
                """)
                more_layout = QHBoxLayout()
                more_layout.setContentsMargins(0, 0, 0, 0)
                
                more_label = QLabel(f"+{len(events) - 4}개")
                more_label.setFont(QFont("Malgun Gothic", 7))
                if is_today:
                    more_label.setStyleSheet("color: white; background: transparent;")
                else:
                    more_label.setStyleSheet(f"color: {t['accent']}; background: transparent;")
                
                more_layout.addWidget(more_label)
                more_container.setLayout(more_layout)
                layout.addWidget(more_container)
                break
        
        layout.addStretch()
        cell.setLayout(layout)
        
        return cell
    
    def create_event_item(self, event, is_today=False):
        """이벤트 아이템 생성 (create_date_cell 및 DayEventsDialog에서 사용)"""
        t = self.theme
        is_holiday = 'holiday' in event.get('calendar_id', '')
        color_id = event.get('colorId')
        custom_color = event.get('customColor')
        
        # 스타일 결정
        if is_today:
            if is_holiday:
                bg_color = 'rgba(255, 255, 255, 0.35)'
                text_color = 'white'
            elif custom_color:
                bg_color = custom_color
                text_color = self.get_contrast_text_color(custom_color)
            elif color_id and color_id in self.event_colors_map:
                bg_hex = self.event_colors_map[color_id]
                bg_color = bg_hex
                text_color = self.get_contrast_text_color(bg_hex)
            else:
                bg_color = 'rgba(255, 255, 255, 0.2)'
                text_color = 'rgba(255, 255, 255, 0.95)'
        else:
            if is_holiday:
                c = QColor(t['sunday'])
                bg_color = f"rgba({c.red()}, {c.green()}, {c.blue()}, 0.15)"
                text_color = t['sunday']
            elif custom_color:
                bg_color = custom_color
                text_color = self.get_contrast_text_color(custom_color)
            elif color_id and color_id in self.event_colors_map:
                bg_hex = self.event_colors_map[color_id]
                bg_color = bg_hex
                text_color = self.get_contrast_text_color(bg_hex)
            else:
                bg_color = 'rgba(0, 122, 255, 0.12)'
                text_color = t['text_secondary']

        hover_color = self.get_hover_color(bg_color)

        event_container = ClickableEventContainer(event)
        event_container.clicked.connect(self.on_event_clicked)
        event_container.setStyleSheet(f"""
            QFrame {{ background-color: {bg_color}; border-radius: 8px; padding: 4px; margin: 0px; }}
            QFrame:hover {{ background-color: {hover_color}; }}
        """)
        
        event_label = QLabel(f"{event['summary']}")
        event_label.setFont(QFont("Malgun Gothic", 9))
        event_label.setStyleSheet(f"color: {text_color}; background: transparent;")
        event_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.addWidget(event_label)
        event_container.setLayout(layout)
        
        return event_container

    def on_date_clicked(self, date_str):
        """날짜 클릭 이벤트"""
        year, month, day = map(int, date_str.split('-'))
        selected_date = datetime.date(year, month, day)
        
        dialog = EventDialog(self.calendar_api, selected_date=selected_date, parent=self)
        if dialog.exec_():
            self.refresh()
    
    def on_event_clicked(self, event_data):
        """일정 클릭 이벤트"""
        sender = self.sender()
        
        detail_dialog = EventDetailDialog(event_data, self.calendar_api, parent=self)
        
        if sender:
            # 클릭된 위젯의 부모(이벤트 컨테이너)를 기준으로 위치 설정
            target = sender.parent() if sender.parent() else sender
            
            # 다이얼로그 크기 계산 (내용에 맞게 크기 확정)
            detail_dialog.adjustSize()
            
            # 타겟 위젯의 전역 좌표(화면상 위치) 가져오기
            target_pos = target.mapToGlobal(QPoint(0, 0))
            
            # 화면 정보 가져오기 (먼저 계산)
            screen = QApplication.screenAt(target_pos)
            if not screen:
                screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            
            # 다이얼로그를 타겟의 왼쪽, 위쪽에 맞춰 배치 (10px 간격)
            x = target_pos.x() - detail_dialog.width() - 10
            y = target_pos.y()
            
            # 화면 왼쪽 밖으로 나가는지 확인
            if x < screen_geometry.left():
                # 오른쪽으로 배치 (타겟 x + 타겟 너비 + 10px)
                x = target_pos.x() + target.width() + 10
            
            # 화면 아래쪽 밖으로 나가는지 확인
            if y + detail_dialog.height() > screen_geometry.bottom():
                # 위쪽으로 배치 (타겟의 하단에 다이얼로그 하단을 맞춤)
                y = target_pos.y() + target.height() - detail_dialog.height()
                
            # [중요] 화면 상하 경계 강제 보정 (잘림 방지)
            if y < screen_geometry.top():
                y = screen_geometry.top()
            elif y + detail_dialog.height() > screen_geometry.bottom():
                y = screen_geometry.bottom() - detail_dialog.height()

            detail_dialog.move(x, y)
            
        result = detail_dialog.exec_()
        
        if result == EventDetailDialog.Accepted:
            if detail_dialog.action == 'edit':
                edit_dialog = EventDialog(self.calendar_api, event_data=event_data, parent=self)
                if edit_dialog.exec_():
                    self.refresh()
            elif detail_dialog.action == 'delete':
                self.refresh()

    def on_more_clicked(self, date_str):
        """+N개 클릭 시 팝업 표시"""
        sender = self.sender()
        # 안 보이는 일정(4번째 이후)만 표시
        events = self.events_by_date.get(date_str, [])[4:]
        
        dialog = DayEventsDialog(date_str, events, self, parent=self)
        
        if sender:
            target = sender
            dialog.ensurePolished() # 스타일 적용 및 사이즈 계산 준비
            dialog.adjustSize()
            target_pos = target.mapToGlobal(QPoint(0, 0))
            
            # 화면 정보 가져오기
            screen = QApplication.screenAt(target_pos)
            if not screen: screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            
            x = target_pos.x() - dialog.width() - 10
            y = target_pos.y()
            
            if x < screen_geometry.left():
                x = target_pos.x() + target.width() + 10
            
            if y + dialog.height() > screen_geometry.bottom():
                y = target_pos.y() + target.height() - dialog.height()
            
            # [중요] 화면 상하 경계 강제 보정 (여백 5px 추가)
            if y < screen_geometry.top(): y = screen_geometry.top()
            elif y + dialog.height() > screen_geometry.bottom(): y = screen_geometry.bottom() - dialog.height() - 5
            
            dialog.move(x, y)
            
        dialog.exec_()
        # 다이얼로그 닫힌 후 새로고침 (삭제/수정 반영)
        self.refresh()
    
    def refresh(self):
        """새로고침"""
        self.theme = theme.get_current_theme()
        self.month_label.setStyleSheet(f"color: {self.theme['text_primary']};")
        self.render_calendar()

    def apply_message_box_style(self, msg):
        """메시지 박스 스타일 적용 (자식 다이얼로그에서 호출)"""
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
