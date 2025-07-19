import streamlit as st
import pandas as pd
import folium
from folium import Icon
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# 한글 폰트 설정 (Windows 기준)
font_path = "C:/Windows/Fonts/malgun.ttf"  # 말굽고딕 폰트 경로
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)

st.set_page_config(
    page_title="데이터 가공",
    page_icon=":page_with_curl:",
    layout="wide",
    initial_sidebar_state="expanded")

# 사이드바 영역
st.sidebar.title("사이드바 메뉴")
option = st.sidebar.selectbox(
    "옵션을 선택하세요:",
    ["표 보기", "지도 보기", "상세한 지도 보기", "유/무료 통계 시각화"]
)


uploaded_file = st.file_uploader("파일 선택(csv or excel)", type=['csv', 'xls', 'xlsx'])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    ext = uploaded_file.name.split('.')[-2]
    st.title(ext+" 시각화")

if option == "표 보기":
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        if df is not None:
            st.dataframe(df)

elif option == "지도 보기":
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        if '위도(Y좌표)' in df.columns and '경도(X좌표)' in df.columns:
            df = df.rename(columns={
                '위도(Y좌표)': 'latitude',
                '경도(X좌표)': 'longitude'
            })
            df = df.dropna(subset=['latitude', 'longitude'])
            st.map(df)

elif option == "상세한 지도 보기":
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        if '위도(Y좌표)' in df.columns and '경도(X좌표)' in df.columns:
            df = df.rename(columns={
                '위도(Y좌표)': 'latitude',
                '경도(X좌표)': 'longitude'
                })
            df = df.dropna(subset=['latitude', 'longitude'])

            center_lat = df['latitude'].mean()
            center_lon = df['longitude'].mean()

            m = folium.Map(location=[center_lat, center_lon], zoom_start=11)

            for _, row in df.iterrows():
                lat, lon = row['latitude'], row['longitude']
                popup_text = f"공연/행사명 :{row.get('공연/행사명', '')}<br> 장소명 :{row.get('장소', '')}"
                place_name = row.get('장소', '')
                folium.Marker(
                    location=[lat, lon],
                    popup=popup_text,
                    tooltip=place_name,
                    icon=Icon(color="red", icon="info-sign")
                ).add_to(m)
            
            st_folium(m, width=700, height=500)
elif option == "유/무료 통계 시각화":
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
    # 유무료 열이 있는지 확인
        if "유무료" in df.columns:
            # 유무료 항목 집계
            counts = df["유무료"].value_counts()

            # 시각화
            st.subheader("유/무료 행사 개수")
            fig, ax = plt.subplots()
            counts.plot(kind="bar", color=["skyblue", "salmon"], ax=ax)
            ax.set_xlabel("유/무료")
            ax.set_ylabel("행사 개수")
            ax.set_title("서울시 문화행사 - 유료 vs 무료")
            st.pyplot(fig)

            # 데이터 표도 함께 출력
            st.subheader("세부 데이터")
            st.dataframe(counts.rename_axis("구분").reset_index(name="개수"))

            


     

