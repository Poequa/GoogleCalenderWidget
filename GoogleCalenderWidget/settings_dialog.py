"""
iOS 스타일 설정 다이얼로그
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QSpinBox, QSlider, QComboBox, QPushButton,
                            QGroupBox, QFormLayout, QMessageBox, QGraphicsDropShadowEffect,
                            QScrollArea, QWidget, QFrame, QCheckBox,
                            QScroller, QScrollerProperties)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QRegion, QPainterPath
import config
import theme


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


class SettingsDialog(QDialog):
    def __init__(self, calendar_api, parent=None):
        super().__init__(parent)
        self.calendar_api = calendar_api
        # 타이틀바 제거
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setMinimumWidth(550)
        self.resize(550, 700)
        
        # 드래그 위한 변수
        self.dragging = False
        self.drag_position = None
        
        # 현재 설정 로드
        self.settings = config.settings
        
        # 현재 테마 가져오기
        self.theme = theme.get_current_theme()
        
        # 테마 적용
        self.apply_theme()
        
        self.init_ui()
        
        # 현재 설정된 투명도 적용
        current_opacity = self.settings.get('widget_opacity', 0.9)
        target_opacity = 1.0 if current_opacity >= 1.0 else 0.95
        self.setWindowOpacity(0.0)
        
        # 등장 애니메이션
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(target_opacity)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()
        
        # 다이얼로그 전체에 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)
    
    def apply_theme(self):
        """iOS 스타일 테마 적용"""
        t = self.theme
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {t['card_background']};
                border-radius: 20px;
            }}
            QLabel {{
                color: {t['text_primary']};
                font-size: 11pt;
            }}
            QGroupBox {{
                color: {t['text_primary']};
                font-weight: 600;
                font-size: 12pt;
                border: none;
                border-radius: 16px;
                margin-top: 15px;
                padding-top: 25px;
                background-color: {t['card_background']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                padding: 5px 10px;
                background-color: {t['card_background']};
                color: {t['text_primary']};
                border-radius: 8px;
            }}
            
            /* CheckBox - iOS Style (Rounded Selection) */
            QCheckBox {{
                spacing: 8px;
                color: {t['text_primary']};
                font-size: 11pt;
                font-weight: 500;
                margin-bottom: 4px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border-radius: 7px;
                border: 1.5px solid {t['text_tertiary']};
                background-color: {t['input_background']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {t['accent']};
                border: 1.5px solid {t['accent']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {t['text_secondary']};
                background-color: {t['elevated_background']};
            }}
            
            /* SpinBox - iOS 스타일 */
            QSpinBox {{
                background-color: {t['input_background']};
                color: {t['input_text']};
                border: 1px solid {t['input_border']};
                border-radius: 10px;
                padding: 10px 12px;
                font-size: 11pt;
                font-weight: 500;
            }}
            QSpinBox:hover {{
                border: 2px solid {t['accent']};
                background-color: {t['elevated_background']};
            }}
            QSpinBox:focus {{
                border: 2px solid {t['accent']};
                background-color: {t['elevated_background']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 0px;
                border: none;
            }}
            
            /* ComboBox - iOS 스타일 */
            QComboBox {{
                background-color: {t['input_background']};
                color: {t['input_text']};
                border: 1px solid {t['input_border']};
                border-radius: 10px;
                padding: 10px 12px;
                padding-right: 35px;
                font-size: 11pt;
                font-weight: 500;
            }}
            QComboBox:hover {{
                border: 2px solid {t['accent']};
                background-color: {t['elevated_background']};
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
                border-top-right-radius: 9px;
                border-bottom-right-radius: 9px;
            }}
            QComboBox::drop-down:hover {{
                background-color: {t['elevated_background']};
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid {t['text_primary']};
                width: 0px;
                height: 0px;
            }}
            
            /* ComboBox 드롭다운 메뉴 */
            QComboBox QAbstractItemView {{
                background-color: {t['card_background']};
                color: {t['text_primary']};
                selection-background-color: {t['accent']};
                selection-color: white;
                border: 1px solid {t['border']};
                border-radius: 12px;
                outline: none;
                padding: 5px;
            }}
            QComboBox QAbstractItemView::item {{
                color: {t['text_primary']};
                background-color: {t['card_background']};
                padding: 12px 15px;
                min-height: 35px;
                border-radius: 8px;
                margin: 2px 5px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {t['elevated_background']};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {t['accent']};
                color: white;
            }}
            
            /* Slider - iOS 스타일 */
            QSlider::groove:horizontal {{
                border: none;
                height: 6px;
                background: {t['separator']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: white;
                border: 2px solid {t['accent']};
                width: 24px;
                height: 24px;
                margin: -10px 0;
                border-radius: 12px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {t['elevated_background']};
            }}
            QSlider::sub-page:horizontal {{
                background: {t['accent']};
                border-radius: 3px;
            }}
        """)
    
    def init_ui(self):
        """UI 초기화"""
        t = self.theme
        
        # 메인 레이아웃 (여백 없음)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. 상단 타이틀 영역 (고정)
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(25, 25, 25, 10)
        
        title_label = QLabel("⚙️ 위젯 설정")
        title_label.setFont(QFont("Malgun Gothic", 18, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.theme['text_primary']}; margin-bottom: 5px;")
        title_layout.addWidget(title_label)
        
        main_layout.addWidget(title_widget)
        
        # 2. 스크롤 영역 (설정 항목들)
        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        
        # 스크롤바 스타일링
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
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
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(25, 10, 25, 10)
        
        # 설정 그룹들 추가
        display_group = self.create_display_settings()
        content_layout.addWidget(display_group)
        
        calendar_group = self.create_calendar_settings()
        content_layout.addWidget(calendar_group)
        
        size_group = self.create_size_settings()
        content_layout.addWidget(size_group)
        
        theme_group = self.create_theme_settings()
        content_layout.addWidget(theme_group)
        
        content_layout.addStretch()
        
        self.scroll.setWidget(content_widget)
        main_layout.addWidget(self.scroll)
        
        # 3. 하단 버튼 영역 (고정)
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(25, 10, 25, 25)
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumHeight(45)
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['button_secondary']};
                color: {self.theme['text_primary']};
                border: 1px solid {self.theme['border']};
                padding: 12px 25px;
                border-radius: 12px;
                font-weight: 600;
                font-size: 12pt;
            }}
            QPushButton:hover {{
                background-color: {self.theme['elevated_background']};
                border: 2px solid {self.theme['border']};
            }}
            QPushButton:pressed {{
                background-color: {self.theme['separator']};
            }}
        """)
        
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setMinimumHeight(45)
        save_btn.setMinimumWidth(120)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-weight: 600;
                font-size: 12pt;
            }}
            QPushButton:hover {{
                background-color: {self.theme['button_primary']};
            }}
            QPushButton:pressed {{
                background-color: {self.theme['today']};
            }}
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        main_layout.addWidget(button_widget)
        
        # 초기 둥근 모서리 적용
        self.apply_rounded_corners()
    
    def create_display_settings(self):
        """표시 설정 그룹 - iOS 스타일"""
        group = QGroupBox("📊 표시 설정")
        form = QFormLayout()
        form.setSpacing(15)
        form.setContentsMargins(20, 25, 20, 20)
        form.setLabelAlignment(Qt.AlignLeft)
        
        # 날짜 범위
        self.date_range_spin = QSpinBox()
        self.date_range_spin.setRange(7, 365)
        self.date_range_spin.setValue(self.settings.get('date_range_days', 30))
        self.date_range_spin.setSuffix(" 일")
        self.date_range_spin.setMinimumHeight(45)
        
        date_label = QLabel("표시 기간")
        date_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-weight: 500; font-size: 11pt;")
        form.addRow(date_label, self.date_range_spin)
        
        # 최대 이벤트 수
        self.max_events_spin = QSpinBox()
        self.max_events_spin.setRange(5, 50)
        self.max_events_spin.setValue(self.settings.get('max_events', 10))
        self.max_events_spin.setSuffix(" 개")
        self.max_events_spin.setMinimumHeight(45)
        
        max_label = QLabel("최대 일정 수")
        max_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-weight: 500; font-size: 11pt;")
        form.addRow(max_label, self.max_events_spin)
        
        # 업데이트 주기
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(1, 60)
        self.update_interval_spin.setValue(self.settings.get('update_interval', 5))
        self.update_interval_spin.setSuffix(" 분")
        self.update_interval_spin.setMinimumHeight(45)
        
        update_label = QLabel("업데이트 주기")
        update_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-weight: 500; font-size: 11pt;")
        form.addRow(update_label, self.update_interval_spin)
        
        # 기본 뷰
        self.default_view_combo = QComboBox()
        self.default_view_combo.addItems(["📋 목록 보기", "📅 달력 보기"])
        self.default_view_combo.setMinimumHeight(45)
        if self.settings.get('default_view') == 'calendar':
            self.default_view_combo.setCurrentIndex(1)
        
        view_label = QLabel("기본 화면")
        view_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-weight: 500; font-size: 11pt;")
        form.addRow(view_label, self.default_view_combo)
        
        group.setLayout(form)
        
        # 그룹박스에 그림자 추가 - 간단하게
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        group.setGraphicsEffect(shadow)
        
        return group
    
    def create_calendar_settings(self):
        """캘린더 선택 설정 그룹"""
        group = QGroupBox("📅 캘린더 선택")
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 25, 15, 15)
        
        # 스크롤 영역 생성
        scroll = SmoothScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)
        
        # API에서 캘린더 목록 가져오기
        calendars = self.calendar_api.get_calendar_list()
        selected_ids = self.settings.get('selected_calendars', ['primary'])
        
        self.calendar_checkboxes = []
        
        for cal in calendars:
            cb = QCheckBox(cal.get('summary', '알 수 없는 캘린더'))
            cal_id = cal.get('id')
            cb.setProperty('calendar_id', cal_id)
            cb.setCursor(Qt.PointingHandCursor)
            
            # 체크 상태 설정
            if cal_id in selected_ids or (cal.get('primary') and 'primary' in selected_ids):
                cb.setChecked(True)
            
            self.calendar_checkboxes.append(cb)
            content_layout.addWidget(cb)
            
        scroll.setWidget(content_widget)
        scroll.setMinimumHeight(120)
        
        layout.addWidget(scroll)
        group.setLayout(layout)
        return group
    
    def create_size_settings(self):
        """크기 설정 그룹 - iOS 스타일"""
        group = QGroupBox("📐 위젯 크기")
        form = QFormLayout()
        form.setSpacing(15)
        form.setContentsMargins(20, 25, 20, 20)
        
        # 너비
        self.width_spin = QSpinBox()
        self.width_spin.setRange(350, 1500)
        self.width_spin.setValue(self.settings.get('widget_width', 1000))
        self.width_spin.setSuffix(" px")
        self.width_spin.setMinimumHeight(45)
        
        width_label = QLabel("너비")
        width_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-weight: 500; font-size: 11pt;")
        form.addRow(width_label, self.width_spin)
        
        # 높이
        self.height_spin = QSpinBox()
        self.height_spin.setRange(450, 1500)
        self.height_spin.setValue(self.settings.get('widget_height', 900))
        self.height_spin.setSuffix(" px")
        self.height_spin.setMinimumHeight(45)
        
        height_label = QLabel("높이")
        height_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-weight: 500; font-size: 11pt;")
        form.addRow(height_label, self.height_spin)
        
        # 투명도
        opacity_layout = QHBoxLayout()
        opacity_layout.setSpacing(15)
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setValue(int(self.settings.get('widget_opacity', 0.9) * 100))
        self.opacity_slider.setMinimumHeight(30)
        
        self.opacity_label = QLabel(f"{self.opacity_slider.value()}%")
        self.opacity_label.setStyleSheet(f"""
            color: {self.theme['accent']}; 
            font-weight: 700; 
            font-size: 13pt;
            min-width: 55px;
        """)
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        
        opacity_main_label = QLabel("투명도")
        opacity_main_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-weight: 500; font-size: 11pt;")
        form.addRow(opacity_main_label, opacity_layout)
        
        group.setLayout(form)
        
        # 그룹박스에 그림자 추가 - 간단하게
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        group.setGraphicsEffect(shadow)
        
        return group
    
    def create_theme_settings(self):
        """테마 설정 그룹 - iOS 스타일"""
        group = QGroupBox("🎨 테마")
        form = QFormLayout()
        form.setSpacing(15)
        form.setContentsMargins(20, 25, 20, 20)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "🌙 다크 모드",
            "☀️ 라이트 모드"
        ])
        self.theme_combo.setMinimumHeight(45)
        
        # 현재 테마 선택
        theme_map = {'dark': 0, 'light': 1}
        current_theme_name = self.settings.get('theme', 'dark')
        self.theme_combo.setCurrentIndex(theme_map.get(current_theme_name, 0))
        
        theme_label = QLabel("색상 테마")
        theme_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-weight: 500; font-size: 11pt;")
        form.addRow(theme_label, self.theme_combo)
        
        group.setLayout(form)
        
        # 그룹박스에 그림자 추가 - 간단하게
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        group.setGraphicsEffect(shadow)
        
        return group
    
    def update_opacity(self, value):
        """투명도 슬라이더 변경 시 실시간 적용"""
        self.opacity_label.setText(f"{value}%")
        # 100%일 때만 완전 불투명(1.0), 그 외에는 95% 고정
        self.setWindowOpacity(1.0 if value >= 100 else 0.95)
    
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
            
    def apply_rounded_corners(self):
        """둥근 모서리 적용"""
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def resizeEvent(self, event):
        """크기 변경 시 마스크 업데이트"""
        self.apply_rounded_corners()
        super().resizeEvent(event)
    
    def apply_message_box_style(self, msg):
        """메시지 박스에 iOS 스타일 적용"""
        msg.setWindowFlags(msg.windowFlags() | Qt.FramelessWindowHint)
        msg.setFont(QFont("Malgun Gothic", 10))
        
        # 투명도 설정
        current_opacity = self.settings.get('widget_opacity', 0.9)
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
    
    def save_settings(self):
        """설정 저장"""
        # 테마 매핑
        theme_names = ['dark', 'light']
        
        # 설정 업데이트
        self.settings.set('date_range_days', self.date_range_spin.value())
        self.settings.set('max_events', self.max_events_spin.value())
        self.settings.set('update_interval', self.update_interval_spin.value())
        self.settings.set('default_view', 
                         'calendar' if self.default_view_combo.currentIndex() == 1 else 'list')
        self.settings.set('widget_width', self.width_spin.value())
        self.settings.set('widget_height', self.height_spin.value())
        self.settings.set('widget_opacity', self.opacity_slider.value() / 100)
        self.settings.set('theme', theme_names[self.theme_combo.currentIndex()])
        
        # 선택된 캘린더 저장
        selected_calendars = []
        for cb in self.calendar_checkboxes:
            if cb.isChecked():
                selected_calendars.append(cb.property('calendar_id'))
        self.settings.set('selected_calendars', selected_calendars)
        
        self.accept()
