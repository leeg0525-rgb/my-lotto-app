from collections import Counter
import random
import requests
import streamlit as st

st.set_page_config(page_title="AI 로또 번호 분석기", page_icon="🎰", layout="centered")

# 번호별 공식 로또 볼 색상 매핑
def get_ball_color(num):
    if num <= 10:
        return "#fbc400"  # 노랑 (1~10)
    elif num <= 20:
        return "#69c8f2"  # 파랑 (11~20)
    elif num <= 30:
        return "#ff7272"  # 빨강 (21~30)
    elif num <= 40:
        return "#aaaaaa"  # 회색 (31~40)
    else:
        return "#b0d840"  # 녹색 (41~45)

def render_balls(numbers):
    html = '<div style="display: flex; gap: 8px; justify-content: center; margin: 10px 0;">'
    for n in sorted(numbers):
        color = get_ball_color(n)
        html += f'<div style="background-color: {color}; color: white; font-weight: bold; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{n}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_lotto_data():
    """당첨 데이터 로드 (1시간 캐싱)"""
    url = "https://raw.githubusercontent.com/jonghwan-park/lotto-history/main/data.json"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
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

# --- UI 메인 ---
st.title("🎰 맞춤 로또 번호 추출기")
st.caption("제외할 번호를 지정하고 최근 회차 출현 패턴에 맞춘 나만의 추천 번호를 생성합니다.")

data = load_lotto_data()

# 1. 제외수 선택
excluded_numbers = st.multiselect(
    "🚫 조합에서 제외할 번호 선택",
    options=list(range(1, 46)),
    placeholder="제외하고 싶은 번호를 터치해 선택하세요"
)

# 2. 분석 옵션 설정
col1, col2 = st.columns(2)
with col1:
    recent_count = st.slider("분석할 최근 회차", min_value=3, max_value=50, value=3, step=1)
with col2:
    game_count = st.slider("생성할 게임 수", min_value=1, max_value=10, value=5)

# 3. 이해하기 쉬운 전략 선택
strategy = st.radio(
    "어떤 방식으로 번호를 뽑을까요?",
    [
        "🔥 요즘 잘 나오는 번호만 뽑기",
        "⚡ 반반 섞기 (자주 나온 수 3개 + 안 나온 수 3개)",
        "❄️ 최근 안 나온 번호만 뽑기 (역발상)",
        "🎲 확률 비례 골고루 뽑기"
    ]
)

# 당첨 데이터 집계
sorted_items = sorted(data, key=lambda x: x["round"], reverse=True)[:recent_count]
all_numbers = []
for item in sorted_items:
    nums = item.get("numbers") or [item[f"drwtNo{i}"] for i in range(1, 7)]
    all_numbers.extend(nums)

counts = Counter(all_numbers)

# 제외수를 뺀 가용 번호 풀
available_pool = [n for n in range(1, 46) if n not in excluded_numbers]
ranked_available = sorted(available_pool, key=lambda x: counts.get(x, 0), reverse=True)

appeared_nums = [n for n in ranked_available if counts.get(n, 0) > 0]
not_appeared_nums = [n for n in ranked_available if counts.get(n, 0) == 0]

hot_pool = appeared_nums if len(appeared_nums) >= 6 else ranked_available[:max(6, len(ranked_available))]
cold_pool = not_appeared_nums if len(not_appeared_nums) >= 6 else ranked_available[-max(6, len(ranked_available)):]

# 상세 통계 접기/펼치기
with st.expander(f"📊 최근 {recent_count}회차 출현 데이터 보기"):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🔥 많이 나온 번호**")
        for num in ranked_available[:5]:
            st.write(f"- {num}번 ({counts.get(num, 0)}회 출현)")
    with c2:
        st.markdown("**❄️ 안 나온 번호**")
        for num in ranked_available[-5:]:
            st.write(f"- {num}번 ({counts.get(num, 0)}회 출현)")

# 번호 추출 버튼
if st.button("🎲 추천 번호 뽑기", use_container_width=True, type="primary"):
    if len(available_pool) < 6:
        st.error("제외된 번호가 너무 많아 6개 번호를 구성할 수 없습니다. 제외수를 줄여주세요.")
    else:
        st.subheader("🎯 생성된 추천 번호")
        if excluded_numbers:
            st.caption(f"제외된 번호: {sorted(excluded_numbers)}")

        for i in range(1, game_count + 1):
            if "요즘 잘 나오는" in strategy:
                pick_pool = hot_pool if len(hot_pool) >= 6 else ranked_available[:12]
                picked = random.sample(pick_pool, min(6, len(pick_pool)))
                if len(picked) < 6:
                    remain = [n for n in available_pool if n not in picked]
                    picked += random.sample(remain, 6 - len(picked))

            elif "최근 안 나온" in strategy:
                pick_pool = cold_pool if len(cold_pool) >= 6 else ranked_available[-12:]
                picked = random.sample(pick_pool, min(6, len(pick_pool)))
                if len(picked) < 6:
                    remain = [n for n in available_pool if n not in picked]
                    picked += random.sample(remain, 6 - len(picked))

            elif "반반 섞기" in strategy:
                h_k = min(3, len(hot_pool))
                h_pick = random.sample(hot_pool, h_k)
                c_pool = [n for n in cold_pool if n not in h_pick]
                c_k = min(6 - len(h_pick), len(c_pool))
                c_pick = random.sample(c_pool, c_k)
                picked = h_pick + c_pick
                if len(picked) < 6:
                    remain = [n for n in available_pool if n not in picked]
                    picked += random.sample(remain, 6 - len(picked))

            else:
                weights = [counts.get(n, 0) + 1 for n in available_pool]
                t_pool = available_pool[:]
                t_weights = weights[:]
                picked_set = set()
                while len(picked_set) < 6 and t_pool:
                    c = random.choices(t_pool, weights=t_weights, k=1)[0]
                    picked_set.add(c)
                    idx = t_pool.index(c)
                    t_pool.pop(idx)
                    t_weights.pop(idx)
                picked = list(picked_set)

            st.write(f"**{i}게임**")
            render_balls(picked)
