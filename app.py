import os
import requests
import streamlit as st
from datetime import datetime, timezone, timedelta
import pandas as pd
from dotenv import load_dotenv

# .env をロード（プロジェクトルートの .env を読みます）
load_dotenv()

# --- 設定 ---
# 優先順位: .env 環境変数 -> Streamlit secrets -> 環境変数（OS）
API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    try:
        API_KEY = st.secrets.get("OPENWEATHER_API_KEY")
    except Exception:
        API_KEY = None
if not API_KEY:
    API_KEY = os.getenv("OPENWEATHER_API_KEY")  # フォールバック（念のため）

# 簡易アイコンマッピング（長いワードを先にマッチするようにソート）
weather_icons = {
    "快晴": "☀️",
    "晴": "☀️",
    "曇": "☁️",
    "雨": "🌧️",
    "霧雨": "🌦️",
    "霧": "🌫️",
    "雪": "❄️",
    "雷": "⚡",
}

def get_weather_icon(desc: str) -> str:
    if not desc:
        return "🌤️"
    for k, v in sorted(weather_icons.items(), key=lambda kv: -len(kv[0])):
        if k in desc:
            return v
    return "🌤️"

# 47都道府県リスト（表示用）
prefectures = [
    "北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県",
    "茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県",
    "新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県",
    "愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県",
    "和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県",
    "香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県",
    "大分県","宮崎県","鹿児島県","沖縄県"
]

# 都道府県名を主要都市名にマッピング（OpenWeatherMap のジオコーディング用）
pref_to_city = {
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

st.title("天気アプリ（OpenWeather 版）")
st.write("都道府県を選択して OpenWeather の天気を表示します。")

if not API_KEY:
    st.error("OpenWeather APIキーが設定されていません。.env に OPENWEATHER_API_KEY を書くか、st.secrets に設定してください。")
    st.stop()

# 選択 UI
selected_pref = st.selectbox("地域を選んでください（都道府県）", prefectures)

# セッションステートで日切り替えインデックス管理（カルーセル代わり）
if 'weather_index' not in st.session_state:
    st.session_state.weather_index = 0

nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
with nav_col1:
    if st.button("◀", key="prev"):
        st.session_state.weather_index = (st.session_state.weather_index - 1) % 3
        st.rerun()
with nav_col3:
    if st.button("▶", key="next"):
        st.session_state.weather_index = (st.session_state.weather_index + 1) % 3
        st.rerun()

# --- キャッシュ付きの API 呼び出し ---
@st.cache_data(ttl=60 * 10)  # 10分キャッシュ（API呼び出しを節約）
def geocode_prefecture(pref_name: str):
    city_name = pref_to_city.get(pref_name, pref_name)
    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": f"{city_name},JP", "limit": 1, "appid": API_KEY}
    r = requests.get(url, params=params, timeout=8)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise ValueError(f"ジオコーディングで結果が見つかりませんでした: {pref_name} ({city_name})")
    return data[0]["lat"], data[0]["lon"], data[0].get("name", city_name)

@st.cache_data(ttl=60 * 5)  # 5分キャッシュ
def fetch_weather(lat: float, lon: float):
    """現在の天気を取得（無料API）"""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "lang": "ja",
        "appid": API_KEY
    }
    r = requests.get(url, params=params, timeout=8)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=60 * 5)  # 5分キャッシュ
def fetch_forecast(lat: float, lon: float):
    """5日間の3時間ごと予報を取得（無料API）"""
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "lang": "ja",
        "appid": API_KEY
    }
    r = requests.get(url, params=params, timeout=8)
    r.raise_for_status()
    return r.json()

def aggregate_daily_forecast(forecast_data):
    """3時間ごとの予報を日次に集約"""
    from collections import defaultdict
    
    daily = defaultdict(lambda: {
        "temps": [],
        "pops": [],
        "weather": [],
        "wind_speeds": [],
        "rain": 0,
        "snow": 0
    })
    
    jst = timezone(timedelta(hours=9))
    
    for item in forecast_data.get("list", []):
        dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc).astimezone(jst)
        date_key = dt.strftime("%Y-%m-%d")
        
        daily[date_key]["temps"].append(item["main"]["temp"])
        daily[date_key]["pops"].append(item.get("pop", 0))
        daily[date_key]["wind_speeds"].append(item.get("wind", {}).get("speed", 0))
        
        if item.get("weather"):
            daily[date_key]["weather"].append(item["weather"][0])
        
        if "rain" in item:
            daily[date_key]["rain"] += item["rain"].get("3h", 0)
        if "snow" in item:
            daily[date_key]["snow"] += item["snow"].get("3h", 0)
    
    result = []
    for date_key in sorted(daily.keys())[:3]:  # 3日分のみ
        d = daily[date_key]
        result.append({
            "dt": datetime.strptime(date_key, "%Y-%m-%d").replace(tzinfo=jst).timestamp(),
            "temp": {
                "max": max(d["temps"]) if d["temps"] else 0,
                "min": min(d["temps"]) if d["temps"] else 0
            },
            "pop": max(d["pops"]) if d["pops"] else 0,
            "weather": [d["weather"][0]] if d["weather"] else [{"description": "不明"}],
            "wind_speed": sum(d["wind_speeds"]) / len(d["wind_speeds"]) if d["wind_speeds"] else 0,
            "rain": d["rain"],
            "snow": d["snow"]
        })
    
    return result

# 実行
try:
    lat, lon, resolved_name = geocode_prefecture(selected_pref)
    current_weather = fetch_weather(lat, lon)
    forecast_data = fetch_forecast(lat, lon)
    
    daily_forecast = aggregate_daily_forecast(forecast_data)

    if len(daily_forecast) < 3:
        st.error("日次予報が取得できませんでした。APIレスポンスを確認してください。")
        st.json({"current": current_weather, "forecast": forecast_data})
        st.stop()

    days_labels = ["今日", "明日", "明後日"]
    idx = st.session_state.weather_index
    day_data = daily_forecast[idx]

    jst = timezone(timedelta(hours=9))
    dt = datetime.fromtimestamp(day_data["dt"], tz=timezone.utc).astimezone(jst)
    date_label = dt.strftime("%Y-%m-%d (%a)")

    weather_desc = day_data.get("weather", [{}])[0].get("description", "不明")
    weather_desc = weather_desc.replace("晴天", "晴れ")
    icon = get_weather_icon(weather_desc)

    temp_max = day_data.get("temp", {}).get("max", "--")
    temp_min = day_data.get("temp", {}).get("min", "--")
    pop = day_data.get("pop", None)
    pop_text = f"{int(pop * 100)}%" if pop is not None else "--"
    wind_speed = day_data.get("wind_speed", "--")
    rain = day_data.get("rain", 0)
    snow = day_data.get("snow", 0)

    st.write(f"選択中の地域: **{selected_pref}**（推定地点: {resolved_name}）")
    st.subheader(f"{days_labels[idx]}の天気 - {date_label}")
    st.markdown(f"<div style='text-align: center; font-size: 80px;'>{icon}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size: 28px;'>{weather_desc}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size: 22px;'>最高: <b>{temp_max}°C</b> / 最低: <b>{temp_min}°C</b></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size: 18px; margin-top: 8px;'>降水確率: <b>{pop_text}</b></div>", unsafe_allow_html=True)

    with st.expander("APIレスポンスを確認（デバッグ）"):
        st.json({"current": current_weather, "forecast": forecast_data})

except requests.HTTPError as e:
    status = e.response.status_code if e.response is not None else "No response"
    st.error(f"HTTP エラー: {status}")
    try:
        st.json(e.response.json())
    except Exception:
        st.write(e.response.text if e.response is not None else str(e))
except requests.RequestException as re:
    st.error(f"ネットワークエラー: {str(re)}")
except Exception as ex:
    st.error(f"エラーが発生しました: {str(ex)}")
    st.stop()