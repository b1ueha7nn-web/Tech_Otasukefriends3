import streamlit as st
from datetime import date, datetime
from weather import weather_api, get_weather_icon
from news_api import news_get
from hour_calc import diff_hour
from horoscope import get_horoscope
from db import supabase
import os
from dotenv import load_dotenv
load_dotenv()
import json
from weather_api import (
    geocode_prefecture, fetch_current_weather, 
    fetch_forecast, aggregate_daily_forecast, get_weather_icon, JST
)


#========================================
# Supabase に設定を保存する関数
#========================================
def save_settings_to_supabase():
    """st.session_state.settings の内容を users テーブルに 1 行保存する"""

    auth_user_id = st.session_state.get("auth_user_id")
    if not auth_user_id:
        st.error("ログインユーザーが取得できません。先にログインしてください。")
        return None

    s = st.session_state.settings
    categories_json = json.dumps(s.get("categories", []), ensure_ascii=False)

    data = {
        "auth_user_id": auth_user_id,
        "birth_year":   s.get("birth_year"),
        "birth_month":  s.get("birth_month"),
        "birth_day":    s.get("birth_day"),
        "home_pref":    s.get("home_pref"),
        "work_pref":    s.get("work_pref"),
        "categories":   categories_json,
    }

    res = (
        supabase
        .table("users")
        .upsert(data, on_conflict="auth_user_id")
        .execute()
    )

    return res



def load_settings_from_supabase():
    #Supabase の users テーブルから、このユーザーの設定を読み込む"""

    auth_user_id = st.session_state.get("auth_user_id")
    if not auth_user_id:
        return  # ログインしていなければ何もしない

    res = (
        supabase
        .table("users")
        .select("*")
        .eq("auth_user_id", auth_user_id)
        .maybe_single()      # 0 or 1 件想定
        .execute()
    )

    if res.data:
        row = res.data
        st.session_state.settings = {
            "birth_year":  row.get("birth_year"),
            "birth_month": row.get("birth_month"),
            "birth_day":   row.get("birth_day"),
            "home_pref":   row.get("home_pref"),
            "work_pref":   row.get("work_pref"),
            "categories":  json.loads(row.get("categories") or "[]"),
        }



# ======================================
# ページの基本設定
# ======================================
st.set_page_config(
    page_title="OTASUKE", #名前は適当です。その日の要点を詰めてるイメージの名前にしてみました
    page_icon="☀️",
    layout="centered",
)

#======================================
#CSS
#======================================
st.markdown("""
<style>
/* 春の花畑背景 - ピンクと黄色の柔らかなグラデーション */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #FFF9FB 0%, #FFF0F3 20%, #FFF9E6 40%, #F0F9F0 60%, #F8F9FF 80%, #FFF5F8 100%);
    background-size: 400% 400%;
    animation: flowerField 25s ease infinite;
}

@keyframes flowerField {
    0%, 100% { background-position: 0% 50%; }
    25% { background-position: 50% 25%; }
    50% { background-position: 100% 50%; }
    75% { background-position: 50% 75%; }
}

/* メインカード - 花びらのような優しさ */
.main-card {
    background: linear-gradient(135deg, #FFFFFF 0%, #FFF8FA 100%);
    padding: 36px;
    border-radius: 28px;
    box-shadow: 0 12px 35px rgba(255, 182, 193, 0.12);
    margin: 24px 0;
    border: 3px solid #FFD4E5;
    animation: fadeIn 0.7s ease, float 6s ease-in-out infinite;
    position: relative;
    overflow: hidden;
}

.main-card::before {
    content: '🌸';
    position: absolute;
    top: 10px;
    right: 15px;
    font-size: 32px;
    opacity: 0.15;
}

.main-card::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 5px;
    background: linear-gradient(90deg, #FFCCE0, #FFE0ED, #FFE8F5, #FFE0ED, #FFCCE0);
    border-radius: 28px 28px 0 0;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-5px); }
}

/* 情報カード - チューリップの花びら */
.info-card {
    background: linear-gradient(135deg, #FFFFFF 0%, #FFFBFC 100%);
    padding: 32px;
    border-radius: 24px;
    box-shadow: 0 10px 30px rgba(255, 182, 193, 0.18);
    margin-bottom: 24px;
    border: 3px solid #FFE5ED;
    transition: all 0.5s ease;
    position: relative;
    overflow: hidden;
}

.info-card::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 150px;
    height: 150px;
    background: radial-gradient(circle, rgba(255, 182, 193, 0.15) 0%, transparent 70%);
    border-radius: 50%;
}

.info-card:hover {
    transform: translateY(-10px) scale(1.02);
    box-shadow: 0 20px 50px rgba(255, 182, 193, 0.28);
    border-color: #FFD4E5;
}

/* ニュースカード - 菜の花畑のイメージ */
.news-card {
    background: linear-gradient(135deg, #FFFEF9 0%, #FFF9F0 100%);
    padding: 28px;
    border-radius: 22px;
    box-shadow: 0 8px 25px rgba(255, 215, 0, 0.2);
    margin-bottom: 24px;
    border: 3px solid #FFE8B6;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
}

.news-card::after {
    content: '✿';
    position: absolute;
    bottom: 15px;
    right: 20px;
    font-size: 24px;
    color: #FFD700;
    opacity: 0.3;
}

.news-card:hover {
    transform: translateY(-6px) rotate(1deg);
    box-shadow: 0 15px 40px rgba(255, 215, 0, 0.3);
    border-color: #FFD700;
}

.news-card img {
    width: 100%;
    height: 220px;
    border-radius: 16px;
    margin-bottom: 18px;
    object-fit: cover;
    box-shadow: 0 6px 18px rgba(255, 182, 193, 0.2);
    filter: saturate(1.1);
}

/* プログレスバー - 春の花グラデーション */
.progress-wrapper {
    width: 100%;
    height: 16px;
    background: linear-gradient(90deg, #FFF0F3, #FFF9E6, #F0F9F0);
    border-radius: 20px;
    overflow: hidden;
    margin-top: 16px;
    box-shadow: inset 0 3px 8px rgba(255, 182, 193, 0.12);
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #FFB6C1, #FFCCE0, #FFE89F, #B8E6B8);
    transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 20px;
    box-shadow: 0 3px 12px rgba(255, 182, 193, 0.3);
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.85; }
}

/* ボタン - 春の花びら */
div.stButton > button {
    background: linear-gradient(135deg, #FFB6C1, #FFCCE0, #FFD4E5) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 20px !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    padding: 16px 40px !important;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 8px 20px rgba(255, 182, 193, 0.3) !important;
    letter-spacing: 1px !important;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #FFA0B4, #FFB6C1, #FFCCE0) !important;
    transform: translateY(-4px) scale(1.05) !important;
    box-shadow: 0 12px 30px rgba(255, 182, 193, 0.4) !important;
}

div.stButton > button:active {
    transform: translateY(-2px) scale(1.02) !important;
}

/* セレクトボックス - 花びらの丸み */
div[data-baseweb="select"] {
    border-radius: 14px !important;
    border-color: #FFD4E5 !important;
}

/* フェードインアニメーション */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* タイトル - 春の花色 */
h1, h2, h3, h4 {
    color: #FFB6C1;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-shadow: 2px 2px 4px rgba(255, 182, 193, 0.15);
}

/* 花びらの装飾 */
.flower-decoration {
    display: inline-block;
    margin: 0 8px;
    font-size: 24px;
    animation: rotate 10s linear infinite;
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
    .info-card, .news-card, .main-card {
        padding: 22px;
        margin-bottom: 20px;
    }
    
    .news-card img {
        height: 180px;
    }
}

</style>
""", unsafe_allow_html=True)

# ======================================
# セッションの初期化
# ======================================


# 都道府県リスト
PREF_LIST = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県",
    "沖縄県",
]

# ニュースジャンルリスト（例）
CATEGORY_LIST = [
    "テクノロジー", "ビジネス", "スポーツ", "政治", "国際",
    "エンタメ", "健康", "ライフスタイル", "経済", "科学",
    "環境", "教育",
]

# ======================================
# 共通ヘッダー
# ======================================
def render_header():
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown("### 🌸 OTASUKE 🌷")
    with cols[1]:
        today = datetime.today()
        st.markdown(
            f"""
            <div style="text-align:right; font-size:14px; color:#FFB6C1; font-weight:700;">
                {today.strftime('%m/%d (%a)')} 🌺
            </div>
            """,
            unsafe_allow_html=True,
        )

# ======================================
# プログレスバー　設定画面
# ======================================
def render_progress(step: int, total: int = 4):
    ratio = int(100 * step / total)
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size:13px;color:#6b7280;">{step}ページ / {total}ページ</div>
        </div>
        <div class="progress-wrapper">
            <div class="progress-bar" style="width:{ratio}%;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ======================================
# ステップ1：生年月日
# ======================================
def step_birthdate():
    st.markdown("#### 生年月日を入力してください")
    st.caption("あなたにあった情報や星座占いをお届けします！")

    year = st.selectbox(
        "年",
        options=["選択してください"] + list(range(1950, date.today().year + 1)),
        index=0,
    )
    col_m, col_d = st.columns(2)
    with col_m:
        month = st.selectbox("月", options=["選択してください"] + list(range(1, 13)))
    with col_d:
        day = st.selectbox("日", options=["選択してください"] + list(range(1, 32)))

    # 保存（実際のバリデーションはお好みで）
    st.session_state.settings["birth_year"] = year if year != "選択してください" else None
    st.session_state.settings["birth_month"] = month if month != "選択してください" else None
    st.session_state.settings["birth_day"] = day if day != "選択してください" else None

# ======================================
# ステップ2：居住地域/勤務地
# ======================================
def step_home_region():
    st.markdown("#### お住まいの地域を教えてください")
    st.caption("地域の天気予報をお届けします")

    home = st.selectbox("都道府県", options=["選択してください"] + PREF_LIST)
    st.session_state.settings["home_pref"] = home if home != "選択してください" else None

# ======================================
# (ステップ3)：勤務地
# ======================================
def step_work_region():
    st.markdown("#### 勤務地を教えてください")
    st.caption("勤務先周辺の天気をお届けします")

    work = st.selectbox("都道府県", options=["選択してください"] + PREF_LIST)
    st.session_state.settings["work_pref"] = work if work != "選択してください" else None

# ======================================
# ステップ4：ニュースジャンル
# ======================================
def step_categories():
    st.markdown("#### 興味のあるニュースジャンルを選択してください")
    st.caption("複数選択可能です。選択したジャンルのニュースを優先的にお届けします！")

    options = CATEGORY_LIST  # 既存リストを使用

    selection = st.pills(
        label="ジャンル",
        options=options,
        selection_mode="multi"
    )

    # 選択数
    st.markdown(
        f"<p style='font-size:13px;color:#6b7280;'>選択中：{len(selection)}個</p>",
        unsafe_allow_html=True
    )

    # 必要であれば session_state に保存
    st.session_state.settings["categories"] = selection


# ======================================
# ダッシュボード（メイン画面）
# ======================================
def render_dashboard():
    cols = st.columns([6, 1])
    with cols[1]:
        # 右上に小さな「設定」ボタン
        if st.button("⚙️ 設定", key="header_settings"):
            st.session_state.page = "onboarding"
            st.session_state.step = 1  # 生年月日からやり直し（好みで変更OK）
            st.rerun()

    render_header()
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    today = datetime.today()
    
    st.markdown(
        f"**{today.strftime('%m月%d日（%a）')}**",
    )

    st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)

    # # 追加
    # # 開発中は True、本番テストは False にする（API100回制限ありのため）
    # USE_TEST_DATA = True
    # if USE_TEST_DATA:
    #     # ----------------------------
    #     # test_news.txt を読み込む
    #     # ----------------------------
    #     with open("test_news.txt", "r", encoding="utf-8") as f:
    #         news_data = f.read()
    #         st.info("📝 開発モード：test_news.txt を使っています（API未使用）")
    # else:
    #     # ----------------------------
    #     # 本番 API を呼び出す
    #     # ----------------------------
    #     news_data = call_news_api(NEWS_API_KEY)
    #     st.success("本番モード：APIを使用しています")

    # # 読み込んだニュースを表示する処理（あなたの UI に合わせて）
    # st.write(news_data)

    # 天気
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    home_pref = st.session_state.settings.get("home_pref") or "東京"
    # st.write("DEBUG - home_pref:", home_pref)
    lat, lon, resolved_name = geocode_prefecture(home_pref, OPENWEATHER_API_KEY)
    current_weather = fetch_current_weather(lat, lon, OPENWEATHER_API_KEY)
    forecast_data = fetch_forecast(lat, lon, OPENWEATHER_API_KEY)    
    daily_forecast = aggregate_daily_forecast(forecast_data)
    day_data = daily_forecast[0]
    weather_desc = day_data.get("weather", [{}])[0].get("description", "不明")
    weather_desc = weather_desc.replace("晴天", "晴れ")
    icon = get_weather_icon(weather_desc) # アイコン取得もモジュール化

    temp_max = day_data.get("temp", {}).get("max", "--")
    temp_min = day_data.get("temp", {}).get("min", "--")
    pop = day_data.get("pop", None)*100
    # telop, max_temp, min_temp = weather_api(home_pref)
    # icon = get_weather_icon(telop)

    st.markdown(
        f"""
        <div class="info-card weather-card">
            <div style="font-size:14px; color:#FF8C00; font-weight:600; margin-bottom:8px;">☀️ 今日の天気</div>
            <div style="display:flex; align-items:center; gap:20px; margin-top:8px;">
                <div style="font-size:72px; line-height:1;">{icon}</div>
                <div>
                    <div style="font-size:16px; color:#666; margin-bottom:4px;">【{home_pref}】</div>
                    <div style="font-size:48px; font-weight:700; color:#FF6347; line-height:1;"> {temp_max}°</div>
                    <div style="font-size:16px; color:#888; margin-top:4px;">最低気温 {temp_min}°</div>
                    <div style="font-size:15px; color:#666; margin-top:4px;">降水確率 {pop}%</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 星占い （記載は一例、APIで取得できる情報を記載する）
    birth_month = st.session_state.settings["birth_month"]
    birth_day = st.session_state.settings["birth_day"]

    horoscope_result = get_horoscope(birth_month, birth_day)
    st.markdown(
        f"""
        <div class="info-card fortune-card">
            <div style="font-size:14px; color:#9370DB; font-weight:600; margin-bottom:8px;">✨ 今日の運勢</div>
            <div style="font-size:20px; font-weight:700; color:#FF69B4; margin-bottom:6px;">
                {horoscope_result["sign"]} 🌟 {horoscope_result["rank"]}位
            </div>
            <div style="font-size:14px; line-height:1.6; color:#555; margin:12px 0; padding:12px; background:#FFF8F0; border-radius:10px;">
                {horoscope_result["content"]}
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:14px; font-size:13px;">
                <div style="background:#FFF0F5; padding:10px; border-radius:10px;">🎨 {horoscope_result["color"]}</div>
                <div style="background:#F0F8FF; padding:10px; border-radius:10px;">🎁 {horoscope_result["item"]}</div>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:10px; font-size:13px; color:#666;">
                <div style="padding:8px; background:#FFF5EE; border-radius:8px;">💼 仕事 {horoscope_result["job"]}</div>
                <div style="padding:8px; background:#F0FFF0; border-radius:8px;">💰 お金 {horoscope_result["money"]}</div>
                <div style="padding:8px; background:#FFF0F5; border-radius:8px;">💕 恋愛 {horoscope_result["love"]}</div>
                <div style="padding:8px; background:#F0F8FF; border-radius:8px;">⭐ 総合 {horoscope_result["total"]}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 🔸 あなたへのおすすめニュース")

    select_categories = st.session_state.settings.get("categories", [])
    articles = news_get(NEWS_API_KEY, select_categories)

    # ニュースカード（ダミーを2件ほど）
    
    for i in range(len(articles)):
        delta = diff_hour(articles[i]["publishedAt"])
        
        st.markdown(
            f"""
            <div class="news-card">
                {f'<img src="{articles[i]["urlToImage"]}" alt="ニュース画像">' if articles[i]["urlToImage"] else ''}
                <div style="font-size:16px; font-weight:700; color:#333; margin-bottom:8px; line-height:1.4;">
                    {articles[i]["title"]}
                </div>
                <div style="font-size:14px; color:#555; line-height:1.6; margin-bottom:10px;">
                    {articles[i]["description"]}
                </div>
                <div style="font-size:11px; color:#999;">
                    🕐 {delta}時間前
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button(
            label="📰 記事を読む",
            url=articles[i]["url"],
            help="クリックすると記事の詳細ページに移動します"
        )
    # ======================================
    # 設定に戻るボタン
    # ======================================




# ======================================
# メイン処理
# ======================================
TOTAL_STEPS = 4

def onboarding_screen():
    st.title("OTASUKE")

    step = st.session_state.step

    # ステップごとの表示
    if step == 1:
        step_birthdate()
    elif step == 2:
        step_home_region()
    elif step == 3:
        step_work_region()
    elif step == 4:
        step_categories()

    # ナビゲーションボタン
    col_back, col_next = st.columns(2)

    with col_back:
        if st.button("＜ 戻る", disabled=step == 1):
            if step > 1:
                st.session_state.step -= 1
                st.rerun()

    with col_next:
        # 最後のステップだけ「完了」ボタンにする
        if step < TOTAL_STEPS:
            if st.button("次へ ＞"):
                if step < TOTAL_STEPS:
                    st.session_state.step += 1
                    st.rerun()
        else:
            if st.button("完了"):
                # デバッグ用に今の状態を表示（動作確認したら消してOK）
                st.write("DEBUG: 完了ボタンが押されました")
                st.write("DEBUG: 保存前 page =", st.session_state.page)

                # Supabase に保存
                try:
                    res = save_settings_to_supabase()
                    if res is not None:
                        st.success("設定を保存しました！")
                    # 保存に成功しても失敗しても、とりあえずダッシュボードへ
                        st.session_state.page = "dashboard"
                        st.rerun()
                except Exception as e:
                    st.error(f"設定の保存中にエラーが発生しました: {e}")
                    
                # 保存の成否にかかわらずダッシュボードへ
                st.session_state.page = "dashboard"
                st.rerun()
    
#=====================================
#認証用の関数
#======================================
def sign_up(email, password):
    try:
        user = supabase.auth.sign_up({"email": email, "password": password})
        if user and user.user:
            # Supabase Auth のユーザーIDをセッションに保存
            st.session_state["auth_user_id"] = user.user.id
        return user
    except Exception as e:
        st.error(f"サインアップ中にエラーが発生しました: {e}")
        return None

def sign_in(email, password):
    #既存ユーザーでログインし、auth_user_id をセッションに保存する
    try:
        user = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        if user and user.user:
            # ★ Supabaseの user.id をセッションに保持
            st.session_state["auth_user_id"] = user.user.id
        return user

    except Exception as e:
        st.error(f"ログイン中にエラーが発生しました: {e}")
        return None
    
def sign_out():
    try:
        supabase.auth.sign_out()
    except Exception as e:
        st.error(f"サインアウト中にエラーが発生しました: {e}")
    
def main_app(user_email):
    st.title(f"ようこそ、{user_email}さん！")
    st.success(f"ログインに成功しました。")
    if st.button("ログアウト"):
        sign_out()
        st.session_state.user_email = None
        st.session_state.page = "auth"
        st.rerun()
    
#======================================
#  認証画面
#======================================
def auth_screen():
    st.title("OTASUKEへようこそ！")

    # ログイン or サインアップ 選択
    option = st.selectbox(
        "選択してください",
        ["ログイン", "サインアップ"],
        help="初めて利用する場合は『サインアップ』を選択してください"
    )

    # 選択内容に応じた説明
    if option == "サインアップ":
        st.caption("初めてOTASUKEを使う方は、こちらでアカウントを作成します。")
    else:
        st.caption("すでに登録済みの方は『ログイン』を選んでください。")

    # メールアドレス
    email = st.text_input("メールアドレス")

    # パスワード
    password = st.text_input("パスワード", type="password")
    st.caption("※ 半角英数字8文字以上を推奨します。英字・数字を組み合わせたパスワードにしてください。")

  # パスワードリセットボタンは option がログインのときだけ表示
    if option == "ログイン":
        if st.button("パスワードを忘れた場合はこちら"):
            if not email:
                st.warning("先にメールアドレスを入力してください。")
            else:
                send_reset_email(email)

    #======================================    
    #ログイン処理
    #======================================
    if option == "ログイン" and st.button("ログイン"):
        user = sign_in(email,password)
        if user and user.user:
            st.session_state.user_email = user.user.email
            load_settings_from_supabase()
            st.success("ログインに成功しました！")
            #Dashboardへ遷移
            st.session_state.page = "dashboard"
            st.rerun()
    
    #======================================
    #サインアップ処理
    #======================================
    if option == "サインアップ" and st.button("サインアップ"):
        user = sign_up(email,password)
        if user and user.user:
            st.success("サインアップに成功しました！")
            #オンボーディングへ遷移
            st.session_state.page = "onboarding"
            st.rerun()
        # st.session_state.page = "onboarding"
        # st.rerun()

#======================================
# パスワード再設定画面　★追加
#======================================
def reset_password_screen():
    st.title("パスワードの再設定")

    st.write("メールに届いたリンクからこの画面を開いているはずです。")
    st.write("新しいパスワードを入力してください。")

    new_password = st.text_input("新しいパスワード", type="password")
    new_password_confirm = st.text_input("新しいパスワード（確認用）", type="password")

    if st.button("パスワードを変更する"):
        if not new_password or not new_password_confirm:
            st.warning("両方の入力欄にパスワードを入力してください。")
            return
        
        if new_password != new_password_confirm:
            st.error("新しいパスワードと確認用パスワードが一致しません。")
            return
        
        if len(new_password) < 8:
            st.warning("8文字以上のパスワードをおすすめします。")

        try:
            # Supabase に新しいパスワードを反映
            res = supabase.auth.update_user({"password": new_password})
            st.success("パスワードを変更しました。ログイン画面に戻ります。")

            # ログイン画面へ戻す
            st.session_state.page = "auth"
            st.rerun()

        except Exception as e:
            st.error(f"パスワード変更中にエラーが発生しました: {e}")


#======================================
#パスワードリセットメール送信
#======================================
def send_reset_email(email: str):
    """Supabase の機能でパスワードリセットメールを送る"""
    try:
        supabase.auth.reset_password_for_email(
            email,
            {
                # ★本番の Streamlit の URL に合わせて変更する
                "redirect_to": "https://techotasukefriends-w3fhwuydwqhsbi9spgcrfx.streamlit.app/?mode=reset"
            },
        )
        st.success("パスワード再設定用のメールを送信しました。メールを確認してください。")
    except Exception as e:
        st.error(f"パスワードリセットメール送信中にエラーが発生しました: {e}")

# ======================================
# メイン処理
# ======================================
def main():
    # セッション初期化（ここはシンプルでOK）
    if "user_email" not in st.session_state:
        st.session_state.user_email = None  # ログインしているかどうか
    if "page" not in st.session_state:
        st.session_state.page = "auth"      # 最初は認証画面
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "birth_year": None,
            "birth_month": None,
            "birth_day": None,
            "home_pref": None,
            "work_pref": None,
            "categories": [],
        }


    # ★ URL のクエリから mode を取得する
    try:
        # 新しい Streamlit の場合
        params = st.query_params
    except AttributeError:
        # 少し古いバージョンの場合
        params = st.experimental_get_query_params()

    mode = ""
    if params is not None:
        value = params.get("mode")  # dict でも QueryParams でも get は使える想定
        if isinstance(value, list):
            # experimental_get_query_params() の場合は ['reset'] みたいなリスト
            mode = value[0] if value else ""
        elif isinstance(value, str):
            # query_params の場合は 'reset'
            mode = value

    # ★ mode=reset のときはパスワード再設定ページへ
    if mode == "reset":
        st.session_state.page = "reset_password"

    # 画面遷移
    if st.session_state.page == "auth":
        auth_screen()
    elif st.session_state.page == "onboarding":
        onboarding_screen()
    elif st.session_state.page == "dashboard":
        render_dashboard()
    elif st.session_state.page == "reset_password":
        reset_password_screen()

# ======================================
# 実行
# ======================================     
if __name__ == "__main__":
    main()


