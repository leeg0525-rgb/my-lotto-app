from collections import Counter
import random
import requests
import streamlit as st

st.set_page_config(page_title="AI 로또 번호 분석기", page_icon="🎰", layout="centered")

def get_ball_color(num):
    if num <= 10:
        return "#fbc400"
    elif num <= 20:
        return "#69c8f2"
    elif num <= 30:
        return "#ff7272"
    elif num <= 40:
        return "#aaaaaa"
    else:
        return "#b0d840"

def render_balls(numbers, bonus=None):
    html = '<div style="display: flex; gap: 8px; justify-content: center; align-items: center; margin: 10px 0;">'
    for n in sorted(numbers):
        color = get_ball_color(n)
        html += f'<div style="background-color: {color}; color: white; font-weight: bold; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{n}</div>'
    
    if bonus:
        html += '<div style="font-size: 20px; font-weight: bold; color: #888; margin: 0 4px;">+</div>'
        b_color = get_ball_color(bonus)
        html += f'<div style="background-color: {b_color}; color: white; font-weight: bold; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{bonus}</div>'
        
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# 100회차 이상의 전체 실제 당첨 데이터 불러오기 (캐싱 6시간)
@st.cache_data(ttl=21600)
def load_lotto_data():
    """안정적인 공개 로또 데이터셋 로드"""
    url_list = [
        "https://raw.githubusercontent.com/lee-gook/lotto-data/main/lotto.json",
        "https://raw.githubusercontent.com/seose/lotto/main/lotto.json",
        "https://raw.githubusercontent.com/jonghwan-park/lotto-history/main/data.json"
    ]
    for url in url_list:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                raw = res.json()
                data_list = []
                # 리스트 또는 딕셔너리 포맷 정규화
                items = raw if isinstance(raw, list) else list(raw.values())
                for item in items:
                    r = item.get("round") or item.get("drwNo")
                    if not r:
                        continue
                    nums = item.get("numbers") or [item[f"drwtNo{i}"] for i in range(1, 7) if f"drwtNo{i}" in item]
                    b = item.get("bonus") or item.get("bnusNo")
                    if len(nums) == 6:
                        data_list.append({"round": int(r), "numbers": [int(x) for x in nums], "bonus": int(b) if b else None})
                if len(data_list) >= 50:
                    return sorted(data_list, key=lambda x: x["round"], reverse=True)
        except Exception:
            continue

    # 백업: 동행복권 API에서 최신 100회차 역순 크롤링
    try:
        # 기준 최신 회차 추정 (1140회 기준)
        base_round = 1140
        fetched = []
        for r in range(base_round, base_round - 100, -1):
            api_url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={r}"
            res = requests.get(api_url, timeout=3)
            if res.status_code == 200:
                d = res.json()
                if d.get("returnValue") == "success":
                    nums = [d[f"drwtNo{i}"] for i in range(1, 7)]
                    fetched.append({"round": r, "numbers": nums, "bonus": d.get("bnusNo")})
        if fetched:
            return fetched
    except Exception:
        pass

    return []

st.title("🎰 맞춤 로또 번호 추출기")

data = load_lotto_data()

# 데이터 로드 실패 방지
if not data:
    st.error("당첨 데이터를 불러오는 중입니다. 잠시 후 새로고침해 주세요.")
    st.stop()

# 1. 최근 당첨 번호 표시
latest = data[0]
l_round = latest["round"]
l_nums = latest["numbers"]
l_bonus = latest.get("bonus")

with st.container(border=True):
    st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 17px;'>🏆 가장 최근 (제 {l_round}회) 당첨 번호</div>", unsafe_allow_html=True)
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
    placeholder="제외하고 싶은 번호를 터치해 선택하세요"
)

# 3. 분석 옵션 설정
max_available = min(100, len(data))
col1, col2 = st.columns(2)
with col1:
    recent_count = st.slider("추출에 반영할 최근 회차 수", min_value=1, max_value=max_available, value=min(10, max_available), step=1)
with col2:
    game_count = st.slider("생성할 게임 수", min_value=1, max_value=10, value=5)

# 4. 전략 선택
strategy = st.radio(
    "어떤 방식으로 번호를 뽑을까요?",
    [
        "🔥 요즘 잘 나오는 번호만 뽑기",
        "⚡ 반반 섞기 (자주 나온 수 3개 + 안 나온 수 3개)",
        "❄️ 최근 안 나온 번호만 뽑기 (역발상)",
        "🎲 확률 비례 골고루 뽑기"
    ]
)

# 5. 통계 조회 전용 섹션 (실제 1~100회차 연동)
with st.expander("📊 회차별 출현 통계 실시간 조회", expanded=False):
    stat_range = st.slider("조회할 최근 회차 범위 (1~100회)", min_value=1, max_value=max_available, value=recent_count, step=1, key="stat_slider")
    
    # 선택 회차 기준으로 카운팅
    stat_subset = data[:stat_range]
    stat_nums = []
    for item in stat_subset:
        stat_nums.extend(item["numbers"])
    
    stat_counts = Counter(stat_nums)
    stat_ranked = sorted(range(1, 46), key=lambda x: stat_counts.get(x, 0), reverse=True)
    
    st.caption(f"💡 최근 **{stat_range}회차**(제 {stat_subset[-1]['round']}회 ~ 제 {stat_subset[0]['round']}회) 집계 결과입니다.")
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
ranked_available = sorted(available_pool, key=lambda x: counts.get(x, 0), reverse=True)

appeared_nums = [n for n in ranked_available if counts.get(n, 0) > 0]
not_appeared_nums = [n for n in ranked_available if counts.get(n, 0) == 0]

hot_pool = appeared_nums if len(appeared_nums) >= 6 else ranked_available[:max(6, len(ranked_available))]
cold_pool = not_appeared_nums if len(not_appeared_nums) >= 6 else ranked_available[-max(6, len(ranked_available)):]

# 추천 번호 뽑기
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
