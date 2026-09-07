from collections import Counter
from datetime import datetime
import random
import time
import requests
import streamlit as st

st.set_page_config(
    page_title="AI 로또 번호 분석기", page_icon="🎰", layout="centered"
)


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


def render_balls(numbers, bonus=None):
    html = '<div style="display: flex; gap: 8px; justify-content: center; align-items: center; margin: 10px 0;">'
    for n in sorted(numbers):
        color = get_ball_color(n)
        html += f'<div style="background-color: {color}; color: white; font-weight: bold; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{n}</div>'

    if bonus:
        html += '<div style="font-size: 20px; font-weight: bold; color: #888; margin: 0 4px;">+</div>'
        b_color = get_ball_color(bonus)
        html += f'<div style="background-color: {b_color}; color: white; font-weight: bold; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{bonus}</div>'

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# 1회차(2002-12-07 20:45) 기준 최신 추첨 회차 계산
def get_estimated_latest_drw():
    first_drw_date = datetime(2002, 12, 7, 20, 45)
    diff_days = (datetime.now() - first_drw_date).days
    return (diff_days // 7) + 1


# 동행복권 공식 서버에서 실제 최근 100회차 수집 (1시간 캐싱)
@st.cache_data(ttl=3600, show_spinner="최신 로또 100회차 데이터를 동기화 중입니다...")
def sync_latest_lotto_history(count=100):
    latest_drw = get_estimated_latest_drw()
    headers = {"User-Agent": "Mozilla/5.0"}
    session = requests.Session()
    session.headers.update(headers)

    results = []

    # 최신 회차부터 역순으로 탐색
    for drw in range(latest_drw + 1, max(1, latest_drw - count - 5), -1):
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drw}"
        try:
            res = session.get(url, timeout=3)
            if res.status_code == 200:
                data = res.json()
                if data.get("returnValue") == "success":
                    nums = [data[f"drwtNo{i}"] for i in range(1, 7)]
                    bonus = data.get("bnusNo")
                    results.append(
                        {
                            "round": data["drwNo"],
                            "date": data.get("drwNoDate"),
                            "numbers": nums,
                            "bonus": bonus,
                        }
                    )
                    if len(results) >= count:
                        break
        except Exception:
            continue
        time.sleep(0.04)

    return results


st.title("🎰 맞춤 로또 번호 추출기")

data = sync_latest_lotto_history()

if not data:
    st.error(
        "로또 데이터를 불러올 수 없습니다. 인터넷 연결 및 동행복권 서버 상태를 확인해 주세요."
    )
    st.stop()

# 1. 최신 당첨 번호 카드
latest = data[0]
l_round = latest["round"]
l_nums = latest["numbers"]
l_bonus = latest.get("bonus")

with st.container(border=True):
    st.markdown(
        f"<div style='text-align: center; font-weight: bold; font-size: 17px;'>🏆 가장 최근 (제 {l_round}회) 당첨 번호</div>",
        unsafe_allow_html=True,
    )
    render_balls(l_nums, l_bonus)

    with st.expander("📜 최근 10회차 당첨 번호 전체 보기"):
        for item in data[:10]:
            r = item["round"]
            nums = item["numbers"]
            b = item.get("bonus")
            b_str = f" + 보너스 {b}" if b else ""
            st.caption(f"**제 {r}회** : {sorted(nums)}{b_str}")

# 2. 제외수 선택
excluded_numbers = st.multiselect(
    "🚫 조합에서 제외할 번호 선택",
    options=list(range(1, 46)),
    placeholder="제외하고 싶은 번호를 터치해 선택하세요",
)

# 3. 분석 및 생성 설정 (1~100회차)
max_available = len(data)
col1, col2 = st.columns(2)
with col1:
    recent_count = st.slider(
        "추출에 반영할 최근 회차 수",
        min_value=1,
        max_value=max_available,
        value=min(10, max_available),
        step=1,
    )
with col2:
    game_count = st.slider("생성할 게임 수", min_value=1, max_value=10, value=5)

# 4. 전략 선택
strategy = st.radio(
    "어떤 방식으로 번호를 뽑을까요?",
    [
        "🔥 요즘 잘 나오는 번호만 뽑기",
        "⚡ 반반 섞기 (자주 나온 수 3개 + 안 나온 수 3개)",
        "❄️ 최근 안 나온 번호만 뽑기 (역발상)",
        "🎲 확률 비례 골고루 뽑기",
    ],
)

# 5. 통계 조회 섹션 (1~100회차 실시간 연동)
with st.expander("📊 회차별 출현 통계 실시간 조회", expanded=False):
    stat_range = st.slider(
        f"조회할 최근 회차 범위 (1~{max_available}회)",
        min_value=1,
        max_value=max_available,
        value=recent_count,
        step=1,
        key="stat_slider",
    )

    stat_subset = data[:stat_range]
    stat_nums = []
    for item in stat_subset:
        stat_nums.extend(item["numbers"])

    stat_counts = Counter(stat_nums)
    stat_ranked = sorted(
        range(1, 46), key=lambda x: stat_counts.get(x, 0), reverse=True
    )

    st.caption(
        f"💡 최근 **{stat_range}회차**(제 {stat_subset[-1]['round']}회 ~ 제 {stat_subset[0]['round']}회) 실제 집계 결과입니다."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🔥 많이 나온 번호 (상위 6개)**")
        for num in stat_ranked[:6]:
            st.write(f"- **{num}번** ({stat_counts.get(num, 0)}회 출현)")
    with c2:
        st.markdown("**❄️ 안 나온 번호 (하위 6개)**")
        for num in stat_ranked[-6:]:
            st.write(f"- **{num}번** ({stat_counts.get(num, 0)}회 출현)")

# 추천 번호 생성용 계산
extract_subset = data[:recent_count]
all_numbers = []
for item in extract_subset:
    all_numbers.extend(item["numbers"])

counts = Counter(all_numbers)
available_pool = [n for n in range(1, 46) if n not in excluded_numbers]
ranked_available = sorted(
    available_pool, key=lambda x: counts.get(x, 0), reverse=True
)

appeared_nums = [n for n in ranked_available if counts.get(n, 0) > 0]
not_appeared_nums = [n for n in ranked_available if counts.get(n, 0) == 0]

hot_pool = (
    appeared_nums
    if len(appeared_nums) >= 6
    else ranked_available[: max(6, len(ranked_available))]
)
cold_pool = (
    not_appeared_nums
    if len(not_appeared_nums) >= 6
    else ranked_available[-max(6, len(ranked_available)) :]
)

# 추천 번호 생성 버튼
if st.button("🎲 추천 번호 뽑기", use_container_width=True, type="primary"):
    if len(available_pool) < 6:
        st.error(
            "제외된 번호가 너무 많아 6개 번호를 구성할 수 없습니다. 제외수를 줄여주세요."
        )
    else:
        st.subheader("🎯 생성된 추천 번호")
        if excluded_numbers:
            st.caption(f"제외된 번호: {sorted(excluded_numbers)}")

        for i in range(1, game_count + 1):
            if "요즘 잘 나오는" in strategy:
                pick_pool = (
                    hot_pool if len(hot_pool) >= 6 else ranked_available[:12]
                )
                picked = random.sample(pick_pool, min(6, len(pick_pool)))
                if len(picked) < 6:
                    remain = [n for n in available_pool if n not in picked]
                    picked += random.sample(remain, 6 - len(picked))

            elif "최근 안 나온" in strategy:
                pick_pool = (
                    cold_pool if len(cold_pool) >= 6 else ranked_available[-12:]
                )
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
