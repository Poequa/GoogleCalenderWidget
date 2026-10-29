"""
구글 캘린더 바탕화면 위젯
실행: py main.py
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from calendar_widget import CalendarWidget


def main():
    # 고해상도 디스플레이 지원
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 창 닫아도 종료 안 됨
    
    # 전역 폰트 설정 (모든 UI 통일)
    # 윈도우에서 한글이 깔끔하게 나오도록 맑은 고딕을 기본으로 설정
    font = QFont("Malgun Gothic", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    # 스타일시트로 폰트 스택 적용 (iOS 폰트 우선)
    app.setStyleSheet("QWidget { font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', 'Segoe UI', sans-serif; }")
    
    # 위젯 생성 및 표시
    widget = CalendarWidget()
    widget.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
