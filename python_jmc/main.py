import streamlit as st
import pandas as pd

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
            st.dataframe(df)
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
