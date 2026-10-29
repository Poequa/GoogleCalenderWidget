# 구글 캘린더 바탕화면 위젯

윈도우 바탕화면에 항상 표시되는 구글 캘린더 위젯입니다.

## 🎉 주요 기능

### ✨ 핵심 기능
- ✅ **바탕화면 고정** - Rainmeter 방식으로 바탕화면 레이어에 고정
- ✅ **Google Calendar API 연동** - 실시간 일정 동기화
- ✅ **두 가지 보기 모드**
  - 📋 **목록 보기** - 일정을 리스트 형태로 표시
  - 📅 **달력 보기** - 월별 캘린더 형태로 표시
- ✅ **자동 날짜 범위 필터링** - 설정한 기간 내 일정만 표시
- ✅ **드래그로 위치 이동** - 원하는 위치에 배치
- ✅ **자동 새로고침** - 설정한 주기마다 자동 업데이트

### ⚙️ 설정 기능
- **표시 기간** - 7일 ~ 365일 (기본: 30일)
- **최대 일정 수** - 5 ~ 50개 (기본: 10개)
- **업데이트 주기** - 1 ~ 60분 (기본: 5분)
- **기본 화면** - 목록/달력 선택
- **위젯 크기** - 너비/높이 조절
- **투명도** - 50% ~ 100%
- **색상 테마** - 다크/라이트/블루/그린

## 🚀 설치 방법

### 1. Python 설치
Python 3.8 이상 필요
- [Python 다운로드](https://www.python.org/downloads/)
- ⚠️ 설치 시 **"Add Python to PATH"** 체크!

### 2. 필요 라이브러리 설치

```bash
cd E:\Project\GoogleCalenderWidget
py -m pip install -r requirements.txt
```

### 3. Google Calendar API 설정

#### 3.1 Google Cloud Console 설정
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 (예: "Calendar Widget")
3. **API 및 서비스 > 라이브러리** 이동
4. "Google Calendar API" 검색 후 **사용 설정**
5. **OAuth 동의 화면** 설정
   - 사용자 유형: **외부**
   - 앱 이름, 이메일 입력
   - 범위 추가: `.../auth/calendar.readonly`
6. **사용자 인증 정보 > OAuth 클라이언트 ID 만들기**
7. 애플리케이션 유형: **데스크톱 앱**
8. **JSON 다운로드**

#### 3.2 테스트 사용자 추가 (중요!)
1. **OAuth 동의 화면** 으로 이동
2. **테스트 사용자** 섹션에서 **+ 사용자 추가**
3. 본인 Gmail 주소 입력
4. 저장

#### 3.3 인증 파일 저장
- 다운로드한 JSON 파일을 **`credentials.json`** 으로 이름 변경
- 프로젝트 폴더가 아니라 아래 로컬 폴더에 저장

```
%LOCALAPPDATA%\GoogleCalendarWidget\credentials.json
```

윈도우에서는 보통 다음 경로입니다.

```
C:\Users\사용자명\AppData\Local\GoogleCalendarWidget\credentials.json
```

`token.json`과 `settings.json`도 프로그램이 이 폴더에 자동으로 만듭니다. 이 세 파일에는 계정 정보가 있으므로 GitHub에 올리지 않습니다.

## ▶️ 실행 방법

```bash
cd E:\Project\GoogleCalenderWidget
py main.py
```

**첫 실행 시:**
1. 브라우저가 자동으로 열림
2. Google 계정으로 로그인
3. "Google에서 확인하지 않은 앱" 경고 → **"계속"** 클릭
4. 캘린더 읽기 권한 허용
5. 인증 완료 후 위젯 실행!

## 🎨 사용 방법

### 화면 전환
- **📋 목록** 탭: 일정을 리스트로 보기
- **📅 달력** 탭: 월별 캘린더로 보기
  - ◀/▶ 버튼으로 이전/다음 달 이동
  - 📅 오늘 버튼으로 현재 월로 이동

### 버튼 기능
- **⚙️ 설정**: 위젯 설정 변경
- **🔄 새로고침**: 즉시 일정 업데이트

### 위치 이동
- 위젯을 **드래그**하여 원하는 위치로 이동
- 위치는 자동으로 저장됨

## ⚙️ 설정 항목

### 📊 표시 설정
- **표시 기간**: 앞으로 N일 이내 일정만 표시 (반복 일정 필터링)
- **최대 일정 수**: 한 번에 표시할 일정 개수
- **업데이트 주기**: 자동 새로고침 간격
- **기본 화면**: 시작 시 보여줄 화면 (목록/달력)

### 📐 위젯 크기
- **너비**: 300 ~ 800 px
- **높이**: 400 ~ 1000 px
- **투명도**: 50% ~ 100%

### 🎨 테마
- **🌙 다크** - 어두운 배경 (기본)
- **☀️ 라이트** - 밝은 배경
- **🔵 블루** - 파란색 테마
- **🟢 그린** - 초록색 테마

## 🔧 윈도우 시작 시 자동 실행

### 방법 1: 시작 프로그램 폴더

1. `Win + R` → `shell:startup` 입력
2. 바로가기 만들기:
   ```
   대상: C:\Users\사용자명\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe "E:\Project\GoogleCalenderWidget\main.py"
   시작 위치: E:\Project\GoogleCalenderWidget
   ```

### 방법 2: bat 파일 생성

`start_widget.bat` 생성:
```batch
@echo off
cd /d E:\Project\GoogleCalenderWidget
pythonw.exe main.py
```

시작 프로그램 폴더에 이 bat 파일 바로가기 복사

## 📦 EXE 파일로 변환 (선택사항)

다른 사람에게 배포하거나 Python 없이 실행하려면:

```bash
py -m pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico main.py
```

생성된 `dist/main.exe` 실행

## ❗ 문제 해결

### "credentials.json 파일이 필요합니다" 오류
→ Google Cloud Console에서 OAuth 2.0 인증 파일 다운로드 필요

### "액세스 차단됨" 오류
→ OAuth 동의 화면에서 **테스트 사용자**에 본인 이메일 추가 필요

### "Google Calendar API has not been used" 오류
→ Google Cloud Console에서 **Google Calendar API** 활성화 필요

### 바탕화면에 고정되지 않음
→ 일반 창으로 표시됨 (Win32 API 권한 문제 가능)
→ 여전히 사용 가능하며 드래그로 이동 가능

### 일정이 표시되지 않음
→ Google Calendar에 일정이 있는지 확인
→ 설정에서 **표시 기간** 확인 (기본: 30일)

### 생일 같은 반복 일정이 계속 표시됨
→ 설정(⚙️)에서 **표시 기간**을 조절하세요
→ 설정한 기간 내의 일정만 표시됩니다

## 📝 파일 구조

```
GoogleCalenderWidget/          ← 이 폴더만 GitHub에 올린다
├── main.py                    # 메인 실행 파일
├── calendar_widget.py         # 메인 위젯 (탭 전환)
├── list_view.py               # 목록 뷰
├── calendar_view.py           # 달력 뷰
├── settings_dialog.py         # 설정 다이얼로그
├── google_calendar_api.py     # Google API 연동
├── config.py                  # 설정 관리
├── requirements.txt           # 필요 라이브러리
├── credentials.json.example   # 인증 파일 예시 (비밀 없음)
└── README.md                  # 이 파일

%LOCALAPPDATA%\GoogleCalendarWidget\   ← 올리지 않는 로컬 파일
├── credentials.json           # Google OAuth
├── token.json                 # 인증 토큰 (자동 생성)
└── settings.json              # 사용자 설정 (자동 생성)
```

## GitHub 웹에 올리기

이 프로젝트 폴더에는 계정 정보가 없습니다. GitHub 웹사이트에서 파일을 그대로 올려도 됩니다.

올리면 안 되는 파일은 프로젝트 밖 `%LOCALAPPDATA%\GoogleCalendarWidget`에 있습니다. 예전에 프로젝트 폴더에 두었다면, 프로그램을 한 번 실행하면 그쪽으로 옮겨집니다.

## 🎯 테스트 모드 vs 프로덕션 모드

### 현재: 테스트 모드
- ✅ 100명까지 사용 가능
- ✅ 개발 및 테스트용
- ✅ 테스트 사용자 추가 필요

### 나중에: 프로덕션 모드 (선택)
- 📝 개인정보 처리방침 작성
- 📸 스크린샷 준비
- 📮 Google 검증 신청
- ⏰ 2-6주 검토 대기
- ✅ 승인 후 무제한 사용자

**현재 credentials.json 그대로 사용 가능!**

## 🎨 사용 팁

- **드래그**: 위젯을 원하는 위치로 이동
- **⚙️ 설정**: 날짜 범위, 테마, 크기 등 커스터마이징
- **탭 전환**: 목록/달력 보기 자유롭게 전환
- **달력 뷰**: 이전/다음 달 버튼으로 탐색
- **자동 업데이트**: 설정한 주기마다 자동 새로고침

## 📄 라이선스

MIT License - 자유롭게 사용 및 수정 가능

## 🤝 기여

버그 리포트나 기능 제안은 Issue로 등록해주세요!

---

Made with ❤️ by Hyun
