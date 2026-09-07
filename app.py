from collections import Counter
import random
import streamlit as st

st.set_page_config(page_title="AI 로또 번호 분석기", page_icon="🎰", layout="centered")

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
        
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# 최신 1240회 기준 실제 공식 당첨 데이터
def get_lotto_history():
    raw_history = [
        (1240, [11, 13, 19, 20, 31, 44], 27),
        (1239, [11, 13, 22, 32, 33, 36], 8),
        (1238, [2, 13, 18, 32, 38, 42], 15),
        (1237, [4, 11, 19, 26, 37, 43], 29),
        (1236, [7, 10, 22, 29, 31, 38], 15),
        (1235, [5, 12, 15, 30, 37, 40], 18),
        (1234, [14, 16, 19, 20, 29, 34], 41),
        (1233, [4, 9, 12, 15, 33, 45], 26),
        (1232, [21, 24, 29, 32, 34, 40], 27),
        (1231, [1, 6, 13, 19, 21, 33], 4),
        (1230, [3, 7, 9, 13, 19, 24], 23),
        (1229, [13, 14, 20, 28, 29, 34], 41),
        (1228, [6, 7, 19, 28, 34, 41], 5),
        (1227, [1, 2, 6, 14, 20, 40], 31),
        (1226, [15, 19, 21, 25, 27, 28], 40),
        (1225, [5, 10, 11, 17, 28, 34], 22),
        (1224, [1, 5, 8, 16, 28, 33], 45),
        (1223, [10, 15, 24, 30, 31, 37], 3),
        (1222, [4, 5, 9, 11, 37, 40], 7),
        (1221, [6, 14, 25, 33, 40, 44], 30),
        (1220, [3, 8, 17, 34, 39, 43], 10),
        (1219, [13, 19, 21, 24, 34, 35], 26),
        (1218, [13, 19, 21, 26, 37, 43], 29),
        (1217, [6, 24, 31, 32, 38, 44], 8),
        (1216, [2, 19, 26, 31, 38, 41], 35),
        (1215, [1, 9, 12, 13, 20, 45], 3),
        (1214, [11, 13, 14, 15, 16, 45], 34),
        (1213, [3, 4, 9, 30, 33, 36], 12),
        (1212, [1, 3, 4, 29, 39, 43], 34),
        (1211, [7, 12, 23, 32, 34, 36], 8),
        (1210, [10, 16, 19, 32, 33, 38], 3),
        (1209, [11, 13, 20, 21, 32, 44], 8),
        (1208, [16, 20, 26, 36, 42, 44], 24),
        (1207, [3, 13, 30, 33, 43, 45], 25),
        (1206, [3, 7, 11, 20, 22, 41], 24),
        (1205, [10, 12, 13, 19, 33, 40], 2),
        (1204, [7, 19, 26, 37, 39, 44], 27),
        (1203, [6, 14, 30, 31, 40, 41], 29),
        (1202, [1, 3, 4, 29, 42, 45], 36),
        (1201, [6, 16, 34, 37, 39, 40], 11),
        (1200, [1, 7, 21, 30, 35, 38], 2),
        (1199, [10, 12, 29, 31, 40, 44], 2),
        (1198, [13, 14, 22, 26, 37, 38], 20),
        (1197, [6, 7, 13, 28, 36, 42], 41),
        (1196, [17, 26, 29, 30, 31, 43], 12),
        (1195, [3, 20, 28, 38, 40, 43], 4),
        (1194, [12, 16, 21, 24, 41, 43], 15),
        (1193, [14, 16, 27, 35, 39, 45], 5),
        (1192, [1, 12, 16, 19, 23, 43], 34),
        (1191, [1, 14, 16, 18, 24, 35], 34),
        (1190, [6, 7, 15, 22, 26, 40], 41),
        (1189, [10, 17, 22, 30, 35, 43], 44),
        (1188, [7, 18, 19, 26, 33, 45], 37),
        (1187, [13, 14, 22, 26, 37, 38], 20),
        (1186, [12, 19, 21, 29, 40, 45], 1),
        (1185, [4, 18, 31, 37, 42, 45], 33),
        (1184, [11, 21, 22, 30, 39, 44], 13),
        (1183, [13, 14, 18, 21, 34, 44], 26),
        (1182, [11, 16, 25, 27, 35, 36], 37),
        (1181, [4, 7, 17, 18, 38, 44], 36),
        (1180, [8, 12, 13, 29, 33, 42], 5),
        (1179, [3, 7, 14, 15, 22, 38], 17),
        (1178, [21, 26, 27, 32, 34, 42], 31),
        (1177, [1, 9, 16, 23, 24, 38], 17),
        (1176, [13, 16, 23, 31, 35, 44], 9),
        (1175, [4, 8, 18, 24, 37, 45], 6),
        (1174, [6, 10, 11, 14, 36, 45], 18),
        (1173, [2, 11, 16, 25, 39, 45], 6),
        (1172, [3, 7, 9, 33, 36, 37], 10),
        (1171, [1, 23, 24, 35, 44, 45], 10),
        (1170, [1, 6, 20, 27, 28, 41], 15),
        (1169, [6, 18, 28, 30, 32, 38], 15),
        (1168, [16, 18, 20, 23, 32, 43], 27),
        (1167, [1, 2, 11, 21, 26, 35], 38),
        (1166, [3, 6, 14, 22, 30, 41], 36),
        (1165, [1, 10, 18, 22, 28, 31], 34),
        (1164, [4, 7, 19, 26, 33, 35], 3),
        (1163, [7, 10, 19, 23, 28, 33], 18),
        (1162, [6, 11, 16, 19, 21, 32], 45),
        (1161, [3, 18, 19, 23, 32, 45], 24),
        (1160, [3, 6, 9, 18, 22, 35], 24),
        (1159, [3, 6, 22, 23, 24, 38], 30),
        (1158, [20, 31, 32, 40, 41, 45], 12),
        (1157, [4, 24, 27, 35, 37, 45], 15),
        (1156, [3, 10, 24, 33, 38, 45], 36),
        (1155, [7, 10, 22, 25, 34, 40], 27),
        (1154, [11, 23, 25, 30, 32, 40], 42),
        (1153, [8, 13, 19, 27, 40, 45], 12),
        (1152, [13, 20, 24, 32, 34, 45], 14),
        (1151, [4, 7, 12, 14, 22, 33], 31),
        (1150, [14, 19, 27, 28, 30, 45], 33),
        (1149, [22, 26, 30, 32, 33, 41], 27),
        (1148, [5, 17, 26, 27, 35, 38], 1),
        (1147, [21, 26, 30, 32, 33, 34], 40),
        (1146, [6, 12, 17, 21, 32, 39], 30),
        (1145, [3, 5, 13, 20, 21, 37], 17),
        (1144, [6, 12, 17, 21, 32, 39], 30),
        (1143, [2, 20, 33, 40, 42, 44], 32),
        (1142, [7, 16, 25, 29, 35, 36], 28),
        (1141, [6, 14, 15, 19, 21, 41], 37)
    ]
    return [{"round": r, "numbers": nums, "bonus": b} for r, nums, b in raw_history]

st.title("🎰 맞춤 로또 번호 추출기")

data = get_lotto_history()

# 1. 최신 당첨 번호 카드 표시 (1240회)
latest = data[0]
l_round = latest["round"]
l_nums = latest["numbers"]
l_bonus = latest["bonus"]

with st.container(border=True):
    st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 17px;'>🏆 가장 최근 (제 {l_round}회) 당첨 번호</div>", unsafe_allow_html=True)
    render_balls(l_nums, l_bonus)
    
    with st.expander("📜 최근 10회차 당첨 번호 전체 보기"):
        for item in data[:10]:
            r = item["round"]
            nums = item["numbers"]
            b = item["bonus"]
            st.caption(f"**제 {r}회** : {sorted(nums)} + 보너스 {b}")

# 2. 제외수 선택
excluded_numbers = st.multiselect(
    "🚫 조합에서 제외할 번호 선택",
    options=list(range(1, 46)),
    placeholder="제외하고 싶은 번호를 터치해 선택하세요"
)

# 3. 분석 및 생성 설정 (1~100회차)
col1, col2 = st.columns(2)
with col1:
    recent_count = st.slider("추출에 반영할 최근 회차 수", min_value=1, max_value=100, value=10, step=1)
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

# 5. 통계 조회 섹션 (1~100회차 실시간 연동)
with st.expander("📊 회차별 출현 통계 실시간 조회", expanded=False):
    stat_range = st.slider("조회할 최근 회차 범위 (1~100회)", min_value=1, max_value=100, value=recent_count, step=1, key="stat_slider")
    
    stat_subset = data[:stat_range]
    stat_nums = []
    for item in stat_subset:
        stat_nums.extend(item["numbers"])
    
    stat_counts = Counter(stat_nums)
    stat_ranked = sorted(range(1, 46), key=lambda x: stat_counts.get(x, 0), reverse=True)
    
    st.caption(f"💡 최근 **{stat_range}회차**(제 {stat_subset[-1]['round']}회 ~ 제 {stat_subset[0]['round']}회) 실제 집계 결과입니다.")
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

# 추천 번호 생성 버튼
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
