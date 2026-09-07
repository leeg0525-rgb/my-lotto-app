from collections import Counter
from datetime import datetime
import json
import random
import urllib.request
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
    html = '<div style="display: flex; gap: 8px; justify-content: center; align-items: center; margin: 8px 0;">'
    for n in sorted(numbers):
        color = get_ball_color(n)
        html += f'<div style="background-color: {color}; color: white; font-weight: bold; border-radius: 50%; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; font-size: 15px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{n}</div>'
    if bonus:
        html += '<div style="font-size: 18px; font-weight: bold; color: #888; margin: 0 4px;">+</div>'
        b_color = get_ball_color(bonus)
        html += f'<div style="background-color: {b_color}; color: white; font-weight: bold; border-radius: 50%; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; font-size: 15px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{bonus}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# 1240회 ~ 1141회 실데이터 내장 베이스
BASE_DATA = [
    (1240, [11, 13, 19, 20, 31, 44], 27), (1239, [11, 13, 22, 32, 33, 36], 8),
    (1238, [2, 13, 18, 32, 38, 42], 22), (1237, [10, 20, 23, 34, 37, 40], 36),
    (1236, [12, 18, 21, 29, 34, 38], 10), (1235, [6, 7, 11, 15, 39, 43], 20),
    (1234, [1, 15, 19, 31, 35, 43], 27), (1233, [2, 7, 20, 25, 37, 40], 29),
    (1232, [12, 15, 19, 22, 24, 36], 3), (1231, [4, 13, 14, 18, 31, 38], 15),
    (1230, [3, 8, 9, 22, 28, 42], 45), (1229, [12, 13, 29, 34, 37, 42], 16),
    (1228, [24, 29, 30, 31, 35, 44], 1), (1227, [1, 14, 16, 34, 41, 44], 13),
    (1226, [4, 6, 13, 17, 26, 28], 41), (1225, [8, 9, 19, 25, 41, 42], 33),
    (1224, [9, 18, 21, 27, 44, 45], 28), (1223, [16, 18, 20, 32, 33, 39], 26),
    (1222, [4, 11, 17, 22, 32, 41], 34), (1221, [6, 13, 18, 28, 30, 36], 9),
    (1220, [2, 22, 25, 28, 34, 43], 16), (1219, [1, 2, 15, 28, 39, 45], 31),
    (1218, [3, 28, 31, 32, 42, 45], 25), (1217, [8, 10, 15, 20, 29, 31], 41),
    (1216, [3, 10, 14, 15, 23, 24], 25), (1215, [13, 15, 19, 21, 44, 45], 39),
    (1214, [10, 15, 19, 27, 30, 33], 14), (1213, [5, 11, 25, 27, 36, 38], 2),
    (1212, [5, 8, 25, 31, 41, 44], 45), (1211, [23, 26, 27, 35, 38, 40], 10),
    (1210, [1, 7, 9, 17, 27, 38], 31), (1209, [2, 17, 20, 35, 37, 39], 24),
    (1208, [6, 27, 30, 36, 38, 42], 25), (1207, [10, 22, 24, 27, 38, 45], 11),
    (1206, [1, 3, 17, 26, 27, 42], 23), (1205, [1, 4, 16, 23, 31, 41], 2),
    (1204, [8, 16, 28, 30, 31, 44], 27), (1203, [3, 6, 18, 29, 35, 39], 24),
    (1202, [5, 12, 21, 33, 37, 40], 7), (1201, [7, 9, 24, 27, 35, 36], 37),
    (1200, [1, 2, 4, 16, 20, 32], 45), (1199, [16, 24, 25, 30, 31, 32], 7),
    (1198, [26, 30, 33, 38, 39, 41], 21), (1197, [1, 5, 7, 26, 28, 43], 30),
    (1196, [8, 12, 15, 29, 40, 45], 14), (1195, [3, 15, 27, 33, 34, 36], 37),
    (1194, [3, 13, 15, 24, 33, 37], 2), (1193, [6, 9, 16, 19, 24, 28], 17),
    (1192, [10, 16, 23, 36, 39, 40], 11), (1191, [1, 4, 11, 12, 20, 41], 2),
    (1190, [7, 9, 19, 23, 26, 45], 33), (1189, [9, 19, 29, 35, 37, 38], 31),
    (1188, [3, 4, 12, 19, 22, 27], 9), (1187, [5, 13, 26, 29, 37, 40], 42),
    (1186, [2, 8, 13, 16, 23, 28], 35), (1185, [6, 17, 22, 28, 29, 32], 38),
    (1184, [14, 16, 23, 25, 31, 37], 42), (1183, [4, 15, 17, 23, 27, 36], 31),
    (1182, [1, 13, 21, 25, 28, 31], 22), (1181, [8, 10, 14, 20, 33, 41], 28),
    (1180, [6, 12, 18, 37, 40, 41], 3), (1179, [3, 16, 18, 24, 40, 44], 21),
    (1178, [5, 6, 11, 27, 43, 44], 17), (1177, [3, 7, 15, 16, 19, 43], 21),
    (1176, [7, 9, 11, 21, 30, 35], 29), (1175, [3, 4, 6, 8, 32, 42], 31),
    (1174, [8, 11, 14, 17, 36, 39], 22), (1173, [1, 5, 18, 20, 30, 35], 3),
    (1172, [7, 9, 24, 40, 42, 44], 45), (1171, [3, 6, 7, 11, 12, 17], 19),
    (1170, [3, 13, 28, 34, 38, 42], 25), (1169, [5, 12, 24, 26, 39, 42], 20),
    (1168, [9, 21, 24, 30, 33, 37], 29), (1167, [8, 23, 31, 35, 39, 40], 24),
    (1166, [14, 23, 25, 27, 29, 42], 16), (1165, [6, 7, 27, 29, 38, 45], 17),
    (1164, [17, 18, 23, 25, 38, 39], 22), (1163, [2, 13, 15, 16, 33, 43], 4),
    (1162, [20, 21, 22, 25, 28, 29], 6), (1161, [2, 12, 20, 24, 34, 42], 37),
    (1160, [7, 13, 18, 36, 39, 45], 19), (1159, [3, 9, 27, 28, 38, 39], 7),
    (1158, [21, 25, 27, 32, 37, 38], 20), (1157, [5, 7, 12, 20, 25, 26], 28),
    (1156, [30, 31, 34, 39, 41, 45], 7), (1155, [10, 16, 19, 27, 37, 38], 13),
    (1154, [4, 8, 22, 26, 32, 38], 27), (1153, [1, 9, 10, 13, 35, 44], 5),
    (1152, [30, 31, 32, 35, 36, 37], 5), (1151, [2, 3, 9, 15, 27, 29], 8),
    (1150, [8, 9, 18, 35, 39, 45], 25), (1149, [8, 15, 19, 21, 32, 36], 38),
    (1148, [3, 6, 13, 15, 16, 22], 32), (1147, [7, 11, 24, 26, 27, 37], 32),
    (1146, [6, 11, 17, 19, 40, 43], 28), (1145, [2, 11, 31, 33, 37, 44], 32),
    (1144, [3, 4, 12, 15, 26, 34], 6), (1143, [10, 16, 17, 27, 28, 36], 6),
    (1142, [2, 8, 28, 30, 37, 41], 22), (1141, [7, 11, 12, 21, 26, 35], 20)
]

def get_current_max_drw():
    first_drw_date = datetime(2002, 12, 7, 20, 45)
    diff_days = (datetime.now() - first_drw_date).days
    return (diff_days // 7) + 1

def fetch_single_drw(drw_no):
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drw_no}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            d = json.loads(resp.read().decode("utf-8"))
            if d.get("returnValue") == "success":
                return (d["drwNo"], [d[f"drwtNo{i}"] for i in range(1, 7)], d.get("bnusNo"))
    except Exception:
        pass
    return None

@st.cache_data(ttl=1800, show_spinner=False)
def get_updated_lotto_data():
    data_list = list(BASE_DATA)
    last_known = data_list[0][0]
    expected_drw = get_current_max_drw()

    if expected_drw > last_known:
        for check_drw in range(last_known + 1, expected_drw + 1):
            new_item = fetch_single_drw(check_drw)
            if new_item:
                data_list.insert(0, new_item)
            else:
                break
    return [{"round": r, "numbers": nums, "bonus": b} for r, nums, b in data_list[:100]]

# 세션 상태 초기화 (내 저장 번호 목록 & 방금 생성된 추천 번호)
if "my_saved_tickets" not in st.session_state:
    st.session_state.my_saved_tickets = []
if "last_generated_games" not in st.session_state:
    st.session_state.last_generated_games = []

data = get_updated_lotto_data()
latest_round = data[0]["round"]
target_next_round = latest_round + 1  # 이번에 도전할 다음 회차

st.title("🎰 맞춤 로또 번호 추출기")

# 1. 최신 당첨 번호 카드
latest = data[0]
with st.container(border=True):
    st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 17px;'>🏆 가장 최근 (제 {latest['round']}회) 실제 공식 당첨 번호</div>", unsafe_allow_html=True)
    render_balls(latest["numbers"], latest.get("bonus"))
    
    with st.expander("📜 최근 10회차 실제 당첨 번호 보기"):
        for item in data[:10]:
            b_str = f" + 보너스 {item.get('bonus')}" if item.get("bonus") else ""
            st.caption(f"**제 {item['round']}회** : {sorted(item['numbers'])}{b_str}")

# 2. 내 저장 번호 보관함 (상단 요약)
saved_cnt = len(st.session_state.my_saved_tickets)
with st.expander(f"📁 나의 저장 번호 보관함 ({saved_cnt}개 저장됨)", expanded=saved_cnt > 0):
    if not st.session_state.my_saved_tickets:
        st.info("아직 저장된 번호가 없습니다. 아래에서 추천 번호를 뽑고 [저장] 버튼을 눌러보세요.")
    else:
        for idx, ticket in enumerate(st.session_state.my_saved_tickets):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**[{ticket['round']}회차 도전]** {ticket['name']} ({ticket['time']})")
                render_balls(ticket["numbers"])
            with c2:
                if st.button("🗑️ 삭제", key=f"del_{idx}"):
                    st.session_state.my_saved_tickets.pop(idx)
                    st.rerun()
        if st.button("전체 삭제", type="secondary"):
            st.session_state.my_saved_tickets = []
            st.rerun()

# 3. 추천 번호 추출 설정
excluded_numbers = st.multiselect("🚫 조합에서 제외할 번호 선택", options=list(range(1, 46)), placeholder="제외수를 터치해 선택하세요")

max_available = len(data)
col1, col2 = st.columns(2)
with col1:
    recent_count = st.slider("추출에 반영할 최근 회차 수", min_value=1, max_value=max_available, value=min(10, max_available), step=1)
with col2:
    game_count = st.slider("생성할 게임 수", min_value=1, max_value=10, value=5)

strategy = st.radio("어떤 방식으로 번호를 뽑을까요?", [
    "🔥 요즘 잘 나오는 번호만 뽑기",
    "⚡ 반반 섞기 (자주 나온 수 3개 + 안 나온 수 3개)",
    "❄️ 최근 안 나온 번호만 뽑기 (역발상)",
    "🎲 확률 비례 골고루 뽑기"
])

# 통계 분석 풀 계산
extract_subset = data[:recent_count]
all_numbers = [n for item in extract_subset for n in item["numbers"]]
counts = Counter(all_numbers)
available_pool = [n for n in range(1, 46) if n not in excluded_numbers]
ranked_available = sorted(available_pool, key=lambda x: counts.get(x, 0), reverse=True)
appeared_nums = [n for n in ranked_available if counts.get(n, 0) > 0]
not_appeared_nums = [n for n in ranked_available if counts.get(n, 0) == 0]

hot_pool = appeared_nums if len(appeared_nums) >= 6 else ranked_available[:max(6, len(ranked_available))]
cold_pool = not_appeared_nums if len(not_appeared_nums) >= 6 else ranked_available[-max(6, len(ranked_available)):]

# 추천 번호 생성 버튼
if st.button("🎲 추천 번호 뽑기", use_container_width=True, type="primary"):
    if len(available_pool) < 6:
        st.error("제외수가 너무 많아 6개 번호를 구성할 수 없습니다.")
    else:
        generated = []
        for i in range(1, game_count + 1):
            if "요즘 잘 나오는" in strategy:
                pick_pool = hot_pool if len(hot_pool) >= 6 else ranked_available[:12]
                picked = random.sample(pick_pool, min(6, len(pick_pool)))
            elif "최근 안 나온" in strategy:
                pick_pool = cold_pool if len(cold_pool) >= 6 else ranked_available[-12:]
                picked = random.sample(pick_pool, min(6, len(pick_pool)))
            elif "반반 섞기" in strategy:
                h_k = min(3, len(hot_pool))
                h_pick = random.sample(hot_pool, h_k)
                c_pool = [n for n in cold_pool if n not in h_pick]
                c_k = min(6 - len(h_pick), len(c_pool))
                picked = h_pick + random.sample(c_pool, c_k)
            else:
                weights = [counts.get(n, 0) + 1 for n in available_pool]
                t_pool, t_weights = available_pool[:], weights[:]
                p_set = set()
                while len(p_set) < 6 and t_pool:
                    c = random.choices(t_pool, weights=t_weights, k=1)[0]
                    p_set.add(c)
                    idx = t_pool.index(c)
                    t_pool.pop(idx)
                    t_weights.pop(idx)
                picked = list(p_set)

            if len(picked) < 6:
                remain = [n for n in available_pool if n not in picked]
                picked += random.sample(remain, 6 - len(picked))
            
            generated.append(sorted(picked))
        st.session_state.last_generated_games = generated

# 생성된 번호 출력 및 개별 저장 버튼
if st.session_state.last_generated_games:
    st.subheader(f"🎯 제 {target_next_round}회 추천 조합")
    for i, nums in enumerate(st.session_state.last_generated_games, start=1):
        with st.container(border=True):
            col_b, col_btn = st.columns([3, 2])
            with col_b:
                st.markdown(f"**{i}게임**")
                render_balls(nums)
            with col_btn:
                save_btn = st.button(f"💾 {target_next_round}회차로 저장", key=f"save_{i}_{nums}")
                if save_btn:
                    ticket_info = {
                        "round": target_next_round,
                        "name": f"{i}번째 조합",
                        "numbers": nums,
                        "time": datetime.now().strftime("%m-%d %H:%M")
                    }
                    st.session_state.my_saved_tickets.append(ticket_info)
                    st.success(f"제 {target_next_round}회차 목록에 저장되었습니다!")
                    st.rerun()
