from collections import Counter
import random
import requests
import streamlit as st

# 모바일 최적화 설정
st.set_page_config(page_title="AI 로또 번호 분석기", page_icon="🎰", layout="centered")

# 번호별 공식 로또 색상 매핑
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

# --- UI 화면 ---
st.title("🎰 맞춤형 전략 로또 분석기")
st.caption("최근 당첨 데이터를 기반으로 원하는 전략별 추천 번호를 추출합니다.")

data = load_lotto_data()

# 옵션 설정 (최소 3회차부터 슬라이더 지원)
col1, col2 = st.columns(2)
with col1:
    recent_count = st.slider("분석 회차 수", min_value=3, max_value=50, value=3, step=1)
with col2:
    game_count = st.slider("생성 게임 수", min_value=1, max_value=10, value=5)

# 전략 선택
strategy = st.radio(
    "추천 전략 선택",
    [
        "⚡ 믹스 조합 (핫 3개 + 콜드 3개)",
        "🔥 핫 넘버 전용 (자주 나온 번호 위주)",
        "❄️ 콜드 넘버 전용 (안 나온 번호 위주)",
        "🎲 전체 가중치 랜덤 (출현 빈도 비례 추첨)"
    ]
)

# 데이터 집계
sorted_items = sorted(data, key=lambda x: x["round"], reverse=True)[:recent_count]
all_numbers = []
for item in sorted_items:
    nums = item.get("numbers") or [item[f"drwtNo{i}"] for i in range(1, 7)]
    all_numbers.extend(nums)

counts = Counter(all_numbers)

# 1~45번 전체 빈도 정렬 (출현 횟수 기준 내림차순)
ranked_by_freq = sorted(range(1, 46), key=lambda x: counts.get(x, 0), reverse=True)

# 3회차 기준 실제 출현한 번호 집합(핫)과 미출현 번호 집합(콜드)
appeared_nums = [num for num in ranked_by_freq if counts.get(num, 0) > 0]
not_appeared_nums = [num for num in ranked_by_freq if counts.get(num, 0) == 0]

# 핫 넘버 풀: 최근 등장 번호가 6개 이상이면 그 번호들로 구성, 부족하면 상위 10~15개 유지
hot_pool = appeared_nums if len(appeared_nums) >= 6 else ranked_by_freq[:12]
# 콜드 넘버 풀: 최근 안 나온 번호 우선
cold_pool = not_appeared_nums if len(not_appeared_nums) >= 6 else ranked_by_freq[-15:]

# 빈도 데이터 접기/펼치기
with st.expander(f"📊 최근 {recent_count}회차 출현 데이터 상세"):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**🔥 출현 번호 (총 {len(appeared_nums)}개)**")
        top_show = ranked_by_freq[:min(6, len(appeared_nums))]
        for num in top_show:
            st.write(f"- {num}번 ({counts.get(num, 0)}회 출현)")
    with c2:
        st.markdown(f"**❄️ 미출현 번호 (총 {len(not_appeared_nums)}개)**")
        sample_cold = not_appeared_nums[:6] if len(not_appeared_nums) >= 6 else ranked_by_freq[-6:]
        for num in sample_cold:
            st.write(f"- {num}번 (0회 출현)")

# 번호 추첨 버튼
if st.button("🎲 번호 생성하기", use_container_width=True, type="primary"):
    st.subheader("🎯 생성된 추천 조합")
    
    for i in range(1, game_count + 1):
        if "핫 넘버 전용" in strategy:
            picked = random.sample(hot_pool, 6)
            
        elif "콜드 넘버 전용" in strategy:
            picked = random.sample(cold_pool, 6)
            
        elif "믹스 조합" in strategy:
            # 핫에서 3개, 콜드에서 3개 비복원 추출
            h_pick = random.sample(hot_pool, min(3, len(hot_pool)))
            c_pick = random.sample(cold_pool, 6 - len(h_pick))
            picked = h_pick + c_pick
            
        else: # 전체 가중치 랜덤
            weights = [counts.get(n, 0) + 1 for n in range(1, 46)]
            pool = list(range(1, 46))
            picked_set = set()
            t_pool = pool[:]
            t_weights = weights[:]
            while len(picked_set) < 6:
                c = random.choices(t_pool, weights=t_weights, k=1)[0]
                if c not in picked_set:
                    picked_set.add(c)
                    idx = t_pool.index(c)
                    t_pool.pop(idx)
                    t_weights.pop(idx)
            picked = list(picked_set)

        st.write(f"**{i}게임** ({strategy.split()[1]})")
        render_balls(picked)
