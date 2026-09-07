import csv
from datetime import datetime
import json
import os
import time
import urllib.request

CSV_FILE = "lotto_history.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}


# 1회차(2002-12-07 20:00) 기준 현재 예상 최신 회차 계산
def get_current_max_drw():
    first_date = datetime(2002, 12, 7, 20, 45)
    now = datetime.now()
    diff_days = (now - first_date).days
    return (diff_days // 7) + 1


def fetch_lotto(drw_no):
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drw_no}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("returnValue") == "success":
                return data
    except Exception:
        return None
    return None


# 파일에 저장된 마지막 회차 확인
last_saved = 0
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        if len(reader) > 1:
            last_saved = int(reader[-1][0])
else:
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "회차",
                "추첨일자",
                "번호1",
                "번호2",
                "번호3",
                "번호4",
                "번호5",
                "번호6",
                "보너스",
                "1등당첨금",
            ]
        )

max_drw = get_current_max_drw()
start_drw = last_saved + 1

if start_drw > max_drw:
    print("이미 최신 회차까지 모두 저장되어 있습니다.")
else:
    with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        for drw in range(start_drw, max_drw + 1):
            data = fetch_lotto(drw)
            if data:
                writer.writerow(
                    [
                        data["drwNo"],
                        data["drwNoDate"],
                        data["drwtNo1"],
                        data["drwtNo2"],
                        data["drwtNo3"],
                        data["drwtNo4"],
                        data["drwtNo5"],
                        data["drwtNo6"],
                        data["bnusNo"],
                        data["firstWinamnt"],
                    ]
                )
                print(f"[{drw}회] 추가 완료")
                time.sleep(0.2)
            else:
                print(f"[{drw}회] 아직 추첨 전이거나 데이터 없음")
                break
