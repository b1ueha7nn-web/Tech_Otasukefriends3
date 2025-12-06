import requests
import json
import datetime

# 星座を判定する関数（誕生日→星座名）
def get_zodiac(month, day):
    zodiac_dates = [
        ("山羊座", (12, 22), (1, 19)),
        ("水瓶座", (1, 20), (2, 18)),
        ("魚座", (2, 19), (3, 20)),
        ("牡羊座", (3, 21), (4, 19)),
        ("牡牛座", (4, 20), (5, 20)),
        ("双子座", (5, 21), (6, 21)),
        ("蟹座", (6, 22), (7, 22)),
        ("獅子座", (7, 23), (8, 22)),
        ("乙女座", (8, 23), (9, 22)),
        ("天秤座", (9, 23), (10, 23)),
        ("蠍座", (10, 24), (11, 22)),
        ("射手座", (11, 23), (12, 21)),
    ]

    for sign, start, end in zodiac_dates:
        # 年をまたぐ星座（山羊座）への対応
        if start[0] == 12:
            if (month == 12 and day >= start[1]) or (month == 1 and day <= end[1]):
                return sign
        else:
            if (month == start[0] and day >= start[1]) or \
               (month == end[0] and day <= end[1]) or \
               (start[0] < month < end[0]):
                return sign

    return None

def get_horoscope(birth_month, birth_day):
    # 今日の日付（API形式）
    date = datetime.datetime.today().strftime("%Y/%m/%d")

    # 星座を判定
    user_sign = get_zodiac(birth_month, birth_day)

    # API取得
    res = requests.get(f"http://api.jugemkey.jp/api/horoscope/free/{date}")
    data = res.json()

    # 今日の12星座一覧
    today_horoscopes = data["horoscope"][date]

    # 星座に一致するデータだけ取り出す
    user_horoscope = next(
        item for item in today_horoscopes if item["sign"] == user_sign
    )

    return user_horoscope

