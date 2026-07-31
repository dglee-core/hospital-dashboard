# =====================================================================
# [1단계] 필요한 도구(라이브러리) 불러오기
# =====================================================================
import streamlit as st          # 🎈 웹사이트 화면을 구성하는 핵심 UI 도구
import gspread                  # 📊 구글 클라우드 시트와 연동하기 위한 도구
import pandas as pd             # 🐼 데이터를 표 형태로 정리하고 가공하는 도구
import plotly.graph_objects as go        # 📈 동적이고 예쁜 인터랙티브 그래프를 만드는 도구
from plotly.subplots import make_subplots # ⚖️ 하나의 그래프에 양쪽 Y축(막대+선)을 쓰게 해주는 도구

# 🔐 폐쇄형 B2B 보안 로그인을 구현하기 위한 추가 도구들
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth


# =====================================================================
# [2단계] 웹사이트 기본 화면 설정
# =====================================================================
# 모니터 화면 전체를 넓게(wide) 쓰도록 설정하고, 웹사이트 상단 타이틀을 지정합니다.
st.set_page_config(layout="wide") 
st.title("나만의 B2B 대시보드 🚀")


# =====================================================================
# 🔐 [3단계] 로그인 시스템 세팅 및 화면 출력
# =====================================================================
# 1. 회원 정보가 담긴 설정 파일(config.yaml)을 읽어옵니다.
with open('config.yaml', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)

# 2. 불러온 회원 정보와 쿠키 설정을 바탕으로 인증 관리자(Authenticator) 객체를 생성합니다.
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# 3. 테스트를 쉽게 하실 수 있도록 로그인 창 안내 문구에 아이디 정보를 적어둡니다.
st.info("💡 **[테스트용 로그인 정보 안내]**\n- **A병원 계정:** 아이디 `user_a` / 비밀번호 `123`\n- **B병원 계정:** 아이디 `user_b` / 비밀번호 `123`\n-구글시트 데이터: https://docs.google.com/spreadsheets/d/1ZUNpBHN0uWQPLEvNjGam1FuNpm5znqV-yud-gWTl4pc/edit?gid=0#gid=0")

# 4. 메인 화면에 로그인 입력 폼(아이디, 패스워드 칸)을 띄웁니다.
authenticator.login(location="main")

# 5. Streamlit 임시 저장소(session_state)에서 현재 로그인 상태와 사용자 정보를 꺼내옵니다.
authentication_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")
username = st.session_state.get("username")


# =====================================================================
# 🚪 [4단계] 로그인 결과에 따른 화면 분기 처리
# =====================================================================
# 케이스 1: 아이디나 비밀번호를 틀렸을 때
if authentication_status == False:
    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
    
# 케이스 2: 아직 로그인을 하지 않아 상태가 비어있을 때 (최초 접속 시)
elif authentication_status == None:
    st.warning("대시보드에 접근하려면 로그인을 해주세요.")
    
# 케이스 3: 로그인에 성공했을 때! 🎉
elif authentication_status == True:
    
    # 사이드바(좌측 메뉴)에 환영 인사말과 로그아웃 버튼을 배치합니다.
    st.sidebar.title(f"환영합니다, {name}님! 👋")
    authenticator.logout(location="sidebar")
    
    # 현재 로그인한 사용자의 영문 아이디를 바탕으로 config에서 권한(Role: 'A' 또는 'B')을 찾아냅니다.
    user_role = config['credentials']['usernames'][username]['role']
    st.sidebar.info(f"현재 부여된 권한: {user_role}")


    # =====================================================================
    # ⚡ [5단계] 속도 최적화: 구글 시트 데이터 캐싱(메모리 저장) 함수
    # =====================================================================
    # 💡 [캐싱 설명] 매번 구글 클라우드에 접속해 다운로드하면 느려지므로, 
    # 데이터를 최초 1회만 가져와 내 컴퓨터 메모리에 10분(600초) 동안 저장해두고 꺼내 씁니다.
    @st.cache_data(ttl=600)
    def load_google_sheet_data(worksheet_name):
        gc = gspread.service_account_from_dict(dict(st.secrets)) # 구글 API 인증키 로드
        sheet_url = "https://docs.google.com/spreadsheets/d/1ZUNpBHN0uWQPLEvNjGam1FuNpm5znqV-yud-gWTl4pc/edit?gid=0#gid=0" 
        doc = gc.open_by_url(sheet_url)                      # 구글 시트 문서 열기
        worksheet = doc.worksheet(worksheet_name)             # 지정한 탭(시트1 또는 시트2) 선택
        return pd.DataFrame(worksheet.get_all_records())      # 표 데이터를 판다스 DataFrame으로 변환 후 반환


    # =====================================================================
    # 🟦 [Section A] 첫 번째 권한('A') 사용자 전용 화면: 시트1 데이터 & 그래프
    # =====================================================================
    if user_role == 'A':
        st.success("A병원 전용 대시보드에 접속하셨습니다.")
        
        # 캐싱된 함수를 호출하여 구글 시트1 데이터를 번개처럼 불러옵니다.
        df_1 = load_google_sheet_data("시트1")

        st.subheader("📊 첫 번째 시트 데이터 (A 권한용)")
        st.dataframe(df_1, use_container_width=True) # 화면 가로 폭에 딱 맞춰서 표 출력

        # [데이터 가공] 그래프가 올바르게 그려지도록 필요한 행과 열을 잘라냅니다(Slicing).
        months_1 = df_1.columns[1:-2].tolist()                  # X축: 월 데이터
        patients_1 = df_1.iloc[0, 1:-2].astype(int).tolist()    # Y축1: 환자 수 (정수형 변환)
        tests_1 = df_1.iloc[1, 1:-2].astype(int).tolist()       # Y축2: 배양검사 수 (정수형 변환)
        # 시행률 데이터(% 문자열을 제거하고 소수점 숫자형태로 변환, 빈칸이면 0.0 처리)
        rates_1 = [float(str(r).replace('%', '')) if str(r) != '' else 0.0 for r in df_1.iloc[2, 1:-2].tolist()]

        # [그래프 생성] 시트1 혼합 그래프 (막대 2개 + 꺾은선 1개)
        st.subheader("📈 [시트1] 특정기간 미생물 배양검사 실시율(폐렴)")
        fig1 = make_subplots(specs=[[{"secondary_y": True}]]) # 오른쪽 Y축 사용 설정

        # ① 환자 수 막대 그래프 (왼쪽 기준)
        fig1.add_trace(go.Bar(x=months_1, y=patients_1, name="폐렴 환자 수", marker_color='#95A5A6', 
                              width=0.35, text=patients_1, textposition='auto', textfont=dict(size=16)), secondary_y=False)
        # ② 배양검사 수 막대 그래프 (왼쪽 기준)
        fig1.add_trace(go.Bar(x=months_1, y=tests_1, name="폐렴 배양검사", marker_color='#E74C3C', 
                              width=0.35, text=tests_1, textposition='auto', textfont=dict(size=16)), secondary_y=False)
        # ③ 시행률 꺾은선 그래프 (오른쪽 기준, 퍼센트 기호 및 볼드체 적용)
        rates_text_1 = [f"<b>{r}%</b>" for r in rates_1]
        fig1.add_trace(go.Scatter(x=months_1, y=rates_1, name="폐렴 시행률(%)", mode='lines+markers+text', 
                                  text=rates_text_1, textposition='top center', line=dict(color='#F39C12', width=5), 
                                  marker=dict(size=14), textfont=dict(size=16, color='#D35400')), secondary_y=True)

        # [그래프 디자인 정돈] 막대가 겹치지 않게 나란히 배치하고 여백 및 Y축 시작점을 0으로 고정
        fig1.update_layout(barmode='group', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), 
                           margin=dict(l=20, r=20, t=50, b=20))
        fig1.update_yaxes(title_text="건수", secondary_y=False, rangemode="tozero")
        fig1.update_yaxes(title_text="시행률(%)", secondary_y=True, rangemode="tozero")

        # 최종 웹 화면에 Plotly 그래프 렌더링
        st.plotly_chart(fig1, use_container_width=True)


    # =====================================================================
    # 🟩 [Section B] 두 번째 권한('B') 사용자 전용 화면: 시트2 데이터 & 그래프
    # =====================================================================
    elif user_role == 'B':
        st.success("B병원 전용 대시보드에 접속하셨습니다.")
        
        # 캐싱된 함수를 호출하여 구글 시트2 데이터를 불러옵니다.
        df_2 = load_google_sheet_data("시트2")

        st.subheader("📊 두 번째 시트 데이터 (B 권한용)")
        st.dataframe(df_2, use_container_width=True)

        # [데이터 가공] 시트2 구조에 맞춰 알맞은 행/열 데이터 추출
        months_2 = df_2.columns[1:-2].tolist()                  # X축: 월 데이터
        total_patients_2 = df_2.iloc[0, 1:-2].astype(int).tolist() # Y축1: 연인원 수
        clinical_tests_2 = df_2.iloc[1, 1:-2].astype(int).tolist() # Y축2: 임상 검사 수
        # 시행률 데이터 가공 (%)
        rates_2 = [float(str(r).replace('%', '')) if str(r) != '' else 0.0 for r in df_2.iloc[2, 1:-2].tolist()]

        # [그래프 생성] 시트2 혼합 그래프 
        st.subheader("📈 [시트2] 임상검사 시행률(%)")
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])

        # ① 연인원 수 막대 그래프 (왼쪽 기준)
        fig2.add_trace(go.Bar(x=months_2, y=total_patients_2, name="폐렴환자 연인원 수 (폐렴 특정 총 일수)", marker_color='#747D8C', 
                              width=0.35, text=total_patients_2, textposition='auto', textfont=dict(size=16)), secondary_y=False)
        # ② 임상 검사 수 막대 그래프 (왼쪽 기준)
        fig2.add_trace(go.Bar(x=months_2, y=clinical_tests_2, name="임상 검사", marker_color='#E67E22', 
                              width=0.35, text=clinical_tests_2, textposition='auto', textfont=dict(size=16)), secondary_y=False)
        # ③ 임상검사 시행률 꺾은선 그래프 (오른쪽 기준)
        rates_text_2 = [f"<b>{r}%</b>" for r in rates_2]
        fig2.add_trace(go.Scatter(x=months_2, y=rates_2, name="임상검사 시행률(%)", mode='lines+markers+text', 
                                  text=rates_text_2, textposition='top center', line=dict(color='#F39C12', width=5), 
                                  marker=dict(size=14), textfont=dict(size=16, color='#D35400')), secondary_y=True)

        # [그래프 디자인 정돈] 레이아웃 및 Y축 0점 고정
        fig2.update_layout(barmode='group', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), 
                           margin=dict(l=20, r=20, t=50, b=20))
        fig2.update_yaxes(title_text="건수", secondary_y=False, rangemode="tozero")
        fig2.update_yaxes(title_text="시행률(%)", secondary_y=True, rangemode="tozero")

        # 웹 화면에 출력
        st.plotly_chart(fig2, use_container_width=True)


    # =====================================================================
    # 🟥 [예외 처리] 권한이 잘못 지정되었거나 없는 사용자의 경우
    # =====================================================================
    else:
        st.error("열람할 수 있는 데이터가 없습니다. 관리자에게 권한을 요청하세요.")
