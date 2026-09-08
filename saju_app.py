# 추천 번호표 사진 이미지 생성 함수 (2배 고해상도 안티앨리어싱 적용)
def create_ticket_image(round_no, games_list, time_str, ticket_title=""):
    scale = 2  # 선명도를 위한 2배 슈퍼샘플링
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

    # 외곽 테두리
    draw.rectangle([(6 * scale, 6 * scale), (w - 7 * scale, h - 7 * scale)], outline=(220, 220, 220), width=2 * scale)

    # 상단 텍스트 (AI 제거 -> LOTTO 6/45, [통계_요즘] 제거 -> 제 1241회 추천 조합)
    draw.text((w // 2, 28 * scale), "LOTTO 6/45", fill=(45, 45, 45), font=font_title, anchor="mm")
    draw.text((w // 2, 56 * scale), f"제 {round_no}회 추천 조합", fill=(30, 90, 200), font=font_round, anchor="mm")
    draw.text((w // 2, 82 * scale), f"발행일시: {time_str}", fill=(130, 130, 130), font=font_main, anchor="mm")
    draw.line([(20 * scale, 100 * scale), (w - 20 * scale, 100 * scale)], fill=(230, 230, 230), width=scale)

    labels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    y_curr = header_h
    r = 15 * scale  # 공 반지름

    for idx, nums in enumerate(games_list):
        lbl = labels[idx] if idx < len(labels) else str(idx + 1)
        draw.text((32 * scale, y_curr + 18 * scale), f"{lbl} 자 동", fill=(90, 90, 90), font=font_main, anchor="lm")

        start_x = 100 * scale
        gap = 45 * scale
        for b_idx, n in enumerate(sorted(nums)):
            cx = start_x + (b_idx * gap)
            cy = y_curr + 18 * scale
            bg_color = get_ball_rgb(n)
            # 안티앨리어싱된 부드러운 원형 생성
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=bg_color)
            draw.text((cx, cy), str(n), fill=(255, 255, 255), font=font_ball, anchor="mm")

        y_curr += row_h

    draw.line([(20 * scale, y_curr + 4 * scale), (w - 20 * scale, y_curr + 4 * scale)], fill=(230, 230, 230), width=scale)
    draw.text((w // 2, y_curr + 24 * scale), "1등 당첨을 진심으로 기원합니다!", fill=(140, 140, 140), font=font_main, anchor="mm")

    # 최종 결과물을 최적의 크기로 부드럽게 리샘플링
    final_img = img.resize((base_w, base_h), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    final_img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
