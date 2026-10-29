"""
iOS 캘린더 스타일 테마 시스템
"""

# iOS 라이트 테마
LIGHT_THEME = {
    # 배경
    'background': '#ffffff',           # 흰색 배경
    'card_background': '#f2f2f7',      # 카드 배경
    'elevated_background': '#fefefe',  # 살짝 높은 배경
    
    # 텍스트
    'text_primary': '#000000',         # 주요 텍스트
    'text_secondary': '#3c3c43',       # 보조 텍스트
    'text_tertiary': '#8e8e93',        # 3차 텍스트
    
    # 보더/구분선
    'border': '#e5e5ea',               # 일반 보더
    'separator': '#d1d1d6',            # 구분선
    
    # 입력 필드
    'input_background': '#ffffff',
    'input_border': '#e5e5ea',
    'input_text': '#000000',
    
    # 버튼
    'button_primary': '#007aff',       # iOS 파란색
    'button_secondary': '#f2f2f7',
    'button_text': '#000000',
    
    # 강조
    'accent': '#007aff',               # iOS 파란색
    'today': '#007aff',                # 오늘 날짜 배경
    'today_border': '#007aff',
    'today_glow': 'rgba(0, 122, 255, 0.3)',  # 파란 빛나는 효과
    
    # 그림자
    'shadow_color': 'rgba(0, 0, 0, 0.08)',
    'shadow_hover': 'rgba(0, 0, 0, 0.12)',
    
    # 요일 색상
    'sunday': '#ff3b30',               # iOS 빨간색
    'saturday': '#007aff',             # iOS 파란색
}

# iOS 다크 테마
DARK_THEME = {
    # 배경
    'background': '#121212',           # 다크 그레이
    'card_background': '#1c1c1e',      # 카드 배경
    'elevated_background': '#2c2c2e',  # 살짝 높은 배경
    
    # 텍스트
    'text_primary': '#ffffff',         # 주요 텍스트
    'text_secondary': '#ebebf5',       # 보조 텍스트
    'text_tertiary': '#8e8e93',        # 3차 텍스트
    
    # 보더/구분선
    'border': '#38383a',               # 일반 보더
    'separator': '#48484a',            # 구분선
    
    # 입력 필드
    'input_background': '#1c1c1e',
    'input_border': '#38383a',
    'input_text': '#ffffff',
    
    # 버튼
    'button_primary': '#0a84ff',       # iOS 다크 파란색
    'button_secondary': '#2c2c2e',
    'button_text': '#ffffff',
    
    # 강조
    'accent': '#0a84ff',               # iOS 다크 파란색
    'today': '#0a84ff',                # 오늘 날짜 배경
    'today_border': '#0a84ff',
    'today_glow': 'rgba(10, 132, 255, 0.5)',  # 파란 빛나는 효과
    
    # 그림자
    'shadow_color': 'rgba(0, 0, 0, 0.3)',
    'shadow_hover': 'rgba(0, 0, 0, 0.5)',
    
    # 요일 색상
    'sunday': '#ff453a',               # iOS 다크 빨간색
    'saturday': '#0a84ff',             # iOS 다크 파란색
}


def get_theme(theme_name='dark'):
    """
    테마 이름으로 테마 딕셔너리 반환
    
    Args:
        theme_name: 'light' 또는 'dark'
    
    Returns:
        테마 딕셔너리
    """
    if theme_name == 'light':
        return LIGHT_THEME
    else:
        return DARK_THEME


def get_current_theme():
    """
    현재 설정된 테마 반환
    
    Returns:
        테마 딕셔너리
    """
    import config
    theme_name = config.settings.get('theme', 'dark')
    return get_theme(theme_name)
