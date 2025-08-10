import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from streamlit_folium import st_folium
import folium
from folium import Icon
from data_processing import *

@st.cache_data
def load_file(file):
    ext = file.name.split(".")[-1].lower()
    if ext in ["csv", "xls", "xlsx"]:
        return pd.read_excel(file)
    else:
        st.error("지원하지 않는 파일 형식입니다.")
        return pd.DataFrame()

def table_view(df):
    st.title(f"{st.session_state['file_name']} 검색기")

    # 문자열 기준 필터
    st.sidebar.subheader("🔍 문자열 기준 필터")
    target_cols = [df.columns[i] for i in [0, 1]]
    selections = {
        col: st.sidebar.selectbox(f"{col} 선택", ["전체"] + sorted(df[col].dropna().astype(str).unique()),
                                  index=0, key=f"filter_{col}")
        for col in target_cols
    }
    filtered_df = apply_filters(df, selections)

    # 날짜 필터
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 날짜 범위로 필터링")
    df, date_cols = detect_and_convert_date_columns(df)
    start_col, end_col = find_start_end_columns(date_cols)

    if start_col and end_col:
        min_date, max_date = get_date_limits(df, start_col, end_col)
        user_start = st.sidebar.date_input("시작일 선택", value=min_date, 
                                           min_value=min_date, max_value=max_date, key="user_start")
        user_end = st.sidebar.date_input("종료일 선택", value=max_date, 
                                         min_value=min_date, max_value=max_date, key="user_end")

        if user_start > user_end:
            st.error("시작일은 종료일보다 이전이어야 합니다.")
        else:
            filtered_df = apply_date_range_filter(filtered_df, start_col, end_col, user_start, user_end)
            filtered_df = filtered_df.astype(str)
    else:
        st.warning("데이터에 '시작'·'종료'가 포함된 날짜 컬럼명이 필요합니다.")

    st.subheader("검색 결과")
    st.markdown(f"**총 {len(filtered_df)}건의 결과가 표시됩니다.**")
    st.dataframe(filtered_df, hide_index=True)

def calendar_view(df):
    st.title(f"📅 {st.session_state['file_name']} 캘린더")

    st.sidebar.header("🎯 검색 필터")
    category_list = ["전체"] + sorted(df["분류"].dropna().unique().tolist())
    gu_list = ["전체"] + sorted(df["자치구"].dropna().unique().tolist())

    selected_category = st.sidebar.selectbox("분류 선택", category_list, key="selected_category")
    selected_gu = st.sidebar.selectbox("자치구 선택", gu_list, key="selected_gu")

    if selected_category == "전체" and selected_gu == "전체":
        st.info("🔍 좌측 필터를 사용해 '분류' 또는 '자치구'를 선택하면 행사들이 캘린더에 표시됩니다.")
        events, event_map = [], {}
    else:
        calendar_df = get_filtered_calendar_df(df.copy(), selected_category, selected_gu)
        events, event_map = create_calendar_events(calendar_df)
        st.markdown(f"**총 {len(events)}건의 결과가 표시됩니다.**")

    calendar_options = {
        "initialView": "dayGridMonth",
        "editable": False,
        "eventStartEditable": False,
        "eventDurationEditable": False,
        "selectable": False,
        "navLinks": True,
        "locale": "ko",
        "headerToolbar": {
            "start": "prev,next today",
            "center": "title",
            "end": "dayGridMonth,timeGridWeek,timeGridDay"
        },
    }

    clicked = calendar(events=events, options=calendar_options)

    if clicked and clicked.get("callback") == "eventClick":
        title = clicked["eventClick"]["event"]["title"]
        detail = event_map.get(title)
        if detail:
            st.session_state["selected_event"] = detail

    if "selected_event" in st.session_state:
        detail = st.session_state["selected_event"]
        st.subheader("📌 행사 상세 정보")
        st.markdown(f"""
        - **공연/행사명**: {detail['공연/행사명']}
        - **분류**: {detail['분류']}
        - **자치구**: {detail['자치구']}
        - **기간**: {detail['시작일']} ~ {detail['종료일']}
        - **장소**: {detail['장소']}
        - **이용요금**: {detail['이용요금']}
        """)

        if "위도(Y좌표)" in df.columns and "경도(X좌표)" in df.columns:
            df = df.rename(columns={"위도(Y좌표)": "latitude", "경도(X좌표)": "longitude"})
            df = df.dropna(subset=["latitude", "longitude"])
            map_df = df[df["공연/행사명"] == detail["공연/행사명"]]

            if not map_df.empty:
                lat = map_df.iloc[0]["latitude"]
                lon = map_df.iloc[0]["longitude"]
                m = folium.Map(location=[lat, lon], zoom_start=16)
                popup_text = f"공연/행사명 : {detail['공연/행사명']}<br>장소 : {detail['장소']}"
                folium.Marker(
                    location=[lat, lon],
                    popup=popup_text,
                    tooltip=detail["장소"],
                    icon=Icon(color="red", icon="info-sign")
                ).add_to(m)

                st.subheader("📍 행사 위치 지도")
                st_folium(m, width=1000, height=700)
            else:
                st.info("이 행사에 대한 위치 정보가 없습니다.")
