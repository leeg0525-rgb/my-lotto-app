import csv
from datetime import datetime
import json
import os
import time
import urllib.request

CSV_FILE = "lotto_history.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}


# 1회차(2002-12-07 20:45) 기준 오늘 기준 최신 추첨 회차 계산
def get_estimated_latest_drw():
    first_drw_date = datetime(2002, 12, 7, 20, 45)
    now = datetime.now()
    diff_days = (now - first_drw_date).days
    return (diff_days // 7) + 1


# 동행복권 API에서 단일 회차 가져오기
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


def main():
    last_saved_drw = 0

    # 1. 기존 파일이 있는지 확인하고, 마지막으로 저장된 회차 번호 추출
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = list(csv.reader(f))
            if len(reader) > 1:
                # 마지막 줄의 첫 번째 컬럼(회차)
                last_saved_drw = int(reader[-1][0])
    else:
        # 파일이 없으면 헤더를 넣고 새로 생성
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
        print(f"새로운 '{CSV_FILE}' 파일을 생성했습니다.")

    target_max_drw = get_estimated_latest_drw()
    start_drw = last_saved_drw + 1

    print(f"현재 파일의 마지막 회차: {last_saved_drw}회")
    print(f"조회 대상 회차: {start_drw}회 ~ 최대 {target_max_drw}회\n")

    if start_drw > target_max_drw:
        print("이미 최신 회차까지 모두 저장되어 있습니다.")
        return

    # 2. 누락된 회차만 조회해서 추가(append)
    added_count = 0
    with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        for drw in range(start_drw, target_max_drw + 2):  # 혹시 모를 1주 오차 감안
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
                print(f"[{drw}회] {data['drwNoDate']} 추가 완료")
                added_count += 1
                time.sleep(0.15)
            else:
                # 아직 추첨 전이거나 데이터가 없는 회차를 만나면 탐색 중단
                break

    if added_count > 0:
        print(f"\n총 {added_count}개의 최신 회차가 업데이트되었습니다.")
    else:
        print("\n새롭게 업데이트할 회차가 없습니다. (모두 최신 상태)")


if __name__ == "__main__":
    main()
