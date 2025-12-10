# weather_api.py
import os
import requests
import streamlit as st
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from dotenv import load_dotenv

# .env をロード
load_dotenv()

# JST (日本標準時) タイムゾーンオブジェクト
JST = timezone(timedelta(hours=9))

# 簡易アイコンマッピング（Streamlit側でも使用するため、ここで定義）
WEATHER_ICONS = {
    "快晴": "☀️", "晴": "☀️", "曇": "☁️", "雨": "🌧️",
    "霧雨": "🌦️", "霧": "🌫️", "雪": "❄️", "雷": "⚡",
}

# 都道府県名を主要都市名にマッピング（OpenWeatherMap のジオコーディング用）
PREF_TO_CITY = {
    "北海道": "Sapporo", "青森県": "Aomori", "岩手県": "Morioka", "宮城県": "Sendai",
    "秋田県": "Akita", "山形県": "Yamagata", "福島県": "Fukushima",
    "茨城県": "Mito", "栃木県": "Utsunomiya", "群馬県": "Maebashi",
    "埼玉県": "Saitama", "千葉県": "Chiba", "東京都": "Tokyo", "神奈川県": "Yokohama",
    "新潟県": "Niigata", "富山県": "Toyama", "石川県": "Kanazawa", "福井県": "Fukui",
    "山梨県": "Kofu", "長野県": "Nagano", "岐阜県": "Gifu",
    "静岡県": "Shizuoka", "愛知県": "Nagoya", "三重県": "Tsu",
    "滋賀県": "Otsu", "京都府": "Kyoto", "大阪府": "Osaka", "兵庫県": "Kobe",
    "奈良県": "Nara", "和歌山県": "Wakayama",
    "鳥取県": "Tottori", "島根県": "Matsue", "岡山県": "Okayama", "広島県": "Hiroshima",
    "山口県": "Yamaguchi", "徳島県": "Tokushima", "香川県": "Takamatsu",
    "愛媛県": "Matsuyama", "高知県": "Kochi",
    "福岡県": "Fukuoka", "佐賀県": "Saga", "長崎県": "Nagasaki", "熊本県": "Kumamoto",
    "大分県": "Oita", "宮崎県": "Miyazaki", "鹿児島県": "Kagoshima", "沖縄県": "Naha"
}

def get_api_key() -> str | None:
    """APIキーのロードロジックを集中管理"""
    # 優先順位: .env 環境変数 -> Streamlit secrets -> 環境変数（OS）
    key = os.getenv("OPENWEATHER_API_KEY")
    if not key:
        try:
            # st.secrets のチェックは Streamlit 実行時にのみ可能
            if st.runtime.exists():
                key = st.secrets.get("OPENWEATHER_API_KEY")
        except Exception:
            pass # Streamlit 環境外では無視
    return key

def get_weather_icon(desc: str) -> str:
    """天気の説明からアイコンを返す"""
    if not desc:
        return "🌤️"
    # 長いワードを先にマッチするようにソート
    for k, v in sorted(WEATHER_ICONS.items(), key=lambda kv: -len(kv[0])):
        if k in desc:
            return v
    return "🌤️"

# --- キャッシュ付きの API 呼び出し ---
@st.cache_data(ttl=60 * 10)  # 10分キャッシュ
def geocode_prefecture(pref_name: str, api_key: str) -> tuple[float, float, str]:
    """都道府県名から緯度・経度を取得し、解決された地名を返す"""
    city_name = PREF_TO_CITY.get(pref_name, pref_name)
    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": f"{city_name},JP", "limit": 1, "appid": api_key}
    r = requests.get(url, params=params, timeout=8)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise ValueError(f"ジオコーディングで結果が見つかりませんでした: {pref_name} ({city_name})")
    
    lat = data[0]["lat"]
    lon = data[0]["lon"]
    resolved_name = data[0].get("name", city_name)
    
    return lat, lon, resolved_name

@st.cache_data(ttl=60 * 5)  # 5分キャッシュ
def fetch_current_weather(lat: float, lon: float, api_key: str) -> dict:
    """現在の天気を取得（無料API）"""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "lang": "ja",
        "appid": api_key
    }
    r = requests.get(url, params=params, timeout=8)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=60 * 5)  # 5分キャッシュ
def fetch_forecast(lat: float, lon: float, api_key: str) -> dict:
    """5日間の3時間ごと予報を取得（無料API）"""
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "lang": "ja",
        "appid": api_key
    }
    r = requests.get(url, params=params, timeout=8)
    r.raise_for_status()
    return r.json()

def aggregate_daily_forecast(forecast_data: dict) -> list[dict]:
    """3時間ごとの予報を日次に集約し、最大3日分を返す"""
    daily = defaultdict(lambda: {
        "temps": [], "pops": [], "weather": [], "wind_speeds": [],
        "rain": 0, "snow": 0
    })
    
    for item in forecast_data.get("list", []):
        # UTCからJSTへ変換
        dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc).astimezone(JST)
        date_key = dt.strftime("%Y-%m-%d")
        
        daily[date_key]["temps"].append(item["main"]["temp"])
        daily[date_key]["pops"].append(item.get("pop", 0))
        daily[date_key]["wind_speeds"].append(item.get("wind", {}).get("speed", 0))
        
        if item.get("weather"):
            # 天気アイコン/説明は、その日の最初の予報を採用することが多いが、ここではリストとして保持
            daily[date_key]["weather"].append(item["weather"][0])
        
        # 降水量・降雪量を累積（3時間分ずつ）
        if "rain" in item:
            daily[date_key]["rain"] += item["rain"].get("3h", 0)
        if "snow" in item:
            daily[date_key]["snow"] += item["snow"].get("3h", 0)
    
    result = []
    # キーを日付順にソートし、最初の3日分のみ処理
    for date_key in sorted(daily.keys())[:3]:
        d = daily[date_key]
        
        # 代表的な天気（ここではその日の最初の予報、または出現頻度最大のものなどを選ぶのが一般的だが、ここでは最初のものを採用）
        main_weather = d["weather"][0] if d["weather"] else {"description": "不明", "icon": "01d"}

        result.append({
            "dt": datetime.strptime(date_key, "%Y-%m-%d").replace(tzinfo=JST).timestamp(),
            "temp": {
                "max": max(d["temps"]) if d["temps"] else 0,
                "min": min(d["temps"]) if d["temps"] else 0
            },
            "pop": max(d["pops"]) if d["pops"] else 0, # 最大降水確率を採用
            "weather": [main_weather],
            "wind_speed": sum(d["wind_speeds"]) / len(d["wind_speeds"]) if d["wind_speeds"] else 0, # 平均風速
            "rain": d["rain"],
            "snow": d["snow"]
        })
    
    return result