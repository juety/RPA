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

            # 날짜형 컬럼 추출
            date_columns = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
            if not date_columns:
                # 날짜 컬럼이 datetime 타입이 아니면 자동으로 변환 시도
                for col in df.columns:
                    try:
                        df[col] = pd.to_datetime(df[col])
                        date_columns.append(col)
                    except:
                        continue

            if date_columns:
                date_col = st.selectbox("날짜 컬럼을 선택하세요", date_columns)

                min_date = df[date_col].min().date()
                max_date = df[date_col].max().date()

                start_date = st.date_input("시작일 선택", min_value=min_date, max_value=max_date, value=min_date)
                end_date = st.date_input("종료일 선택", min_value=min_date, max_value=max_date, value=max_date)

                if start_date > end_date:
                    st.error("시작일은 종료일보다 이전이어야 합니다.")
                else:
                # 날짜 변환 (filtered_df에도 적용)
                    filtered_df[date_col] = pd.to_datetime(filtered_df[date_col], errors='coerce')
                    filtered_df = filtered_df.dropna(subset=[date_col])

                mask = (filtered_df[date_col].dt.date >= start_date) & (filtered_df[date_col].dt.date <= end_date)
                filtered_df = filtered_df[mask]

            # 결과 출력
            st.subheader("검색 결과")
            st.dataframe(filtered_df.reset_index(drop=True))