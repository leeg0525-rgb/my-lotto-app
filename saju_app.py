import streamlit as st
import random
import json
import os
import urllib.request
from datetime import datetime, date
import io
import hashlib
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="사주 & 별자리 맞춤 로또 번호", page_icon="🔮", layout="centered")

# ================= 1. 최신 회차 번호 계산 =================
def get_current_max_drw():
    first_drw_date = datetime(2002, 12, 7, 20, 45)
    diff_days = (datetime.now() - first_drw_date).days
    return (diff_days // 7) + 1

target_round = get_current_max_drw()

# ================= 2. 공 그래픽 및 한글 폰트 영수증 생성 =================
def get_ball_rgb(num):
    if num <= 10:
        return (251, 196, 0)
    elif num <= 20:
        return (105, 200, 242)
    elif num <= 30:
        return (255, 114, 114)
    elif num <= 40:
        return (170, 170, 170)
    else:
        return (176, 216, 64)

def get_ball_color(num):
    rgb = get_ball_rgb(num)
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"

def render_balls(numbers):
    html = '<div style="display: flex; gap: 8px; justify-content: center; align-items: center; margin: 8px 0;">'
    for n in sorted(numbers):
        color = get_ball_color(n)
        html += f'<div style="background-color: {color}; color: white; font-weight: bold; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 15px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{n}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def get_korean_font_path():
    font_path = "NanumGothicBold.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp, open(font_path, "wb") as f:
                f.write(resp.read())
        except Exception:
            return None
    return font_path

def create_ticket_image(round_no, games_list, time_str, theme_title):
    width = 460
    header_h = 135
    row_h = 58
    footer_h = 55
    height = header_h + (len(games_list) * row_h) + footer_h
    
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    font_path = get_korean_font_path()
    if font_path and os.path.exists(font_path):
        try:
            font_bold = ImageFont.truetype(font_path, 21)
            font_main = ImageFont.truetype(font_path, 13)
            font_ball = ImageFont.truetype(font_path, 15)
        except Exception:
            font_bold = font_main = font_ball = ImageFont.load_default()
    else:
        font_bold = font_main = font_ball = ImageFont.load_default()

    draw.rectangle([(8, 8), (width - 9, height - 9)], outline=(210, 210, 210), width=2)
    draw.text((width // 2, 35), "AI LOTTO 6/45", fill=(40, 40, 40), font=font_bold, anchor="mm")
    draw.text((width // 2, 68), f"제 {round_no}회 [{theme_title}]", fill=(130, 60, 210), font=font_bold, anchor="mm")
    draw.text((width // 2, 98), f"발행일시: {time_str}", fill=(120, 120, 120), font=font_main, anchor="mm")
    draw.line([(25, 120), (width - 25, 120)], fill=(225, 225, 225), width=1)

    labels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    y_curr = header_h
    r = 18

    for idx, nums in enumerate(games_list):
        lbl = labels[idx] if idx < len(labels) else str(idx + 1)
        draw.text((38, y_curr + 22), f"{lbl} 운 세", fill=(90, 90, 90), font=font_main, anchor="lm")
        
        start_x = 118
        gap = 52
        for b_idx, n in enumerate(sorted(nums)):
            cx = start_x + (b_idx * gap)
            cy = y_curr + 22
            bg_color = get_ball_rgb(n)
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=bg_color)
            draw.text((cx, cy), str(n), fill=(255, 255, 255), font=font_ball, anchor="mm")
            
        y_curr += row_h

    draw.line([(25, y_curr + 6), (width - 25, y_curr + 6)], fill=(225, 225, 225), width=1)
    draw.text((width // 2, y_curr + 30), "1등 당첨의 행운이 함께하기를 기원합니다!", fill=(140, 140, 140), font=font_main, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ================= 3. 정밀 사주 오행 & 별자리 데이터 =================
DETAILED_ELEMENT_DATA = {
    "목(木) - 약동하는 봄의 생기와 번영": {
        "short": "목(木)",
        "nums": [3, 8, 13, 18, 23, 28, 33, 38, 43],
        "fortune": "겨울의 땅을 뚫고 솟아오르는 새싹처럼, 정체되었던 흐름이 풀리고 새로운 기운이 싹트는 날입니다.",
        "money": "갑작스러운 횡재수보다는 '예상치 못했던 작은 기회나 귀인의 조언'을 통해 재물의 문이 열리는 운세입니다.",
        "action": "평소 주저했던 선택을 과감하게 실행에 옮기기 좋은 날입니다. 동쪽 방향의 로또 판매점이 길합니다.",
        "lucky_items": "청색/초록색 계열, 식물이나 나무가 있는 장소"
    },
    "화(火) - 타오르는 불과 폭발적인 결실": {
        "short": "화(火)",
        "nums": [2, 7, 12, 17, 22, 27, 32, 37, 42],
        "fortune": "한낮의 뜨거운 태양처럼 모든 것을 환하게 비추고 에너지가 최고조로 상승하는 날입니다.",
        "money": "강한 추진력과 함께 직관이 예리해지는 날로, 한 번 꽂힌 번호나 느낌을 믿었을 때 강한 행운이 따릅니다.",
        "action": "고민을 오래 하기보다는 즉각적인 직관으로 선택하는 것이 유리합니다. 남쪽 방향의 판매점이 행운을 줍니다.",
        "lucky_items": "붉은색/오렌지색 계열, 번화하고 활기찬 장소"
    },
    "토(土) - 기름진 대지와 든든한 축적": {
        "short": "토(土)",
        "nums": [5, 10, 15, 20, 25, 30, 35, 40, 45],
        "fortune": "만물을 품고 양분을 공급하는 비옥한 대지처럼 마음이 안정되고 실리가 두터워지는 운세입니다.",
        "money": "재물이 새어나가지 않고 차곡차곡 모이는 기운이 강하며, 큰 욕심을 부리지 않을 때 뜻밖의 복이 깃듭니다.",
        "action": "기존에 눈여겨보았던 단골 판매점이나 평소 자주 지나치던 익숙한 길목에서 구매하는 것이 길합니다.",
        "lucky_items": "황토색/베이지/노란색 계열, 안정감을 주는 카페나 정원"
    },
    "금(金) - 단단한 금석과 날카로운 직관": {
        "short": "금(金)",
        "nums": [4, 9, 14, 19, 24, 29, 34, 39, 44],
        "fortune": "가을철 낟알을 수확하고 보석을 제련하듯, 명확한 기준과 날카로운 분별력이 돋보이는 날입니다.",
        "money": "우유부단함을 버리고 칼같이 결단할 때 재물복이 크게 트입니다. 복잡한 생각보다는 첫 느낌의 번호가 정답일 수 있습니다.",
        "action": "주변의 말에 흔들리지 말고 본인만의 소신대로 밀고 나가세요. 서쪽 방향의 판매점이 길합니다.",
        "lucky_items": "화이트/실버/메탈 계열, 깔끔하고 정돈된 장소"
    },
    "수(水) - 깊은 바다와 끊이지 않는 재물 샘": {
        "short": "수(水)",
        "nums": [1, 6, 11, 16, 21, 26, 31, 36, 41],
        "fortune": "쉬지 않고 바다로 흘러드는 강물처럼 유연함과 통찰력이 극대화되며 재물의 순환이 매우 원활한 날입니다.",
        "money": "사주에서 수(水)는 본래 재물과 직결되는 기운입니다. 막혀 있던 금전 운의 물꼬가 트이는 길조가 보입니다.",
        "action": "여유로운 마음으로 물 한 잔을 마신 뒤 편안한 마음으로 번호를 선택하세요. 북쪽 방향이나 수변 근처가 길합니다.",
        "lucky_items": "블랙/네이비 계열, 분수대나 호수, 물이 가까운 곳"
    }
}

ZODIAC_DATA = {
    "양자리 (3/21~4/19)": {"planet": "화성", "nums": [9, 18, 27, 36, 45], "desc": "불타는 용기와 승부욕이 빛나는 날입니다. 주저 없는 결단이 큰 행운을 부릅니다."},
    "황소자리 (4/20~5/20)": {"planet": "금성", "nums": [6, 15, 24, 33, 42], "desc": "실리적이고 단단한 감각이 돋보입니다. 꾸준함 속에서 뜻밖의 결실을 맺을 기운입니다."},
    "쌍둥이자리 (5/21~6/21)": {"planet": "수성", "nums": [5, 14, 23, 32, 41], "desc": "영감이 번뜩이고 두뇌 회전이 빠른 날입니다. 직감적으로 떠오르는 번호를 놓치지 마세요."},
    "게자리 (6/22~7/22)": {"planet": "달", "nums": [2, 7, 11, 16, 20, 29], "desc": "감수성과 예지력이 풍부해집니다. 마음이 편안하게 끌리는 번호가 길한 운을 가져옵니다."},
    "사자자리 (7/23~8/22)": {"planet": "태양", "nums": [1, 4, 10, 19, 28, 37], "desc": "강한 주인공의 에너지가 감돕니다. 자신감을 갖고 당당하게 선택할 때 기운이 트입니다."},
    "처녀자리 (8/23~9/22)": {"planet": "수성", "nums": [5, 12, 14, 23, 32, 41], "desc": "꼼꼼하고 치밀한 통찰력이 길합니다. 균형 잡힌 배열 속에서 행운이 싹틉니다."},
    "천칭자리 (9/23~10/22)": {"planet": "금성", "nums": [6, 15, 24, 33, 42], "desc": "조화와 심미안이 뛰어난 날입니다. 고른 배분과 안정된 마음가짐이 길한 결과를 만듭니다."},
    "전갈자리 (10/23~11/21)": {"planet": "명왕성", "nums": [9, 18, 27, 36, 45], "desc": "깊은 통찰과 한 방의 응축된 힘이 있습니다. 은밀하게 준비된 큰 행운을 기대해 볼 만합니다."},
    "사수자리 (11/22~12/21)": {"planet": "목성", "nums": [3, 12, 21, 30, 39], "desc": "행운의 행성 목성의 비호를 받습니다. 낙천적이고 긍정적인 에너지가 대길을 부릅니다."},
    "염소자리 (12/22~1/19)": {"planet": "토성", "nums": [4, 8, 13, 22, 31, 40], "desc": "인내와 성실함이 보답받는 운세입니다. 흔들림 없는 집중력이 행운의 문을 엽니다."},
    "물병자리 (1/20~2/18)": {"planet": "천왕성", "nums": [4, 7, 11, 22, 29, 38], "desc": "고정관념을 깨는 독창적인 발상이 빛납니다. 남들이 보지 못한 곳에 기회가 숨어 있습니다."},
    "물고기자리 (2/19~3/20)": {"planet": "해왕성", "nums": [3, 9, 12, 21, 30, 39], "desc": "풍부한 상상력과 직관이 흐릅니다. 꿈자리나 무의식 속 감각을 믿어보세요."}
}

def get_zodiac_sign(month, day):
    dates = [(1, 20), (2, 19), (3, 21), (4, 20), (5, 21), (6, 22), 
             (7, 23), (8, 23), (9, 23), (10, 23), (11, 22), (12, 22)]
    signs = list(ZODIAC_DATA.keys())
    for idx, (m, d) in enumerate(dates):
        if (month == m and day >= d) or (month == (m % 12) + 1 and day < dates[m % 12][1]):
            return signs[idx]
    return signs[-1]

# ================= 4. UI 입력 폼 =================
st.title("🔮 사주 & 별자리 맞춤 번호 추출기")
st.markdown("생년월일과 **오늘의 일진(日辰)**을 결합하여, 오늘 나에게 가장 강하게 들어오는 재물 기운과 맞춤 번호를 도출합니다.")

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        birth_date = st.date_input(
            "📅 생년월일",
            value=date(1985, 1, 1),
            min_value=date(1930, 1, 1),
            max_value=date.today()
        )
    with col2:
        hour_options = [
            "모름 / 무관",
            "자시 (23:30 ~ 01:29)", "축시 (01:30 ~ 03:29)", "인시 (03:30 ~ 05:29)",
            "묘시 (05:30 ~ 07:29)", "진시 (07:30 ~ 09:29)", "사시 (09:30 ~ 11:29)",
            "오시 (11:30 ~ 13:29)", "미시 (13:30 ~ 15:29)", "신시 (15:30 ~ 17:29)",
            "유시 (17:30 ~ 19:29)", "술시 (19:30 ~ 21:29)", "해시 (21:30 ~ 23:29)"
        ]
        birth_hour = st.selectbox("⏰ 태어난 시간(시진)", hour_options, index=0)

    mode = st.radio(
        "추천 방식을 선택하세요",
        ["🌿 오늘의 사주 오행 일진 번호 (매일 변경)", "⭐ 나의 수호 별자리 행운 번호"],
        horizontal=True
    )
    
    game_count = st.slider("생성할 게임 수", min_value=1, max_value=10, value=5)

# ================= 5. 번호 추첨 실행 =================
if st.button("✨ 오늘의 맞춤 행운 번호 뽑기", use_container_width=True, type="primary"):
    today_str = datetime.now().strftime("%Y-%m-%d")
    games = []
    
    if "사주 오행" in mode:
        seed_key = f"{birth_date}_{birth_hour}_{today_str}"
        val = int(hashlib.md5(seed_key.encode()).hexdigest(), 16)
        
        elem_keys = list(DETAILED_ELEMENT_DATA.keys())
        chosen_elem = elem_keys[val % len(elem_keys)]
        info = DETAILED_ELEMENT_DATA[chosen_elem]
        lucky_nums = info["nums"]
        theme_title = f"사주_{info['short']}"
        
        # 상세 풀이 텍스트 구성
        st.session_state.result_story = f"""
### 📜 오늘의 일진(日辰) & 사주 정밀 분석

* **오늘의 중심 기운:** **{chosen_elem}**
* **총평:** {info['fortune']}
* **재물운의 흐름:** {info['money']}
* **오늘의 추천 행동:** {info['action']}
* **행운의 요소:** {info['lucky_items']}

---
💡 **오늘의 오행 수비학 핵심 번호:** `{', '.join(map(str, lucky_nums))}`
> 위 번호 풀에 높은 가중치를 배정하여, 오늘 회원님에게 가장 길한 에너지의 6개 조합을 완성했습니다.
        """
        
        for g_idx in range(1, game_count + 1):
            rnd = random.Random(f"{seed_key}_game_{g_idx}")
            weights = [4 if n in lucky_nums else 1 for n in range(1, 46)]
            pool = list(range(1, 46))
            
            picked = set()
            while len(picked) < 6 and pool:
                c = rnd.choices(pool, weights=weights, k=1)[0]
                picked.add(c)
                idx = pool.index(c)
                pool.pop(idx)
                weights.pop(idx)
            games.append(sorted(list(picked)))
            
    else:
        zodiac = get_zodiac_sign(birth_date.month, birth_date.day)
        z_info = ZODIAC_DATA[zodiac]
        lucky_nums = z_info["nums"]
        theme_title = f"별자리_{zodiac.split()[0]}"
        
        st.session_state.result_story = f"""
### ⭐ 나의 수호성 & 별자리 정밀 운세

* **당신의 별자리:** **{zodiac}**
* **지배 수호성:** **{z_info['planet']}**
* **운세 조언:** {z_info['desc']}

---
💡 **수호성의 고유 행운 번호:** `{', '.join(map(str, lucky_nums))}`
> 수호성이 지닌 고유 주파수의 숫자를 기점으로 6개 번호를 조화롭게 구성했습니다.
        """
        
        for g_idx in range(1, game_count + 1):
            rnd = random.Random(f"zodiac_{zodiac}_{today_str}_{g_idx}")
            weights = [5 if n in lucky_nums else 1 for n in range(1, 46)]
            pool = list(range(1, 46))
            
            picked = set()
            while len(picked) < 6 and pool:
                c = rnd.choices(pool, weights=weights, k=1)[0]
                picked.add(c)
                idx = pool.index(c)
                pool.pop(idx)
                weights.pop(idx)
            games.append(sorted(list(picked)))
            
    st.session_state.current_games = games
    st.session_state.current_theme = theme_title

# ================= 6. 결과 화면 & 직관적인 사진 저장 버튼 =================
if "current_games" in st.session_state and st.session_state.current_games:
    st.markdown("---")
    st.subheader(f"🎯 제 {target_round}회 행운 추천 조합")
    
    if "result_story" in st.session_state:
        st.markdown(st.session_state.result_story)
        
    for idx, nums in enumerate(st.session_state.current_games, start=1):
        with st.container(border=True):
            st.markdown(f"**{idx}게임**")
            render_balls(nums)
            
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    img_bytes = create_ticket_image(
        target_round, 
        st.session_state.current_games, 
        now_str, 
        st.session_state.current_theme
    )
    
    # 문구 개선: '영수증 생성' -> '오늘의 추천 번호 사진으로 저장'
    st.markdown("### 💾 번호 보관")
    st.download_button(
        label="📥 오늘의 행운 조합 사진으로 저장하기 (PNG)",
        data=img_bytes,
        file_name=f"로또_{target_round}회_행운번호_{st.session_state.current_theme}.png",
        mime="image/png",
        type="primary",
        use_container_width=True
    )
    
    with st.expander("👁️ 저장될 번호 사진 미리보기"):
        st.image(img_bytes, caption=f"제 {target_round}회 추천 번호표", use_container_width=True)
