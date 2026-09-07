from collections import Counter
import random
import re
import cv2
import numpy as np
from PIL import Image
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

def render_balls(numbers):
    html = '<div style="display: flex; gap: 8px; justify-content: center; margin: 10px 0;">'
    for n in sorted(numbers):
        color = get_ball_color(n)
        html += f'<div style="background-color: {color}; color: white; font-weight: bold; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{n}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# QR 데이터 및 임의의 텍스트에서 1~45 로또 번호 추출
def extract_numbers_from_qr_or_text(text):
    if not text:
        return []
    
    extracted = set()
    
    # 1. 동행복권 공식 QR 규격 포맷 (v=회차q게임1q게임2...)
    if "v=" in text or "method=winQr" in text or "q" in text:
        match = re.search(r'v=([0-9a-zA-Z]+)', text)
        raw_val = match.group(1) if match else text.strip()
        parts = raw_val.split('q')[1:]  # 회차 제외
        for p in parts:
            if len(p) >= 12:
                game_str = p[:12]
                for i in range(0, 12, 2):
                    try:
                        n = int(game_str[i:i+2])
                        if 1 <= n <= 45:
                            extracted.add(n)
                    except ValueError:
                        pass
        if extracted:
            return sorted(list(extracted))
            
    # 2. 사용자가 그냥 띄어쓰기나 쉼표로 숫자를 막 적은 경우
    found = re.findall(r'\b\d{1,2}\b', text)
    for f in found:
        n = int(f)
        if 1 <= n <= 45:
            extracted.add(n)
            
    return sorted(list(extracted))

# 카메라로 찍은 이미지에서 QR 읽기 (OpenCV 활용)
def read_qr_from_image(image_file):
    try:
        image = Image.open(image_file)
        img_np = np.array(image)
        # BGR 변환
        if len(img_np.shape) == 3 and img_np.shape[2] == 3:
            img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img_np)
        return data if data else None
    except Exception:
        return None

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

# --- UI 메인 ---
st.title("🎰 맞춤 로또 번호 추출기")
st.caption("방금 산 영수증 QR을 찍거나 번호를 입력하면, 그 번호들을 싹 빼고 새로 뽑아줍니다.")

data = load_lotto_data()

# 번호 간편 제외 섹션
with st.expander("📷 구매한 로또 번호 간편 제외 (QR 촬영 / 직접 입력)", expanded=True):
    tab1, tab2 = st.tabs(["📸 카메라로 QR 찍기", "✍️ 숫자 편하게 적기"])
    
    auto_excluded = []
    
    with tab1:
        st.caption("로또 용지 상단의 네모난 QR 코드를 비춰서 사진을 찍으세요.")
        camera_img = st.camera_input("로또 QR 코드 촬영", label_visibility="collapsed")
        if camera_img:
            qr_data = read_qr_from_image(camera_img)
            if qr_data:
                auto_excluded = extract_numbers_from_qr_or_text(qr_data)
                if auto_excluded:
                    st.success(f"🎉 QR 인식 성공! {len(auto_excluded)}개 번호가 자동 제외됩니다.")
                else:
                    st.warning("QR은 인식되었으나 번호 데이터를 찾지 못했습니다.")
            else:
                st.error("QR 코드를 찾지 못했습니다. 조금 더 가깝고 밝게 다시 찍어보세요.")
                
    with tab2:
        st.caption("복잡한 기호 없이 '1 5 13 22 35 44' 처럼 숫자만 띄어서 적으면 됩니다.")
        raw_text = st.text_area("제외할 번호 입력", placeholder="예: 3 14 20 28 29 34 7 11 19...", height=80)
        if raw_text:
            text_excluded = extract_numbers_from_qr_or_text(raw_text)
            if text_excluded:
                auto_excluded = sorted(list(set(auto_excluded + text_excluded)))

    if auto_excluded:
        st.info(f"🚫 현재 제외 적용된 번호: {auto_excluded}")

# 옵션 설정
col1, col2 = st.columns(2)
with col1:
    recent_count = st.slider("분석할 최근 회차", min_value=3, max_value=50, value=3, step=1)
with col2:
    game_count = st.slider("생성할 게임 수", min_value=1, max_value=10, value=5)

# 알기 쉬운 전략 선택
strategy = st.radio(
    "어떤 방식으로 번호를 뽑을까요?",
    [
        "🔥 요즘 잘 나오는 번호만 뽑기",
        "⚡ 반반 섞기 (자주 나온 수 3개 + 안 나온 수 3개)",
        "❄️ 최근 안 나온 번호만 뽑기 (역발상)",
        "🎲 확률 비례 골고루 뽑기"
    ]
)

# 데이터 집계 및 번호 추출 로직
sorted_items = sorted(data, key=lambda x: x["round"], reverse=True)[:recent_count]
all_numbers = []
for item in sorted_items:
    nums = item.get("numbers") or [item[f"drwtNo{i}"] for i in range(1, 7)]
    all_numbers.extend(nums)

counts = Counter(all_numbers)
available_pool = [n for n in range(1, 46) if n not in auto_excluded]
ranked_available = sorted(available_pool, key=lambda x: counts.get(x, 0), reverse=True)

appeared_nums = [n for n in ranked_available if counts.get(n, 0) > 0]
not_appeared_nums = [n for n in ranked_available if counts.get(n, 0) == 0]

hot_pool = appeared_nums if len(appeared_nums) >= 6 else ranked_available[:max(6, len(ranked_available))]
cold_pool = not_appeared_nums if len(not_appeared_nums) >= 6 else ranked_available[-max(6, len(ranked_available)):]

if st.button("🎲 추천 번호 뽑기", use_container_width=True, type="primary"):
    if len(available_pool) < 6:
        st.error("제외된 번호가 너무 많아 6개를 뽑을 수 없습니다.")
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
