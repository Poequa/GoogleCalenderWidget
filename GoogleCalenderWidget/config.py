"""
구글 캘린더 위젯 설정
"""
import json
import os
import shutil
from pathlib import Path

# 프로젝트 루트 디렉토리 (GitHub에 올리는 코드만 둔다)
BASE_DIR = Path(__file__).parent

# 인증 정보와 개인 설정은 프로젝트 밖에 둔다.
# GitHub 웹에서 이 폴더를 통째로 올려도 계정 정보가 포함되지 않는다.
def _data_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_app_data) if local_app_data else Path.home()
    path = root / "GoogleCalendarWidget"
    path.mkdir(parents=True, exist_ok=True)
    return path


DATA_DIR = _data_dir()


def _move_private_file_out_of_project(name: str) -> None:
    """예전에 프로젝트 폴더에 있던 비밀 파일을 로컬 데이터 폴더로 옮긴다."""
    source = BASE_DIR / name
    destination = DATA_DIR / name
    if not source.exists() or source.resolve() == destination.resolve():
        return
    if destination.exists():
        source.unlink()
        return
    shutil.move(str(source), str(destination))


for _private_name in ("credentials.json", "token.json", "settings.json"):
    _move_private_file_out_of_project(_private_name)

# Google Calendar API 설정
SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_PATH = DATA_DIR / 'token.json'
CREDENTIALS_PATH = DATA_DIR / 'credentials.json'

# 사용자 설정 파일
SETTINGS_PATH = DATA_DIR / 'settings.json'

# 기본 설정값
DEFAULT_SETTINGS = {
    'widget_width': 1000,
    'widget_height': 900,
    'widget_opacity': 0.9,
    'widget_position_x': 50,
    'widget_position_y': 50,
    'update_interval': 5,
    'max_events': 10,
    'date_range_days': 30,
    'theme': 'dark',
    'default_view': 'calendar',
    'selected_calendars': ['primary'],  # 선택된 캘린더 ID 목록 (기본값: 내 캘린더)
}

# 테마 색상
THEMES = {
    'dark': {
        'background': '#2b2b2b',  # 다크 그레이 배경 (원래대로)
        'text': '#ffffff',
        'accent': '#4285f4',
        'card_bg': '#3a3a3a',
        'header_bg': '#1e1e1e',
    },
    'light': {
        'background': '#f5f5f5',  # 라이트 그레이 배경 (원래대로)
        'text': '#333333',
        'accent': '#4285f4',
        'card_bg': '#ffffff',
        'header_bg': '#e0e0e0',
    },
}


class Settings:
    """설정 관리 클래스"""
    
    def __init__(self):
        self.settings = self.load_settings()
    
    def load_settings(self):
        """설정 파일 로드"""
        if SETTINGS_PATH.exists():
            try:
                with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    # 기본값과 병합
                    settings = DEFAULT_SETTINGS.copy()
                    settings.update(saved_settings)
                    return settings
            except Exception as e:
                print(f"설정 로드 실패: {e}")
                return DEFAULT_SETTINGS.copy()
        return DEFAULT_SETTINGS.copy()
    
    def save_settings(self):
        """설정 파일 저장"""
        try:
            with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"설정 저장 실패: {e}")
    
    def get(self, key, default=None):
        """설정 값 가져오기"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """설정 값 변경"""
        self.settings[key] = value
        self.save_settings()
    
    def get_theme_colors(self):
        """현재 테마의 색상 가져오기"""
        theme_name = self.get('theme', 'dark')
        return THEMES.get(theme_name, THEMES['dark'])


# 전역 설정 인스턴스
settings = Settings()
