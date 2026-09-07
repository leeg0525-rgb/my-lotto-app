from collections import Counter
import random
import requests
import streamlit as st

# 모바일 화면 설정
st.set_page_config(page_title="AI 로또 번호 분석기", page_icon="🎰", layout="centered")

# 번호별 색상 매핑 (공식 로또 색상)
def get_ball_color(num):
    if num <= 10:
        return "#fbc400"  # 노랑
    elif num <= 20:
        return "#69c8f2"  # 파랑
    elif num <= 30:
        return "#ff7272"  # 빨강
    elif num <= 40:
        return "#aaaaaa"  # 회색
    else:
        return "#b0d840"  # 녹색

def render_balls(numbers):
    html = '<div style="display: flex; gap: 8px; justify-content: center; margin: 10px 0;">'
    for n in sorted(numbers):
        color = get_ball_color(n)
        html += f'<div style="background-color: {color}; color: white; font-weight: bold; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{n}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_lotto_data():
    """데이터 캐싱 (1시간 유지)"""
    url = "https://raw.githubusercontent.com/jonghwan-park/lotto-history/main/data.json"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    
    # 예비 데이터
    return [
        {"round": 1135, "numbers": [1, 6, 13, 19, 21, 33]},
        {"round": 1134, "numbers": [3, 7, 9, 13, 19, 24]},
        {"round": 1133, "numbers": [13, 14, 20, 28, 29, 34]},
        {"round": 1132, "numbers": [6, 7, 19, 28, 34, 41]},
        {"round": 1131, "numbers": [1, 2, 6, 14, 20, 40]},
        {"round": 1130, "numbers": [15, 19, 21, 25, 27, 28]},
        {"round": 1129, "numbers": [5, 10, 11, 17, 28, 34]},
        {"round": 1128, "numbers": [1, 5, 8, 16, 28, 33]},
        {"round": 1127, "numbers": [10, 15, 24, 30, 31, 37]},
        {"round": 1126, "numbers": [4, 5, 9, 11, 37, 40]},
        {"round": 1125, "numbers": [6, 14, 25, 33, 40, 44]},
        {"round": 1124, "numbers": [3, 8, 17, 34, 39, 43]},
        {"round": 1123, "numbers": [13, 19, 21, 24, 34, 35]},
        {"round": 1122, "numbers": [13, 19, 21, 26, 37, 43]},
        {"round": 1121, "numbers": [6, 24, 31, 32, 38, 44]},
        {"round": 1120, "numbers": [2, 19, 26, 31, 38, 41]},
    ]

# --- UI 화면 구성 ---
st.title("🎰 로또 번호 분석기")
st.caption("최근 당첨 빈도를 분석하여 가중치 추천 번호를 생성합니다.")

data = load_lotto_data()
recent_count = st.slider("분석할 최근 회차 수", min_value=10, max_value=50, value=20, step=5)
game_count = st.slider("생성할 게임 수", min_value=1, max_value=10, value=5)

sorted_items = sorted(data, key=lambda x: x["round"], reverse=True)[:recent_count]
all_numbers = []
for item in sorted_items:
    nums = item.get("numbers") or [item[f"drwtNo{i}"] for i in range(1, 7)]
    all_numbers.extend(nums)

counts = Counter(all_numbers)

# 상위 빈도 번호 표시 접기/펼치기
with st.expander(f"📊 최근 {recent_count}회차 최다 출현 번호 확인"):
    cols = st.columns(5)
    for idx, (num, cnt) in enumerate(counts.most_common(10)):
        cols[idx % 5].metric(label=f"{num}번", value=f"{cnt}회")

# 번호 추첨 버튼
if st.button("🎲 추천 번호 생성하기", use_container_width=True, type="primary"):
    weights = [counts.get(n, 0) + 1 for n in range(1, 46)]
    pool = list(range(1, 46))

    st.subheader("🎯 생성된 추천 조합")
    for i in range(1, game_count + 1):
        picked = set()
        temp_pool = pool[:]
        temp_weights = weights[:]

        while len(picked) < 6:
            c = random.choices(temp_pool, weights=temp_weights, k=1)[0]
            if c not in picked:
                picked.add(c)
                idx = temp_pool.index(c)
                temp_pool.pop(idx)
                temp_weights.pop(idx)

        st.write(f"**{i}게임**")
        render_balls(list(picked))