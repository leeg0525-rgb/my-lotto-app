from collections import Counter
import random
import re
from google import genai
from PIL import Image
import requests
import streamlit as st

st.set_page_config(page_title="AI 로또 번호 분석기", page_icon="🎰", layout="centered")

# Gemini API 키 (Secrets에서 읽거나 직접 입력)
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

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

def render_balls(numbers):
    html = '<div style="display: flex; gap: 8px; justify-content: center; margin: 10px 0;">'
    for n in sorted(numbers):
        color = get_ball_color(n)
        html += f'<div style="background-color: {color}; color: white; font-weight: bold; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{n}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def read_lotto_numbers_with_ai(image_file, api_key):
    try:
        client = genai.Client(api_key=api_key)
        img = Image.open(image_file)
        
        prompt = """
        이 사진은 한국 로또 6/45 복권 용지입니다.
        용지에 인쇄된 게임별(A, B, C, D, E 등) 6자리 로또 번호들을 모두 읽어주세요.
        결과는 오직 1부터 45 사이의 정수들이 들어있는 단일 JSON 숫자 배열 형식으로만 응답하세요.
        예: [3, 11, 14, 18, 22, 35]
        추가 설명 없이 오직 JSON 배열만 출력하세요.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img]
        )
        
        cleaned = re.sub(r'[^0-9,]', '', response.text)
        nums = [int(n) for n in cleaned.split(',') if n.isdigit() and 1 <= int(n) <= 45]
        return sorted(list(set(nums)))
    except Exception as e:
        st.error(f"판독 중 오류 발생: {e}")
        return []

@st.cache_data(ttl=3600)
def load_lotto_data():
    url = "https://raw.githubusercontent.com/jonghwan-park/lotto-history/main/data.json"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return [{"round": 1135, "numbers": [1, 6, 13, 19, 21, 33]}]

# UI 메인
st.title("🎰 맞춤 로또 번호 추출기")
st.caption("로또 사진을 올리면 AI가 이미 산 번호를 자동으로 읽어 제외하고 새로 뽑아줍니다.")

data = load_lotto_data()

if "excluded_nums" not in st.session_state:
    st.session_state.excluded_nums = []

# 사진 첨부 섹션
with st.expander("📷 로또 용지 사진으로 번호 제외하기", expanded=True):
    # 키가 코드에 없으면 화면에서 입력받을 수 있도록 지원
    user_key = GEMINI_API_KEY
    if not user_key:
        user_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    
    uploaded_file = st.file_uploader("로또 용지 사진 첨부 (앨범에서 선택)", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        st.image(uploaded_file, caption="선택된 용지 사진", width=220)
        if st.button("🔍 AI로 사진 속 번호 읽기", use_container_width=True):
            if not user_key:
                st.warning("Gemini API 키를 먼저 입력해 주세요.")
            else:
                with st.spinner("AI가 영수증 속 번호를 읽는 중입니다..."):
                    found = read_lotto_numbers_with_ai(uploaded_file, user_key)
                    if found:
                        st.session_state.excluded_nums = found
                        st.success(f"🎉 총 {len(found)}개 번호 자동 판독 완료!")
                    else:
                        st.warning("번호를 찾지 못했습니다. 사진을 더 밝게 찍어 올려주세요.")

# 수동 및 자동 제외 목록
auto_excluded = st.session_state.excluded_nums
manual_excluded = st.multiselect(
    "🚫 제외할 번호 목록 (AI 판독 결과 및 수동 편집)",
    options=list(range(1, 46)),
    default=auto_excluded
)
total_excluded = set(manual_excluded)

# 분석 설정
col1, col2 = st.columns(2)
with col1:
    recent_count = st.slider("분석할 최근 회차", min_value=3, max_value=50, value=3, step=1)
with col2:
    game_count = st.slider("생성할 게임 수", min_value=1, max_value=10, value=5)

# 전략 선택
strategy = st.radio(
    "어떤 방식으로 번호를 뽑을까요?",
    [
        "🔥 요즘 잘 나오는 번호만 뽑기",
        "⚡ 반반 섞기 (자주 나온 수 3개 + 안 나온 수 3개)",
        "❄️ 최근 안 나온 번호만 뽑기 (역발상)",
        "🎲 확률 비례 골고루 뽑기"
    ]
)

# 당첨 통계 집계
sorted_items = sorted(data, key=lambda x: x["round"], reverse=True)[:recent_count]
all_numbers = []
for item in sorted_items:
    nums = item.get("numbers") or [item[f"drwtNo{i}"] for i in range(1, 7)]
    all_numbers.extend(nums)

counts = Counter(all_numbers)
available_pool = [n for n in range(1, 46) if n not in total_excluded]
ranked_available = sorted(available_pool, key=lambda x: counts.get(x, 0), reverse=True)

appeared_nums = [n for n in ranked_available if counts.get(n, 0) > 0]
not_appeared_nums = [n for n in ranked_available if counts.get(n, 0) == 0]

hot_pool = appeared_nums if len(appeared_nums) >= 6 else ranked_available[:max(6, len(ranked_available))]
cold_pool = not_appeared_nums if len(not_appeared_nums) >= 6 else ranked_available[-max(6, len(ranked_available)):]

# 추천 번호 생성 버튼
if st.button("🎲 추천 번호 뽑기", use_container_width=True, type="primary"):
    if len(available_pool) < 6:
        st.error("제외된 번호가 너무 많아 6개를 뽑을 수 없습니다. 제외수를 줄여주세요.")
    else:
        st.subheader("🎯 생성된 추천 번호")
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
