"""
목록 뷰 (리스트 형태로 일정 표시)
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                            QScrollArea, QFrame, QGraphicsDropShadowEffect, QApplication,
                            QScroller, QScrollerProperties, QHBoxLayout)
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QCursor, QRegion, QPainterPath, QColor, QPalette
from datetime import datetime, timedelta
import theme
from event_detail_dialog import EventDetailDialog
from event_dialog import EventDialog
import config


class ClickableEventFrame(QFrame):
    """클릭 가능한 이벤트 프레임"""
    def __init__(self, event_data, calendar_api, parent_widget, parent=None):
        super().__init__(parent)
        self.event_data = event_data
        self.calendar_api = calendar_api
        self.parent_widget = parent_widget
        self.setCursor(QCursor(Qt.PointingHandCursor))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.press_pos = event.globalPos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and hasattr(self, 'press_pos'):
            # 드래그 거리가 짧을 때만 클릭으로 인정 (스크롤 오작동 방지)
            moved = (event.globalPos() - self.press_pos).manhattanLength()
            if moved < 10:
                self.show_event_detail()
                event.accept()
        super().mouseReleaseEvent(event)
    
    def show_event_detail(self):
        """일정 상세 다이얼로그 표시"""
        # ✅ parent를 self.parent_widget으로 변경하여 스타일 상속 방지
        detail_dialog = EventDetailDialog(self.event_data, self.calendar_api, parent=self.parent_widget)
        
        # 위치 계산
        target = self
        detail_dialog.ensurePolished() # 스타일 적용 및 사이즈 계산 준비
        detail_dialog.adjustSize()
        
        target_pos = target.mapToGlobal(QPoint(0, 0))
        
        # 화면 정보 가져오기
        screen = QApplication.screenAt(target_pos)
        if not screen:
            screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # 기본: 왼쪽 배치 (10px 간격)
        x = target_pos.x() - detail_dialog.width() - 10
        y = target_pos.y()
        
        # 화면 왼쪽 밖으로 나가는지 확인
        if x < screen_geometry.left():
            # 오른쪽으로 배치
            x = target_pos.x() + target.width() + 10
            
        if y + detail_dialog.height() > screen_geometry.bottom():
            # 위쪽으로 배치 (타겟의 하단에 다이얼로그 하단을 맞춤)
            y = target_pos.y() + target.height() - detail_dialog.height()
            
        # [중요] 화면 상하 경계 강제 보정
        if y < screen_geometry.top():
            y = screen_geometry.top()
        elif y + detail_dialog.height() > screen_geometry.bottom():
            y = screen_geometry.bottom() - detail_dialog.height() - 5
                
        detail_dialog.move(x, y)
        
        result = detail_dialog.exec_()
        
        if result == EventDetailDialog.Accepted:
            if detail_dialog.action == 'edit':
                edit_dialog = EventDialog(self.calendar_api, event_data=self.event_data, parent=self.parent_widget)
                if edit_dialog.exec_():
                    # 수정 후 새로고침
                    self.parent_widget.refresh()
            elif detail_dialog.action == 'delete':
                # 삭제 후 새로고침
                self.parent_widget.refresh()


class SmoothScrollArea(QScrollArea):
    """부드러운 스크롤 (휠 + 드래그) 지원"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. 키네틱 스크롤 (마우스 드래그로 스크롤)
        QScroller.grabGesture(self.viewport(), QScroller.LeftMouseButtonGesture)
        props = QScroller.scroller(self.viewport()).scrollerProperties()
        props.setScrollMetric(QScrollerProperties.OvershootDragDistanceFactor, 0.1)
        props.setScrollMetric(QScrollerProperties.OvershootScrollDistanceFactor, 0.1)
        props.setScrollMetric(QScrollerProperties.FrameRate, QScrollerProperties.Fps60)
        QScroller.scroller(self.viewport()).setScrollerProperties(props)
        
        # 2. 휠 스크롤 애니메이션
        self.scroll_anim = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.scroll_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.scroll_anim.setDuration(400)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            super().wheelEvent(event)
            return

        delta = event.angleDelta().y()
        if delta == 0:
            return

        v_bar = self.verticalScrollBar()
        current_val = v_bar.value()
        
        # 애니메이션 중이면 목표 지점에서 시작
        if self.scroll_anim.state() == QPropertyAnimation.Running:
            start_val = self.scroll_anim.endValue()
        else:
            start_val = current_val

        # 스크롤 거리 계산
        step = -delta 
        target = start_val + step
        target = max(v_bar.minimum(), min(v_bar.maximum(), target))

        self.scroll_anim.stop()
        self.scroll_anim.setStartValue(current_val)
        self.scroll_anim.setEndValue(target)
        self.scroll_anim.start()
        
        event.accept()


class ListView(QWidget):
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
        
        # 색상 맵 초기화
        self.event_colors_map = self.EVENT_COLORS.copy()
        self.colors_loaded = False
        
        # 현재 테마 가져오기
        self.theme = theme.get_current_theme()
        
        self.init_ui()
        
        # 초기 로드
        self.load_events()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 이벤트 목록 스크롤 영역
        scroll = SmoothScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # 테마에 따른 배경색
        t = self.theme
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {t['background']};
            }}
            QScrollBar:vertical {{
                width: 8px;
                background: transparent;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {t['text_tertiary']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {t['text_secondary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        self.events_widget = QWidget()
        self.events_widget.setStyleSheet(f"background-color: {t['background']};")
        self.events_layout = QVBoxLayout()
        self.events_layout.setSpacing(0)  # 간격 제거 (헤더와 아이템 간격은 개별 조정)
        self.events_layout.setContentsMargins(0, 0, 0, 0)
        self.events_layout.setAlignment(Qt.AlignTop)  # ✅ 위쪽 정렬!
        self.events_widget.setLayout(self.events_layout)
        
        scroll.setWidget(self.events_widget)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
    
    def load_events(self):
        """이벤트 로드"""
        try:
            # 기존 이벤트 제거
            for i in reversed(range(self.events_layout.count())):
                item = self.events_layout.itemAt(i)
                if item:
                    if item.widget():
                        item.widget().deleteLater()
                    elif item.spacerItem():
                        self.events_layout.removeItem(item)
            
            # 로딩 메시지
            t = self.theme
            loading_label = QLabel("⏳ 로딩 중...")
            loading_label.setFont(QFont("Malgun Gothic", 11))
            loading_label.setStyleSheet(f"color: {t['text_secondary']}; padding: 20px;")
            loading_label.setAlignment(Qt.AlignCenter)
            self.events_layout.addWidget(loading_label)
            
            # 인증 및 이벤트 가져오기
            if not self.calendar_api.service:
                self.calendar_api.authenticate()
            
            # 색상 정보 로드 (최초 1회)
            if not self.colors_loaded:
                colors_data = self.calendar_api.get_colors()
                if colors_data and 'event' in colors_data:
                    for cid, cdata in colors_data['event'].items():
                        self.event_colors_map[cid] = cdata['background']
                self.colors_loaded = True
            
            # 앞으로 30일간의 일정 최대 50개 가져오기
            events = self.calendar_api.get_upcoming_events(
                max_results=50,
                days_ahead=30
            )
            
            # 로딩 메시지 제거
            loading_label.deleteLater()
            
            if not events:
                no_events_label = QLabel("📭 예정된 일정이 없습니다")
                no_events_label.setFont(QFont("Malgun Gothic", 11))
                no_events_label.setStyleSheet(f"color: {t['text_secondary']}; padding: 20px;")
                no_events_label.setAlignment(Qt.AlignCenter)
                self.events_layout.addWidget(no_events_label)
            else:
                last_date = None
                for event in events:
                    # 날짜별 그룹화
                    start_str = event['start']
                    if 'T' in start_str:
                        event_date = start_str.split('T')[0]
                    else:
                        event_date = start_str
                    
                    if event_date != last_date:
                        self.add_date_header(event_date)
                        last_date = event_date
                    
                    self.add_event_item(event)
            
            # ✅ addStretch를 맨 마지막에 추가 (위에 고정)
            self.events_layout.addStretch()
            
        except FileNotFoundError as e:
            error_label = QLabel(f"❌ {str(e)}")
            error_label.setFont(QFont("Malgun Gothic", 10))
            error_label.setWordWrap(True)
            error_label.setStyleSheet("color: #ff6b6b; padding: 20px;")
            error_label.setAlignment(Qt.AlignCenter)
            self.events_layout.addWidget(error_label)
            
        except Exception as e:
            error_label = QLabel(f"❌ 오류: {str(e)}")
            error_label.setFont(QFont("Malgun Gothic", 10))
            error_label.setWordWrap(True)
            error_label.setStyleSheet("color: #ff6b6b; padding: 20px;")
            error_label.setAlignment(Qt.AlignCenter)
            self.events_layout.addWidget(error_label)
    
    def add_date_header(self, date_str):
        """날짜 헤더 추가"""
        t = self.theme
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            today = datetime.now().date()
            dt_date = dt.date()
            
            diff = (dt_date - today).days
            
            day_names = ['월', '화', '수', '목', '금', '토', '일']
            day_name = day_names[dt.weekday()]
            
            if diff == 0:
                text = f"오늘 · {dt.month}월 {dt.day}일 ({day_name})"
                color = t['accent']
            elif diff == 1:
                text = f"내일 · {dt.month}월 {dt.day}일 ({day_name})"
                color = t['text_primary']
            else:
                text = f"{dt.month}월 {dt.day}일 ({day_name})"
                color = t['text_primary']
                
            label = QLabel(text)
            label.setFont(QFont("Malgun Gothic", 10, QFont.Bold))
            label.setStyleSheet(f"color: {color}; margin-top: 20px; margin-bottom: 8px; margin-left: 5px;")
            self.events_layout.addWidget(label)
        except Exception:
            pass
    
    def add_event_item(self, event):
        """이벤트 아이템 추가 (클릭 가능)"""
        t = self.theme
        
        # 과거 일정 확인
        is_past = False
        time_str = ""
        try:
            end_str = event['end']
            if 'T' in end_str:
                # 시간 지정 일정
                end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                start_dt = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                time_str = start_dt.strftime("%H:%M")
                if end_dt < datetime.now().astimezone():
                    is_past = True
            else:
                # 종일 일정 (종료일은 exclusive이므로 오늘보다 작거나 같으면 지난 것)
                end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
                if end_date <= datetime.now().date():
                    is_past = True
                time_str = "종일"
        except Exception:
            pass
        
        # 스타일 색상 결정
        border_color = t['text_tertiary'] if is_past else t['accent']
        title_color = t['text_tertiary'] if is_past else t['text_primary']
        text_color = t['text_tertiary'] if is_past else t['text_secondary']
        
        # 배경색 기본값
        bg_color = t['card_background']
        bg_hover = t['elevated_background']
        if is_past:
            bg_hover = t['background']
        
        # 사용자 지정 색상 또는 구글 캘린더 색상 적용
        if not is_past:
            custom_color = event.get('customColor')
            color_id = event.get('colorId')
            if custom_color:
                border_color = custom_color
            elif color_id and color_id in self.event_colors_map:
                border_color = self.event_colors_map[color_id]
            
            # 배경색을 일정 색상의 연한 파스텔 톤(투명도 12%)으로 설정
            c = QColor(border_color)
            bg_color = f"rgba({c.red()}, {c.green()}, {c.blue()}, 0.12)"
            bg_hover = f"rgba({c.red()}, {c.green()}, {c.blue()}, 0.20)"

        # 클릭 가능한 프레임
        item_frame = ClickableEventFrame(event, self.calendar_api, self)
        
        # 세련된 카드 스타일 (왼쪽 테두리 제거, 내부 바 사용)
        # QFrame 대신 ClickableEventFrame 선택자 사용 (자식 위젯 영향 방지)
        item_frame.setStyleSheet(f"""
            ClickableEventFrame {{
                background-color: {bg_color};
                border-radius: 12px;
                margin-bottom: 6px;
            }}
            ClickableEventFrame:hover {{
                background-color: {bg_hover};
            }}
            /* 내부 라벨 배경 투명화 (검정 박스 제거) */
            QLabel {{
                background-color: transparent;
            }}
        """)
        
        # 가로 레이아웃 (시간 | 바 | 내용)
        item_layout = QHBoxLayout(item_frame)
        item_layout.setContentsMargins(15, 20, 15, 20)
        item_layout.setSpacing(15)
        
        # 1. 시간 표시 (왼쪽)
        time_label = QLabel(time_str)
        time_label.setFont(QFont("Malgun Gothic", 11, QFont.Bold))
        time_label.setStyleSheet(f"color: {text_color}; background-color: transparent;")
        time_label.setFixedWidth(50)  # 폰트 크기 증가에 따른 너비 조정
        time_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        item_layout.addWidget(time_label)
        
        # 2. 색상 바 (중앙)
        color_bar = QFrame()
        color_bar.setFixedWidth(3)
        color_bar.setStyleSheet(f"background-color: {border_color}; border-radius: 1.5px;")
        item_layout.addWidget(color_bar)
        
        # 3. 내용 (오른쪽)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 제목
        title_label = QLabel(event['summary'])
        title_label.setFont(QFont("Malgun Gothic", 12, QFont.Bold))
        title_label.setStyleSheet(f"color: {title_color}; background-color: transparent;")
        title_label.setWordWrap(True)
        content_layout.addWidget(title_label)
        
        # 위치 (있으면)
        if event.get('location'):
            location_label = QLabel(event['location'])
            location_label.setFont(QFont("Malgun Gothic", 8))
            location_label.setStyleSheet(f"color: {text_color}; background-color: transparent;")
            location_label.setWordWrap(True)
            content_layout.addWidget(location_label)
        
        item_layout.addLayout(content_layout)
        
        # 그림자 효과 추가
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 1)
        item_frame.setGraphicsEffect(shadow)
        
        self.events_layout.addWidget(item_frame)
    
    def refresh(self):
        """새로고침"""
        self.theme = theme.get_current_theme()
        
        # UI 배경색 업데이트
        self.events_widget.setStyleSheet(f"background-color: {self.theme['background']};")
        
        # 일정 다시 로드
        self.load_events()

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
