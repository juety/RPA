import streamlit as st
from st_ui import *

def main():
    st.set_page_config(page_title="데이터 가공", page_icon=":page_with_curl:", layout="wide")
    st.sidebar.title("사이드바 메뉴")
    option = st.sidebar.selectbox("옵션을 선택하세요:", ["표 보기", "캘린더 보기"])

    uploaded_file = st.file_uploader("파일 선택(csv or excel)", type=["csv", "xls", "xlsx"])
    if uploaded_file:
        st.session_state["file_name"] = uploaded_file.name.rsplit(".", 1)[0]
        df = load_file(uploaded_file)
        if option == "표 보기":
            table_view(df)
        elif option == "캘린더 보기":
            calendar_view(df)

if __name__ == "__main__":
    main()
