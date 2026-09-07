import csv
import json
import time
import urllib.request

# 1. 최신 회차 찾기 (최신 번호부터 역순으로 100개 수집)
headers = {"User-Agent": "Mozilla/5.0"}


def get_lotto_data(drw_no):
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drw_no}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("returnValue") == "success":
                return data
    except Exception as e:
        return None
    return None


# 기준이 되는 최신 회차 번호를 직접 입력하거나 지정하세요 (예: 1160 등)
# 아래는 1160회부터 역순으로 100개를 수집하는 예시입니다.
latest_drw = 1160
count = 100
start_drw = latest_drw - count + 1

output_filename = f"lotto_{start_drw}_to_{latest_drw}.csv"

with open(output_filename, "w", newline="", encoding="utf-8-sig") as f:
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

    print(f"{start_drw}회차부터 {latest_drw}회차까지 실제 데이터 다운로드 시작...")

    for drw in range(latest_drw, start_drw - 1, -1):
        data = get_lotto_data(drw)
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
            print(f"[{data['drwNo']}회] {data['drwNoDate']} 수집 완료")
        else:
            print(f"[{drw}회] 조회 실패 또는 미추첨 회차")

        time.sleep(0.1)  # 서버 부하 방지용 짧은 딜레이

print(f"\n저장 완료: {output_filename}")
