import pandas as pd

# ─────────────────────────────────────────────────────────────
# 1. 날짜형 컬럼을 찾아 datetime으로 변환
# ─────────────────────────────────────────────────────────────
def detect_and_convert_date_columns(df: pd.DataFrame):
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    if not date_cols:
        for c in df.columns:
            try:
                df[c] = pd.to_datetime(df[c])
                date_cols.append(c)
            except Exception:
                continue
    return df, date_cols

# ─────────────────────────────────────────────────────────────
# 2. "시작", "종료"가 포함된 컬럼명 추출
# ─────────────────────────────────────────────────────────────
def find_start_end_columns(date_cols):
    start_col = next((c for c in date_cols if "시작" in c), None)
    end_col   = next((c for c in date_cols if "종료" in c), None)
    return start_col, end_col

# ─────────────────────────────────────────────────────────────
# 3. 일반(문자열) 필터 적용
# ─────────────────────────────────────────────────────────────
def apply_filters(df, selections: dict):
    out = df.copy()
    for col, val in selections.items():
        if val != "전체":
            out = out[out[col].astype(str) == val]
    return out

# ─────────────────────────────────────────────────────────────
# 4. 날짜 범위 필터 적용
# ─────────────────────────────────────────────────────────────
def apply_date_range_filter(df, start_col, end_col, user_start, user_end):
    df[start_col] = pd.to_datetime(df[start_col], errors="coerce")
    df[end_col]   = pd.to_datetime(df[end_col],   errors="coerce")
    df = df.dropna(subset=[start_col, end_col])

    mask = (df[start_col].dt.date >= user_start) & (df[end_col].dt.date <= user_end)
    return df[mask]

# ─────────────────────────────────────────────────────────────
# 5. 날짜 선택 위젯의 min/max 계산
# ─────────────────────────────────────────────────────────────
def get_date_limits(df, start_col, end_col):
    return df[start_col].min().date(), df[end_col].max().date()
def get_filtered_calendar_df(df, selected_category, selected_gu):
    if selected_category != "전체":
        df = df[df["분류"] == selected_category]
    if selected_gu != "전체":
        df = df[df["자치구"] == selected_gu]
    return df

def create_calendar_events(df):
    events = []
    event_map = {}

    for _, row in df.iterrows():
        title = row["공연/행사명"]
        start = pd.to_datetime(row["시작일"]).strftime("%Y-%m-%d")
        end   = pd.to_datetime(row["종료일"]).strftime("%Y-%m-%d")
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
            "분류": row.get("분류", ""),
            "자치구": row.get("자치구", ""),
            "시작일": row.get("시작일", ""),
            "종료일": row.get("종료일", ""),
            "장소": row.get("장소", "미정"),
            "기관명": row.get("기관명", "미정"),
            "이용요금": row["이용요금"] if pd.notna(row["이용요금"]) else "정보 없음"
        }
    return events, event_map
