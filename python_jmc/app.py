import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="데이터 가공",
    page_icon=":page_with_curl:",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
