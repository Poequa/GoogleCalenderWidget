"""
Google Calendar API 연동
"""
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config


class GoogleCalendarAPI:
    def __init__(self):
        self.creds = None
        self.service = None
        
    def authenticate(self):
        """Google Calendar API 인증"""
        # 토큰 파일이 있으면 로드
        if config.TOKEN_PATH.exists():
            self.creds = Credentials.from_authorized_user_file(
                str(config.TOKEN_PATH), config.SCOPES
            )
        
        # 유효하지 않은 토큰이면 갱신 또는 새로 로그인
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not config.CREDENTIALS_PATH.exists():
                    raise FileNotFoundError(
                        f"credentials.json 파일이 필요합니다.\n"
                        f"Google Cloud Console에서 다운로드하여 {config.CREDENTIALS_PATH}에 저장하세요."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(config.CREDENTIALS_PATH), config.SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # 토큰 저장
            with open(config.TOKEN_PATH, 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=self.creds)
        return True
    
    def get_calendar_list(self):
        """사용 가능한 캘린더 목록 가져오기"""
        try:
            if not self.service:
                self.authenticate()
            
            calendar_list = []
            page_token = None
            while True:
                calendar_list_entry = self.service.calendarList().list(pageToken=page_token).execute()
                for entry in calendar_list_entry['items']:
                    calendar_list.append(entry)
                page_token = calendar_list_entry.get('nextPageToken')
                if not page_token:
                    break
            return calendar_list
        except Exception as e:
            print(f"캘린더 목록 조회 실패: {e}")
            return []

    def get_upcoming_events(self, max_results=10, days_ahead=None):
        """다가오는 일정 가져오기
        
        Args:
            max_results: 최대 결과 개수
            days_ahead: 앞으로 N일 이내 일정만 (None이면 제한 없음)
        """
        try:
            # 현재 시간
            now = datetime.datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            
            # 종료 시간 설정
            if days_ahead:
                time_max = (now + datetime.timedelta(days=days_ahead)).isoformat() + 'Z'
            else:
                time_max = None
            
            # API 요청 파라미터
            params = {
                'timeMin': time_min,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            if time_max:
                params['timeMax'] = time_max
            
            # 선택된 캘린더들에서 이벤트 조회
            calendar_ids = config.settings.get('selected_calendars', ['primary'])
            all_events = []

            for cal_id in calendar_ids:
                try:
                    params['calendarId'] = cal_id
                    events_result = self.service.events().list(**params).execute()
                    events = events_result.get('items', [])
                    all_events.extend(events)
                except Exception as e:
                    print(f"캘린더({cal_id}) 일정 조회 실패: {e}")
            
            # 이벤트 정보 포맷팅
            formatted_events = []
            for event in all_events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                formatted_events.append({
                    'calendar_id': event.get('organizer', {}).get('email', 'unknown'), # 출처 캘린더
                    'summary': event.get('summary', '(제목 없음)'),
                    'start': start,
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'colorId': event.get('colorId'),
                    'customColor': event.get('extendedProperties', {}).get('private', {}).get('customColor')
                })
            
            # 시간순 정렬 및 개수 제한
            formatted_events.sort(key=lambda x: x['start'])
            return formatted_events[:max_results]
            
        except HttpError as error:
            print(f'API 오류 발생: {error}')
            return []
    
    def get_events_for_month(self, year, month):
        """특정 월의 모든 일정 가져오기
        
        Args:
            year: 연도
            month: 월 (1-12)
        """
        try:
            # 해당 월의 시작일과 마지막 날
            start_date = datetime.datetime(year, month, 1)
            
            if month == 12:
                end_date = datetime.datetime(year + 1, 1, 1)
            else:
                end_date = datetime.datetime(year, month + 1, 1)
            
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            # 선택된 캘린더들에서 이벤트 조회
            calendar_ids = config.settings.get('selected_calendars', ['primary'])
            all_events = []

            for cal_id in calendar_ids:
                try:
                    events_result = self.service.events().list(
                        calendarId=cal_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    all_events.extend(events_result.get('items', []))
                except Exception as e:
                    print(f"캘린더({cal_id}) 월별 조회 실패: {e}")
            
            # 날짜별로 그룹화
            events_by_date = {}
            for event in all_events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                
                # 날짜만 추출 (YYYY-MM-DD)
                if 'T' in start:
                    date_key = start.split('T')[0]
                else:
                    date_key = start
                
                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                
                events_by_date[date_key].append({
                    'calendar_id': event.get('organizer', {}).get('email', 'unknown'),
                    'id': event.get('id'),  # 이벤트 ID 추가
                    'summary': event.get('summary', '(제목 없음)'),
                    'start': start,
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'colorId': event.get('colorId'),
                    'customColor': event.get('extendedProperties', {}).get('private', {}).get('customColor')
                })
            
            return events_by_date
            
        except HttpError as error:
            print(f'API 오류 발생: {error}')
            return {}
    
    def format_datetime(self, datetime_str):
        """날짜/시간 포맷팅"""
        try:
            # ISO 8601 형식 파싱
            if 'T' in datetime_str:
                # 날짜와 시간 포함
                dt = datetime.datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                return dt.strftime('%m/%d (%a) %H:%M')
            else:
                # 날짜만
                dt = datetime.datetime.fromisoformat(datetime_str)
                return dt.strftime('%m/%d (%a) 종일')
        except Exception as e:
            return datetime_str
    
    def create_event(self, summary, start_datetime, end_datetime, description='', location='', is_all_day=False, color_id=None, custom_color=None):
        """일정 생성"""
        try:
            if not self.service:
                print('오류: Google Calendar 서비스가 초기화되지 않았습니다.')
                return None
            
            event = {
                'summary': summary,
                'description': description,
                'location': location,
            }
            
            if color_id:
                event['colorId'] = color_id
            
            if custom_color:
                event['extendedProperties'] = {
                    'private': {'customColor': custom_color}
                }
            
            # 종일 이벤트 여부에 따라 형식 다르게
            if is_all_day:
                # 종일 이벤트: 날짜만 (YYYY-MM-DD)
                event['start'] = {'date': start_datetime}
                event['end'] = {'date': end_datetime}
                print(f'종일 이벤트 생성 시도: {start_datetime} ~ {end_datetime}')
            else:
                # 시간 지정 이벤트: ISO 8601 형식
                event['start'] = {'dateTime': start_datetime, 'timeZone': 'Asia/Seoul'}
                event['end'] = {'dateTime': end_datetime, 'timeZone': 'Asia/Seoul'}
                print(f'시간 이벤트 생성 시도: {start_datetime} ~ {end_datetime}')
            
            print(f'일정 데이터: {event}')
            
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            print(f'✅ 일정 생성 성공: {created_event.get("htmlLink")}')
            return created_event
            
        except HttpError as error:
            print(f'❌ 일정 생성 오류 (HttpError): {error}')
            print(f'오류 상세: {error.content}')
            return None
        except Exception as e:
            print(f'❌ 일정 생성 오류 (Exception): {e}')
            import traceback
            traceback.print_exc()
            return None
    
    def update_event(self, event_id, summary=None, start_datetime=None, end_datetime=None, 
                    description=None, location=None, is_all_day=False, color_id=None, custom_color=None):
        """일정 수정"""
        try:
            if not self.service:
                return None
            
            # 기존 일정 가져오기
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # 수정할 필드만 업데이트
            if summary is not None:
                event['summary'] = summary
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location
            if color_id is not None:
                if color_id == "":
                    # 기본 색상 선택 시 colorId 필드 제거
                    event.pop('colorId', None)
                else:
                    event['colorId'] = color_id
            
            # 사용자 지정 색상 처리 (빈 문자열이면 삭제)
            if custom_color is not None:
                if custom_color:
                    # 색상 설정
                    if 'extendedProperties' not in event:
                        event['extendedProperties'] = {'private': {}}
                    if 'private' not in event['extendedProperties']:
                        event['extendedProperties']['private'] = {}
                    event['extendedProperties']['private']['customColor'] = custom_color
                elif 'extendedProperties' in event and 'private' in event['extendedProperties']:
                    # 색상 삭제 (키 제거)
                    event['extendedProperties']['private'].pop('customColor', None)
            
            if start_datetime and end_datetime:
                if is_all_day:
                    event['start'] = {'date': start_datetime}
                    event['end'] = {'date': end_datetime}
                else:
                    event['start'] = {'dateTime': start_datetime, 'timeZone': 'Asia/Seoul'}
                    event['end'] = {'dateTime': end_datetime, 'timeZone': 'Asia/Seoul'}
            
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            print(f'일정 수정됨: {updated_event.get("htmlLink")}')
            return updated_event
            
        except HttpError as error:
            print(f'일정 수정 오류: {error}')
            return None
    
    def delete_event(self, event_id):
        """일정 삭제"""
        try:
            if not self.service:
                return False
            
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            print(f'일정 삭제됨: {event_id}')
            return True
            
        except HttpError as error:
            print(f'일정 삭제 오류: {error}')
            return False

    def get_colors(self):
        """캘린더 및 이벤트 색상 정보 가져오기"""
        try:
            if not self.service:
                self.authenticate()
            
            return self.service.colors().get().execute()
        except Exception as e:
            print(f"색상 정보 조회 실패: {e}")
            return {}

    def get_calendar_color(self, calendar_id='primary'):
        """특정 캘린더의 배경색 가져오기"""
        try:
            # 캘린더 목록에서 해당 캘린더 찾기
            calendar_list = self.get_calendar_list()
            for cal in calendar_list:
                if cal['id'] == calendar_id:
                    return cal.get('backgroundColor', '#4285f4')
            
            return '#4285f4'  # 기본값 (Google Blue)
        except Exception as e:
            print(f"캘린더 색상 조회 실패: {e}")
            return '#4285f4'
