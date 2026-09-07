from collections import Counter
import json
import random
import re
from google import genai
from google.genai import types
from PIL import Image
import requests
import streamlit as st

st.set_page_config(page_title="AI 로또 번호 분석기", page_icon="🎰", layout="centered")

# --- 설정: Gemini API 키 입력 ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "여기에_발급받은_GEMINI_API_키_입력")

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

# AI 시각 판독 함수 (Gemini Flash 사용)
def read_lotto_numbers_with_ai(image_file):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        img = Image.open(image_file)
        
        prompt = """
        이 사진은 한국 로또 6/45 복권 용지입니다.
        용지에 인쇄된 게임별(A, B, C, D, E 등) 6자리 로또 번호들을 모두 찾아서 읽어주세요.
        결과는 오직 1부터 45 사이의 정수들이 들어있는 단일 JSON 숫자 배열 형식으로만 응답하세요.
        예: [3, 11, 14, 18, 22, 35, 7, 12, ...]
        추가 설명이나 마크다운 코드블록(```json 등) 없이 오직 JSON 배열만 반환하세요.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img]
        )
        
        cleaned = re.sub(r'[^0-9,]', '', response.text)
        nums = [int(n) for n in cleaned.split(',') if n.isdigit() and 1 <= int(n) <= 45]
        return sorted(list(set(nums)))
    except Exception as e:
        st.error(f"AI 이미지 판독 중 오류 발생: {e}")
        return []

@st.cache_data(ttl=3600)
def load_lotto_data():
    url = "[https://raw.githubusercontent.com/jonghwan-park/lotto-history/main/data.json](https://raw.githubusercontent.com/jonghwan-park/lotto-history/main/data.json)"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return [{"round": 1135, "numbers": [1, 6, 13, 19, 21, 33]}]

# --- UI 메인 ---
st.title("🎰 맞춤 로또 번호 추출기")
st.caption("로또 용지 사진을 올리면 AI가 이미 산 번호를 자동으로 읽어 제외하고 새로 뽑아줍니다.")

data = load_lotto_data()

# 세션 상태로 판독된 제외 번호 관리
if "excluded_nums" not in st.session_state:
    st.session_state.excluded_nums = []

# 1. 사진 첨부로 간편 번호 제외
with st.
