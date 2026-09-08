import streamlit as st
import random
from collections import Counter
import json
import os
import urllib.request
from datetime import datetime, date
import io
import hashlib
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="맞춤 로또 & 사주 번호 추출기", page_icon="🎰", layout="centered")

# ================= 영구 저장소 (JSON 관리) =================
DATA_FILE = "my_lotto_history.json"

def load_saved_history():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history_to_disk(history_list):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"저장 오류: {e}")

if "my_saved_groups" not in st.session_state:
    st.session_state.my_saved_groups = load_saved_history()
if "last_generated_games" not in st.session_state:
    st.session_state.last_generated_games = []
if "generated_source_title" not in st.session_state:
    st.session_state.generated_source_title = "추천 번호 세트"
if "fortune_story" not in st.session_state:
    st.session_state.fortune_story = ""

# ================= 색상 및 그래픽 (공 렌더링) =================
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

# 상단 최근 당첨 번호용 렌더링 함수
def render_balls(numbers, bonus=None):
    html = '<div style="display: flex; gap: 8px; justify-content: center; align-items: center; margin: 4px 0;">'
    for n in sorted(numbers):
        color = get_ball_color(n)
        html += f'<div style="background-color: {color}; color: white; font-weight: bold; border-radius: 50%; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; font-size: 15px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{n}</div>'
    if bonus:
        html += '<div style="font-size: 18px; font-weight: bold; color: #888; margin: 0 4px;">+</div>'
        b_color = get_ball_color(bonus)
        html += f'<div style="background-color: {b_color}; color: white; font-weight: bold; border-radius: 50%; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; font-size: 15px; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{bonus}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# 카드 박스 일체형 한 줄 렌더링 (라벨 + 공 수평/수직 완벽 정렬 & 상하 여백 압축)
def render_game_row(label_text, numbers):
    balls_html = ""
    for n in sorted(numbers):
        color = get_ball_color(n)
        balls_html += f'<div style="background-color: {color}; color: white; font-weight: bold; border-radius: 50%; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; font-size: 14px; box-shadow: 1px 1px 2px rgba(0,0,0,0.25); flex-shrink: 0;">{n}</div>'
    
    card_html = f'''
    <div style="
        display: flex;
        align-items: center;
        background-color: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 10px;
        padding: 8px 16px;
        margin-bottom: 8px;
        box-sizing: border-box;
    ">
        <div style="
            width: 48px;
            font-size: 15px;
            font-weight: 700;
            color: #d1d5db;
            text-align: center;
            flex-shrink: 0;
            letter-spacing: -0.5px;
        ">{label_text}</div>
        <div style="
            display: flex;
            gap: 8px;
            align-items: center;
            margin-left: 12px;
            flex-grow: 1;
        ">
            {balls_html}
        </div>
    </div>
    '''
    st.markdown(card_html, unsafe_allow_html=True)

# 한글 폰트 자동 다운로드
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

# 추천 번호표 사진 이미지 생성 함수
def create_ticket_image(round_no, games_list, time_str):
    scale = 2
    base_w = 400
    base_header_h = 110
    base_row_h = 48
    base_footer_h = 45
    base_h = base_header_h + (len(games_list) * base_row_h) + base_footer_h

    w = base_w * scale
    h = base_h * scale
    header_h = base_header_h * scale
    row_h = base_row_h * scale

    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_path = get_korean_font_path()
    if font_path and os.path.exists(font_path):
        try:
            font_title = ImageFont.truetype(font_path, 20 * scale)
            font_round = ImageFont.truetype(font_path, 19 * scale)
            font_main = ImageFont.truetype(font_path, 11 * scale)
            font_ball = ImageFont.truetype(font_path, 13 * scale)
        except Exception:
            font_title = font_round = font_main = font_ball = ImageFont.load_default()
    else:
        font_title = font_round = font_main = font_ball = ImageFont.load_default()

    draw.rectangle([(6 * scale, 6 * scale), (w - 7 * scale, h - 7 * scale)], outline=(220, 220, 220), width=2 * scale)
    draw.text((w // 2, 28 * scale), "LOTTO 6/45", fill=(45, 45, 45), font=font_title, anchor="mm")
    draw.text((w // 2, 56 * scale), f"제 {round_no}회 추천 조합", fill=(30, 90, 200), font=font_round, anchor="mm")
    draw.text((w // 2, 82 * scale), f"발행일시: {time_str}", fill=(130, 130, 130), font=font_main, anchor="mm")
    draw.line([(20 * scale, 100 * scale), (w - 20 * scale, 100 * scale)], fill=(230, 230, 230), width=scale)

    labels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    y_curr = header_h
    r = 15 * scale

    for idx, nums in enumerate(games_list):
        lbl = labels[idx] if idx < len(labels) else str(idx + 1)
        draw.text((32 * scale, y_curr + 18 * scale), f"{lbl} 자 동", fill=(90, 90, 90), font=font_main, anchor="lm")

        start_x = 100 * scale
        gap = 45 * scale
        for b_idx, n in enumerate(sorted(nums)):
            cx = start_x + (b_idx * gap)
            cy = y_curr + 18 * scale
            bg_color = get_ball_rgb(n)
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=bg_color)
            draw.text((cx, cy), str(n), fill=(255, 255, 255), font=font_ball, anchor="mm")

        y_curr += row_h

    draw.line([(20 * scale, y_curr + 4 * scale), (w - 20 * scale, y_curr + 4 * scale)], fill=(230, 230, 230), width=scale)
    draw.text((w // 2, y_curr + 24 * scale), "1등 당첨을 진심으로 기원합니다!", fill=(140, 140, 140), font=font_main, anchor="mm")

    final_img = img.resize((base_w, base_h), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    final_img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()

# ================= 공식 100회차 베이스 데이터 =================
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

data = get_updated_lotto_data()
latest_round = data[0]["round"]
target_next_round = latest_round + 1

# ================= 정밀 사주 오행 & 별자리 데이터 풀 =================
DETAILED_ELEMENT_DATA = {
    "목(木) - 약동하는 봄의 생기와 번영": {
        "short": "목(木)",
        "nums": [3, 8, 13, 18, 23, 28, 33, 38, 43],
        "fortune": "겨울 땅을 뚫고 솟아오르는 새싹처럼, 정체되었던 운이 풀리고 새로운 행운의 싹이 트는 날입니다.",
        "money": "갑작스러운 횡재수보다는 '예상치 못했던 작은 기회나 번뜩이는 영감'을 통해 재물의 문이 열립니다.",
        "action": "평소 망설였던 선택을 과감하게 실행에 옮기기 좋은 날입니다. 동쪽 방향 판매점이 길합니다.",
        "lucky_items": "청색/초록색 계열, 식물이나 나무가 있는 장소"
    },
    "화(火) - 타오르는 불과 폭발적인 결실": {
        "short": "화(火)",
        "nums": [2, 7, 12, 17, 22, 27, 32, 37, 42],
        "fortune": "한낮의 태양처럼 기운이 환하게 비추며 에너지가 최고조로 상승하는 역동적인 날입니다.",
        "money": "강한 추진력과 함께 직관이 매우 예리해지는 날로, 첫 느낌으로 고른 번호에 큰 행운이 따릅니다.",
        "action": "복잡하게 재기보다는 직관에 맡기는 것이 유리합니다. 남쪽 방향의 번화한 판매점이 좋습니다.",
        "lucky_items": "붉은색/오렌지색 계열, 활기차고 밝은 장소"
    },
    "토(土) - 기름진 대지와 든든한 축적": {
        "short": "토(土)",
        "nums": [5, 10, 15, 20, 25, 30, 35, 40, 45],
        "fortune": "비옥한 대지처럼 중심을 든든히 지키며 실속과 재물이 차곡차곡 쌓여가는 안정된 운세입니다.",
        "money": "재물이 흩어지지 않고 모이는 기운이 강하며, 큰 욕심을 부리지 않을 때 뜻밖의 큰 복이 깃듭니다.",
        "action": "평소 자주 가던 단골 판매점이나 익숙한 길목에서 구매하는 것이 행운을 높여줍니다.",
        "lucky_items": "황토색/베이지/노란색 계열, 편안한 카페나 정원"
    },
    "금(金) - 단단한 보석과 날카로운 결단": {
        "short": "금(金)",
        "nums": [4, 9, 14, 19, 24, 29, 34, 39, 44],
        "fortune": "가을철 풍성한 낟알을 수확하고 보석을 다듬듯, 명확한 기준과 분별력이 돋보이는 날입니다.",
        "money": "우유부단함을 버리고 칼같이 결단할 때 재물복이 크게 트입니다. 나의 소신을 믿는 것이 핵심입니다.",
        "action": "주변 의견에 흔들리지 말고 본인만의 주관대로 밀고 나가세요. 서쪽 방향 판매점이 길합니다.",
        "lucky_items": "화이트/실버/메탈 계열, 깔끔하고 정돈된 장소"
    },
    "수(水) - 깊은 바다와 끊이지 않는 재물 샘": {
        "short": "수(水)",
        "nums": [1, 6, 11, 16, 21, 26, 31, 36, 41],
        "fortune": "쉬지 않고 바다로 흐르는 강물처럼 유연함과 통찰력이 극대화되며 재물의 순환이 원활한 날입니다.",
        "money": "사주에서 수(水)는 본래 재물과 직결되는 기운입니다. 막혀 있던 금전 운의 물꼬가 트이는 길조가 보입니다.",
        "action": "시원한 물 한 잔을 마신 뒤 차분한 마음으로 번호를 선택하세요. 북쪽 방향 판매점이 길합니다.",
        "lucky_items": "블랙/네이비 계열, 분수대나 강, 물이 가까운 곳"
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

# ================= 메인 헤더 & 공통 영역 =================
st.title("🎰 맞춤 로또 번호 추출기")

# 1. 최근 실제 당첨 번호 박스
latest = data[0]
with st.container(border=True):
    st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 16px; margin-bottom: 6px;'>🏆 가장 최근 (제 {latest['round']}회) 실제 공식 당첨 번호</div>", unsafe_allow_html=True)
    render_balls(latest["numbers"], latest.get("bonus"))

# 2. 나의 저장 번호 보관함
total_saved_games = sum(len(grp["games"]) for grp in st.session_state.my_saved_groups)
with st.expander(f"📁 나의 저장 번호 보관함 ({len(st.session_state.my_saved_groups)}개 세트 / 총 {total_saved_games}게임)", expanded=len(st.session_state.my_saved_groups) > 0):
    if not st.session_state.my_saved_groups:
        st.info("아직 보관함에 저장된 번호가 없습니다.")
    else:
        for grp_idx, grp in enumerate(st.session_state.my_saved_groups):
            with st.container(border=True):
                c_title, c_del = st.columns([4, 1])
                with c_title:
                    st.markdown(f"**[{grp['round']}회차 도전]** {grp['title']} `({grp['time']})`")
                with c_del:
                    if st.button("🗑️ 삭제", key=f"del_grp_{grp_idx}"):
                        st.session_state.my_saved_groups.pop(grp_idx)
                        save_history_to_disk(st.session_state.my_saved_groups)
                        st.rerun()
                
                # 보관함 번호 표시 (일체형 row 렌더링)
                for g_idx, g_nums in enumerate(grp["games"], start=1):
                    render_game_row(f"{g_idx}번", g_nums)
                
                saved_img_bytes = create_ticket_image(grp["round"], grp["games"], grp["time"])
                st.download_button(
                    label="🖼️ 이 조합 사진 파일로 보관",
                    data=saved_img_bytes,
                    file_name=f"로또_{grp['round']}회_{grp['title']}.png",
                    mime="image/png",
                    key=f"dl_saved_{grp_idx}",
                    use_container_width=True
                )
        
        if st.button("🗑️ 보관함 전체 비우기", type="secondary", key="btn_clear_all_storage"):
            st.session_state.my_saved_groups = []
            save_history_to_disk([])
            st.rerun()

# ================= 탭 분리: [기존 통계 분석] vs [신규 사주/별자리 운세] =================
tab_stats, tab_fortune = st.tabs(["📊 공식 통계 기반 분석", "🔮 사주 & 별자리 맞춤 운세"])

# ----------------------------------------------------
# TAB 1: 기존 통계 기반 분석
# ----------------------------------------------------
with tab_stats:
    excluded_numbers = st.multiselect("🚫 조합에서 제외할 번호 선택", options=list(range(1, 46)), placeholder="제외수를 선택하세요", key="stat_exclude")

    max_available = len(data)
    col1, col2 = st.columns(2)
    with col1:
        recent_count = st.slider("추출에 반영할 최근 회차 수", min_value=1, max_value=max_available, value=min(10, max_available), step=1, key="stat_recent")
    with col2:
        game_count = st.slider("생성할 게임 수", min_value=1, max_value=10, value=5, key="stat_games")

    strategy = st.radio("어떤 방식으로 번호를 뽑을까요?", [
        "🔥 요즘 잘 나오는 번호만 뽑기",
        "⚡ 반반 섞기 (자주 나온 수 3개 + 안 나온 수 3개)",
        "❄️ 최근 안 나온 번호만 뽑기 (역발상)",
        "🎲 확률 비례 골고루 뽑기"
    ], key="stat_strategy")

    extract_subset = data[:recent_count]
    all_numbers = [n for item in extract_subset for n in item["numbers"]]
    counts = Counter(all_numbers)
    available_pool = [n for n in range(1, 46) if n not in excluded_numbers]
    ranked_available = sorted(available_pool, key=lambda x: counts.get(x, 0), reverse=True)
    appeared_nums = [n for n in ranked_available if counts.get(n, 0) > 0]
    not_appeared_nums = [n for n in ranked_available if counts.get(n, 0) == 0]

    hot_pool = appeared_nums if len(appeared_nums) >= 6 else ranked_available[:max(6, len(ranked_available))]
    cold_pool = not_appeared_nums if len(not_appeared_nums) >= 6 else ranked_available[-max(6, len(ranked_available)):]

    if st.button("🎲 통계 기반 추천 번호 뽑기", use_container_width=True, type="primary", key="btn_stat"):
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
            st.session_state.generated_source_title = f"통계 추천 ({strategy.split()[1]})"
            st.session_state.fortune_story = ""

# ----------------------------------------------------
# TAB 2: 신규 사주 & 별자리 정밀 운세 기반 번호
# ----------------------------------------------------
with tab_fortune:
    st.markdown("##### 🔮 생년월일과 오늘 일진(日辰)의 기운을 담은 번호")
    st.caption("고정된 생년월일에 '오늘의 날짜'를 대조하여 매일 달라지는 맞춤 재물 오행 번호를 도출합니다.")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_birth_date = st.date_input("📅 생년월일", value=date(1985, 1, 1), min_value=date(1930, 1, 1), max_value=date.today(), key="f_date")
    with col_f2:
        hour_list = [
            "모름 / 무관",
            "자시 (23:30 ~ 01:29)", "축시 (01:30 ~ 03:29)", "인시 (03:30 ~ 05:29)",
            "묘시 (05:30 ~ 07:29)", "진시 (07:30 ~ 09:29)", "사시 (09:30 ~ 11:29)",
            "오시 (11:30 ~ 13:29)", "미시 (13:30 ~ 15:29)", "신시 (15:30 ~ 17:29)",
            "유시 (17:30 ~ 19:29)", "술시 (19:30 ~ 21:29)", "해시 (21:30 ~ 23:29)"
        ]
        f_birth_hour = st.selectbox("⏰ 태어난 시간(시진)", hour_list, key="f_hour")

    f_game_count = st.slider("생성할 게임 수", min_value=1, max_value=10, value=5, key="f_games")
    fortune_mode = st.radio("운세 추천 테마를 선택하세요", [
        "🌿 오늘의 사주 오행 일진 번호 (매일 변경)",
        "⭐ 나의 수호 별자리 행운 번호"
    ], key="f_mode", horizontal=True)

    if st.button("✨ 오늘의 맞춤 행운 번호 뽑기", use_container_width=True, type="primary", key="btn_fortune"):
        today_s = datetime.now().strftime("%Y-%m-%d")
        f_generated = []

        if "사주 오행" in fortune_mode:
            seed_s = f"{f_birth_date}_{f_birth_hour}_{today_s}"
            val = int(hashlib.md5(seed_s.encode()).hexdigest(), 16)
            elem_keys = list(DETAILED_ELEMENT_DATA.keys())
            chosen_elem = elem_keys[val % len(elem_keys)]
            info = DETAILED_ELEMENT_DATA[chosen_elem]
            lucky_pool = info["nums"]

            st.session_state.fortune_story = f"""
### 📜 오늘의 일진(日辰) & 사주 정밀 분석

* **오늘의 중심 기운:** **{chosen_elem}**
* **총평:** {info['fortune']}
* **재물운의 흐름:** {info['money']}
* **오늘의 추천 행동:** {info['action']}
* **행운의 요소:** {info['lucky_items']}

---
💡 **오늘의 오행 핵심 번호:** `{', '.join(map(str, lucky_pool))}`
> 위 번호 풀에 높은 가중치를 배정하여, 오늘 회원님에게 가장 길한 에너지의 번호 조합을 완성했습니다.
            """
            st.session_state.generated_source_title = f"사주 운세 ({info['short']})"

            for i in range(1, f_game_count + 1):
                g_seed = f"saju_{seed_s}_{i}"
                rng = random.Random(g_seed)
                
                weights = [4 if n in lucky_pool else 1 for n in range(1, 46)]
                t_pool = list(range(1, 46))
                t_weights = weights[:]
                p_set = set()
                while len(p_set) < 6 and t_pool:
                    c = rng.choices(t_pool, weights=t_weights, k=1)[0]
                    p_set.add(c)
                    idx = t_pool.index(c)
                    t_pool.pop(idx)
                    t_weights.pop(idx)
                f_generated.append(sorted(list(p_set)))

        else:
            z_sign = get_zodiac_sign(f_birth_date.month, f_birth_date.day)
            z_info = ZODIAC_DATA[z_sign]
            lucky_pool = z_info["nums"]

            st.session_state.fortune_story = f"""
### ⭐ 나의 수호성 & 별자리 정밀 운세

* **당신의 별자리:** **{z_sign}**
* **지배 수호성:** **{z_info['planet']}**
* **운세 조언:** {z_info['desc']}

---
💡 **수호성의 고유 행운 번호:** `{', '.join(map(str, lucky_pool))}`
> 수호성이 지닌 고유 주파수의 숫자를 기점으로 6개 번호를 조화롭게 구성했습니다.
            """
            st.session_state.generated_source_title = f"별자리 운세 ({z_sign.split()[0]})"

            for i in range(1, f_game_count + 1):
                g_seed = f"zodiac_{z_sign}_{today_s}_{i}"
                rng = random.Random(g_seed)
                
                weights = [5 if n in lucky_pool else 1 for n in range(1, 46)]
                t_pool = list(range(1, 46))
                t_weights = weights[:]
                p_set = set()
                while len(p_set) < 6 and t_pool:
                    c = rng.choices(t_pool, weights=t_weights, k=1)[0]
                    p_set.add(c)
                    idx = t_pool.index(c)
                    t_pool.pop(idx)
                    t_weights.pop(idx)
                f_generated.append(sorted(list(p_set)))

        st.session_state.last_generated_games = f_generated

# ================= 공통 추천 결과 화면 & 영구 보관 =================
if st.session_state.last_generated_games:
    st.markdown("---")
    st.subheader(f"🎯 제 {target_next_round}회 추천 조합")
    
    if st.session_state.fortune_story:
        st.markdown(st.session_state.fortune_story)
    
    total_g = len(st.session_state.last_generated_games)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    set_title = st.session_state.generated_source_title
    
    img_data = create_ticket_image(target_next_round, st.session_state.last_generated_games, now_str)
    
    col_save, col_dl = st.columns(2)
    with col_save:
        if st.button(f"💾 보관함에 영구 저장 ({total_g}게임)", type="primary", use_container_width=True, key="btn_save_to_storage"):
            group_ticket = {
                "round": target_next_round,
                "title": f"{set_title} ({total_g}게임)",
                "games": list(st.session_state.last_generated_games),
                "time": datetime.now().strftime("%m-%d %H:%M")
            }
            st.session_state.my_saved_groups.append(group_ticket)
            save_history_to_disk(st.session_state.my_saved_groups)
            st.toast(f"제 {target_next_round}회차 추천 {total_g}게임이 보관함에 저장되었습니다!", icon="📁")
            st.rerun()

    with col_dl:
        st.download_button(
            label="📥 오늘의 추천 번호 사진으로 저장 (PNG)",
            data=img_data,
            file_name=f"로또_{target_next_round}회_추천_{total_g}게임.png",
            mime="image/png",
            use_container_width=True,
            key="btn_download_ticket_png"
        )

    with st.expander("👁️ 저장될 번호 사진 미리보기"):
        st.image(img_data, caption=f"제 {target_next_round}회 추천 번호표", use_container_width=True)

    # 하단 결과 리스트 (일체형 row 렌더링으로 여백 완전 밀착)
    for i, nums in enumerate(st.session_state.last_generated_games, start=1):
        render_game_row(f"{i}번", nums)
