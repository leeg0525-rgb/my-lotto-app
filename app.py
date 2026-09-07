from collections import Counter
import csv
import os
import random
import streamlit as st

st.set_page_config(
    page_title="AI 로또 번호 분석기", page_icon="🎰", layout="centered"
)


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


# GitHub 저장소에 올라온 실제 CSV 파일 읽기
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "real_lotto_100.csv")


@st.cache_data
def load_lotto_data():
    records = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = list(csv.reader(f))
            if len(reader) > 1:
                for row in reader[1:]:
                    try:
                        records.append(
                            {
                                "round": int(row[0]),
                                "numbers": [int(x) for x in row[1:7]],
                                "bonus": int(row[7]),
                            }
                        )
                    except Exception:
                        continue
    records.sort(key=lambda x: x["round"], reverse=True)
    return records


st.title("🎰 맞춤 로또 번호 추출기")

data = load_lotto_data()

if not data:
    st.error(
        "저장소에 'real_lotto_100.csv' 파일이 없습니다. GitHub에 파일을"
        " 업로드해주세요."
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

# 3. 분석 및 생성 설정
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

# 5. 통계 조회 섹션
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

# 추천 번호 생성 계산
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

# 번호 생성 버튼
if st.button("🎲 추천 번호 뽑기", use_container_width=True, type="primary"):
    if len(available_pool) < 6:
        st.error(
            "제외된 번호가 너무 많아 6개 번호를 구성할 수 없습니다. 제외수를"
            " 줄여주세요."
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
