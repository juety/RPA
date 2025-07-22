import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
import folium
from folium import Icon
from streamlit_folium import st_folium

st.set_page_config(
    page_title="데이터 가공",
    page_icon=":page_with_curl:",
    layout="wide",
    initial_sidebar_state="expanded")

# 사이드바 영역
st.sidebar.title("사이드바 메뉴")
option = st.sidebar.selectbox(
    "옵션을 선택하세요:",
    ["표 보기", "캘린더 보기"]
)

# 엑셀 파일 불러오기
uploaded_file = st.file_uploader("파일 선택(csv or excel)", type=['csv', 'xls', 'xlsx'])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    ext = uploaded_file.name.split('.')[0]
    if option == "표 보기":
        if df is not None:
            target_columns = [df.columns[i] for i in [0, 1]]
            # 선택 필터 UI 만들기
            selections = {}
            st.title(f"{ext} 검색기")
            for col in target_columns:
                options = df[col].dropna().unique()
                selected = st.selectbox(f"{col} 선택", ["전체"] + sorted(options.astype(str)))
                selections[col] = selected
            # 필터링
            filtered_df = df.copy()
            for col, selected in selections.items():
                if selected != "전체":
                    filtered_df = filtered_df[filtered_df[col].astype(str) == selected]

            # 결과 출력
            st.subheader("검색 결과")
            st.dataframe(filtered_df.reset_index(drop=True))
            # 날짜 필터링 기능 추가
            st.markdown("---")
            st.subheader("날짜 범위로 필터링")

            # 날짜형 컬럼 자동 감지
            date_columns = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
            if not date_columns:
                for col in df.columns:
                    try:
                        df[col] = pd.to_datetime(df[col])
                        date_columns.append(col)
                    except:
                        continue

            # "시작" / "종료" 키워드로 컬럼 이름 자동 추정
            start_col = None
            end_col = None
            for col in date_columns:
                if '시작' in col:
                    start_col = col
                elif '종료' in col:
                    end_col = col

            # 필터링 실행
            if start_col and end_col:
                filtered_df[start_col] = pd.to_datetime(filtered_df[start_col], errors='coerce')
                filtered_df[end_col] = pd.to_datetime(filtered_df[end_col], errors='coerce')
                filtered_df = filtered_df.dropna(subset=[start_col, end_col])

                min_date = filtered_df[start_col].min().date()
                max_date = filtered_df[end_col].max().date()

                user_start = st.date_input("시작일 선택", value=min_date, key="user_start")
                user_end = st.date_input("종료일 선택", value=max_date, key="user_end")

                if user_start > user_end:
                    st.error("시작일은 종료일보다 이전이어야 합니다.")
                else:
                    # 당신의 의도대로 row가 기간 안에 **완전히 포함된** 경우만 필터
                    mask = (
                        filtered_df[start_col].dt.date >= user_start
                    ) & (
                        filtered_df[end_col].dt.date <= user_end
                    )
                    filtered_df = filtered_df[mask]
            else:
                st.warning("'시작' 또는 '종료'가 포함된 날짜 컬럼명이 존재하지 않습니다.")

            # 결과 출력
            st.subheader("검색 결과")
            st.dataframe(filtered_df.reset_index(drop=True))
    if option == "캘린더 보기":
        if df is not None:
            # 필터 선택 UI
            st.sidebar.header("🎯 검색 필터")
            selected_category = st.sidebar.selectbox("분류 선택", ["전체"] + sorted(df["분류"].dropna().unique().tolist()))
            selected_gu = st.sidebar.selectbox("자치구 선택", ["전체"] + sorted(df["자치구"].dropna().unique().tolist()))

            # 조건 필터링
            filtered_df = df.copy()
            if selected_category != "전체":
                filtered_df = filtered_df[filtered_df["분류"] == selected_category]
            if selected_gu != "전체":
                filtered_df = filtered_df[filtered_df["자치구"] == selected_gu]

            events = []
            event_map = {}
            for _, row in filtered_df.iterrows():
                title = row['공연/행사명']
                start = pd.to_datetime(row['시작일']).strftime("%Y-%m-%d")
                end = pd.to_datetime(row['종료일']).strftime("%Y-%m-%d")
                events.append({
                    "title": title,
                    "start": start,
                    "end": end,
                    "allDay": True,
                    "backgroundColor": "#FF6C6C",
                    "borderColor": "#FF6C6C"
                })
                event_map[title] = {
                    "공연/행사명": title,
                    "분류": row["분류"],
                    "자치구": row["자치구"],
                    "시작일": row["시작일"],
                    "종료일": row["종료일"],
                    "장소": row.get("장소", "미정"),
                    "기관명": row.get("기관명", "미정"),
                    "이용요금": row["이용요금"] if pd.notna(row["이용요금"]) else "정보 없음"
                }

            st.title(f"📅 {ext} 캘린더")
            st.markdown(f"**총 {len(events)}건의 결과가 표시됩니다.**")

            # calendar 옵션 설정
            calendar_options = {
            "initialView": "dayGridMonth",  # 초기 보기: 월간
            "editable": False,              # 이벤트 수정 가능
            "eventStartEditable": False,
            "eventDurationEditable": False,
            "selectable": False,             # 날짜 선택 가능
            "navLinks": True,
            "locale": "ko",                 # 한글 설정
            "headerToolbar": {
            "start": "prev,next today",
            "center": "title",
            "end": "dayGridMonth,timeGridWeek,timeGridDay"
            },
            }
            # 캘린더 렌더링 및 클릭 이벤트 처리
            clicked = calendar(events=events, options=calendar_options)

            if clicked and clicked.get("callback") == "eventClick":
                event_data = clicked["eventClick"]["event"]
                title = event_data["title"]
                detail = event_map.get(title)

                if detail:
                    st.subheader("📌 행사 상세 정보")
                    st.markdown(f"""
                    - **공연/행사명**: {detail['공연/행사명']}
                    - **분류**: {detail['분류']}
                    - **자치구**: {detail['자치구']}
                    - **기간**: {detail['시작일']} ~ {detail['종료일']}
                    - **장소**: {detail['장소']}
                    - **기관명**: {detail['기관명']}
                    - **이용요금**: {detail.get('이용요금') or "정보 없음"}
                    """)
                    if "위도(Y좌표)" in df.columns and "경도(X좌표)" in df.columns:
                        df = df.rename(columns={
                            '위도(Y좌표)': 'latitude',
                            '경도(X좌표)': 'longitude'
                        })
                        df = df.dropna(subset=['latitude', 'longitude'])

                        # 선택된 행사 위치만 필터링
                        map_df = df[df['공연/행사명'] == detail['공연/행사명']]
                            
                        if not map_df.empty:
                            lat = map_df.iloc[0]['latitude']
                            lon = map_df.iloc[0]['longitude']

                            m = folium.Map(location=[lat, lon], zoom_start=16)
                            popup_text = f"공연/행사명 : {detail['공연/행사명']}<br>장소 : {detail['장소']}"
                            folium.Marker(
                                location=[lat, lon],
                                popup=popup_text,
                                tooltip=detail['장소'],
                                icon=Icon(color="red", icon="info-sign")
                            ).add_to(m)

                            st.subheader("📍 행사 위치 지도")
                            st_folium(m, width=1000, height=700)
                        else:
                            st.info("이 행사에 대한 위치 정보가 없습니다.")
                else:
                    st.warning("선택한 이벤트의 상세 정보를 찾을 수 없습니다.")
