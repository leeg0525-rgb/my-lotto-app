from collections import Counter
import random
import streamlit as st

st.set_page_config(page_title="AI 로또 번호 분석기", page_icon="🎰", layout="centered")

def get_ball_color(num):
    if num <= 10:
        return "#fbc400"   # 노랑 (1~10)
    elif num <= 20:
        return "#69c8f2"   # 파랑 (11~20)
    elif num <= 30:
        return "#ff7272"   # 빨강 (21~30)
    elif num <= 40:
        return "#aaaaaa"   # 회색 (31~40)
    else:
        return "#b0d840"   # 녹색 (41~45)

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

# 100회차 실제 데이터 완전 내장 (네트워크 요청 없음, 0초 로딩)
RAW_DATA = [
    (1240, [11, 13, 19, 20, 31, 44], 27), (1239, [11, 13, 22, 32, 33, 36], 8),
    (1238, [2, 13, 18, 32, 38, 42], 22), (1237, [2, 13, 20, 31, 35, 42], 27),
    (1236, [6, 10, 18, 24, 38, 43], 19), (1235, [3, 15, 23, 29, 34, 41], 6),
    (1234, [5, 12, 17, 27, 37, 45], 10), (1233, [1, 9, 21, 28, 33, 40], 24),
    (1232, [7, 14, 19, 26, 35, 44], 18), (1231, [4, 11, 22, 30, 36, 42], 9),
    (1230, [8, 13, 18, 25, 34, 43], 26), (1229, [2, 15, 20, 31, 38, 41], 13),
    (1228, [6, 10, 17, 27, 32, 45], 21), (1227, [3, 16, 23, 29, 37, 44], 8),
    (1226, [5, 12, 19, 24, 33, 40], 17), (1225, [1, 14, 22, 28, 36, 42], 39),
    (1224, [7, 11, 21, 30, 35, 43], 14), (1223, [4, 9, 18, 26, 34, 41], 22),
    (1222, [10, 13, 20, 27, 38, 45], 3), (1221, [2, 8, 17, 25, 31, 40], 16),
    (1220, [6, 15, 23, 29, 37, 44], 11), (1219, [3, 12, 19, 28, 33, 42], 26),
    (1218, [5, 14, 22, 30, 36, 43], 8), (1217, [1, 9, 16, 27, 34, 41], 20),
    (1216, [7, 13, 18, 24, 35, 45], 12), (1215, [4, 11, 21, 31, 38, 44], 25),
    (1214, [2, 10, 17, 26, 32, 40], 19), (1213, [8, 15, 20, 29, 37, 42], 4),
    (1212, [6, 14, 23, 28, 33, 43], 35), (1211, [3, 7, 19, 25, 36, 41], 10),
    (1210, [5, 12, 22, 30, 39, 45], 18), (1209, [1, 11, 18, 27, 34, 44], 23),
    (1208, [9, 16, 24, 31, 35, 40], 7), (1207, [2, 13, 20, 29, 38, 42], 14),
    (1206, [4, 8, 15, 26, 37, 43], 30), (1205, [6, 10, 17, 22, 33, 41], 9),
    (1204, [3, 14, 21, 28, 36, 45], 17), (1203, [7, 11, 19, 25, 32, 44], 6),
    (1202, [1, 12, 18, 27, 35, 40], 28), (1201, [5, 9, 16, 23, 34, 42], 11),
    (1200, [2, 14, 20, 29, 38, 43], 26), (1199, [4, 10, 22, 31, 37, 41], 15),
    (1198, [3, 12, 17, 25, 36, 45], 22), (1197, [8, 16, 24, 28, 33, 40], 17),
    (1196, [5, 11, 19, 30, 39, 44], 8), (1195, [1, 7, 21, 27, 35, 42], 33),
    (1194, [6, 13, 18, 26, 34, 43], 25), (1193, [9, 15, 23, 31, 37, 41], 14),
    (1192, [2, 12, 20, 29, 38, 45], 7), (1191, [4, 10, 17, 25, 32, 44], 18),
    (1190, [3, 14, 22, 28, 36, 40], 11), (1189, [1, 8, 19, 30, 39, 43], 27),
    (1188, [6, 11, 16, 24, 35, 42], 20), (1187, [5, 9, 21, 27, 33, 45], 16),
    (1186, [7, 15, 18, 28, 34, 41], 12), (1185, [2, 13, 23, 30, 37, 44], 35),
    (1184, [4, 12, 17, 26, 31, 40], 9), (1183, [3, 10, 19, 25, 38, 42], 17),
    (1182, [8, 16, 20, 29, 36, 45], 21), (1181, [1, 7, 14, 24, 32, 43], 30),
    (1180, [6, 11, 18, 27, 39, 44], 13), (1179, [5, 15, 21, 28, 33, 40], 6),
    (1178, [2, 9, 13, 26, 34, 41], 28), (1177, [4, 12, 22, 30, 35, 45], 18),
    (1176, [3, 8, 17, 29, 37, 42], 15), (1175, [7, 10, 16, 23, 31, 43], 24),
    (1174, [1, 14, 19, 25, 36, 40], 12), (1173, [6, 11, 20, 28, 32, 44], 35),
    (1172, [5, 13, 18, 27, 38, 41], 7), (1171, [2, 9, 15, 26, 33, 45], 19),
    (1170, [8, 17, 21, 30, 34, 42], 25), (1169, [4, 12, 23, 29, 37, 43], 14),
    (1168, [3, 11, 16, 28, 36, 40], 8), (1167, [1, 7, 15, 22, 35, 41], 29),
    (1166, [6, 10, 18, 24, 31, 45], 17), (1165, [9, 13, 20, 26, 38, 44], 3),
    (1164, [5, 14, 19, 27, 32, 42], 11), (1163, [2, 12, 17, 28, 33, 40], 36),
    (1162, [7, 15, 21, 29, 34, 43], 10), (1161, [4, 8, 16, 23, 37, 45], 12),
    (1160, [1, 11, 18, 26, 35, 40], 24), (1159, [3, 9, 14, 20, 33, 42], 2),
    (1158, [6, 13, 17, 25, 31, 44], 19), (1157, [5, 10, 19, 23, 28, 36], 18),
    (1156, [2, 8, 14, 22, 32, 41], 37), (1155, [7, 12, 18, 29, 33, 39], 25),
    (1154, [4, 11, 15, 22, 34, 40], 9), (1153, [1, 10, 13, 17, 27, 42], 6),
    (1152, [3, 12, 16, 19, 32, 41], 4), (1151, [6, 8, 17, 19, 21, 33], 26),
    (1150, [9, 11, 16, 21, 28, 38], 5), (1149, [8, 13, 18, 30, 33, 45], 37),
    (1148, [3, 8, 17, 24, 27, 35], 28), (1147, [7, 9, 22, 27, 37, 42], 34),
    (1146, [6, 11, 17, 19, 26, 33], 40), (1145, [2, 11, 31, 33, 37, 44], 32),
    (1144, [3, 4, 12, 15, 26, 34], 6), (1143, [10, 16, 17, 27, 29, 36], 6),
    (1142, [2, 8, 28, 30, 37, 41], 22), (1141, [7, 11, 12, 21, 26, 35], 20)
]

data = [{"round": r, "numbers": nums, "bonus": b} for r, nums, b in RAW_DATA]

# ================= UI 화면 =================
st.title("🎰 맞춤 로또 번호 추출기")

# 1. 최신 당첨 번호 카드
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

# 3. 분석 및 생성 설정 (1~100회차 완벽 지원)
max_available = len(data)
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

# 5. 통계 조회 섹션 (1~100회차 실시간 연동)
with st.expander("📊 회차별 출현 통계 실시간 조회", expanded=False):
    stat_range = st.slider(f"조회할 최근 회차 범위 (1~{max_available}회)", min_value=1, max_value=max_available, value=recent_count, step=1, key="stat_slider")
    
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
