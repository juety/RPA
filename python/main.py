import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from streamlit_folium import st_folium
import folium
from folium import Icon

from data_processing import (
    detect_and_convert_date_columns,
    find_start_end_columns,
    apply_filters,
    apply_date_range_filter,
    get_date_limits,
    get_filtered_calendar_df,
    create_calendar_events,
)

st.set_page_config(page_title="데이터 가공", page_icon=":page_with_curl:", layout="wide")

# ────────── 사이드바 ──────────
st.sidebar.title("사이드바 메뉴")
option = st.sidebar.selectbox("옵션을 선택하세요:", ["표 보기", "캘린더 보기"])
uploaded_file = st.file_uploader("파일 선택(csv or excel)", type=["csv", "xls", "xlsx"])

# ────────── 본문 처리 ──────────
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    ext = uploaded_file.name.rsplit(".", 1)[0]

    if option == "표 보기":
        st.title(f"{ext} 검색기")

        # ── (1) 문자열 기준 필터 UI ──
        target_cols = [df.columns[i] for i in [0, 1]]
        selections = {
            col: st.selectbox(f"{col} 선택", ["전체"] + sorted(df[col].dropna().astype(str).unique()))
            for col in target_cols
        }

        filtered_df = apply_filters(df, selections)

        # ── (2) 날짜 범위 필터 UI ──
        st.markdown("---")
        st.subheader("날짜 범위로 필터링")

        df, date_cols          = detect_and_convert_date_columns(df)
        start_col, end_col     = find_start_end_columns(date_cols)

        if start_col and end_col:
            min_date, max_date = get_date_limits(df, start_col, end_col)

            user_start = st.date_input("시작일 선택", value=min_date,
                                       min_value=min_date, max_value=max_date, key="user_start")
            user_end   = st.date_input("종료일 선택", value=max_date,
                                       min_value=min_date, max_value=max_date, key="user_end")

            if user_start > user_end:
                st.error("시작일은 종료일보다 이전이어야 합니다.")
            else:
                filtered_df = apply_date_range_filter(filtered_df, start_col, end_col,
                                                      user_start, user_end)
        else:
            st.warning("데이터에 '시작'·'종료'가 포함된 날짜 컬럼명이 필요합니다.")

        # ── (3) 결과 출력 ──
        st.subheader("검색 결과")
        st.dataframe(filtered_df.reset_index(drop=True))

    elif option == "캘린더 보기":
        st.title(f"📅 {ext} 캘린더")

        # 사이드바 필터
        st.sidebar.header("🎯 검색 필터")
        category_list = ["전체"] + sorted(df["분류"].dropna().unique().tolist())
        gu_list       = ["전체"] + sorted(df["자치구"].dropna().unique().tolist())

        selected_category = st.sidebar.selectbox("분류 선택", category_list)
        selected_gu       = st.sidebar.selectbox("자치구 선택", gu_list)

        # 데이터 필터링
        calendar_df = get_filtered_calendar_df(df.copy(), selected_category, selected_gu)
        events, event_map = create_calendar_events(calendar_df)

        st.markdown(f"**총 {len(events)}건의 결과가 표시됩니다.**")

        # 캘린더 렌더링
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
                - **이용요금**: {detail['이용요금']}
                """)

                if "위도(Y좌표)" in df.columns and "경도(X좌표)" in df.columns:
                    df = df.rename(columns={"위도(Y좌표)": "latitude", "경도(X좌표)": "longitude"})
                    df = df.dropna(subset=["latitude", "longitude"])
                    map_df = df[df["공연/행사명"] == title]

                    if not map_df.empty:
                        lat = map_df.iloc[0]["latitude"]
                        lon = map_df.iloc[0]["longitude"]
                        m = folium.Map(location=[lat, lon], zoom_start=16)
                        popup_text = f"공연/행사명 : {title}<br>장소 : {detail['장소']}"

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
