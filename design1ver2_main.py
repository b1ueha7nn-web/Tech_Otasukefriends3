import streamlit as st
from datetime import date, datetime
from weather import weather_api, get_weather_icon
import os
from dotenv import load_dotenv
from news_api import news_get
from hour_calc import diff_hour
from horoscope import get_horoscope
from supabase import create_client, Client
from dotenv import load_dotenv

#categoriesを文字列にするためにjason必要
import json

#.envを読み込ませる
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabaseクライアントの初期化（キーがない場合はNone）
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase接続エラー: {e}")

def save_settings_to_supabase():
    """st.session_state.settings の内容を users テーブルに 1 行保存する"""

    if not supabase:
        # Supabaseが利用できない場合はスキップ（デモモード）
        return None

    s = st.session_state.settings

    # list → JSON文字列に変換（["テクノロジー", "経済"] など）
    categories_json = json.dumps(s.get("categories", []), ensure_ascii=False)

    data = {
        "birth_year":  s.get("birth_year"),
        "birth_month": s.get("birth_month"),
        "birth_day":   s.get("birth_day"),
        "home_pref":   s.get("home_pref"),
        "work_pref":   s.get("work_pref"),
        "categories":  categories_json,
    }

    try:
        # Supabase に insert
        res = supabase.table("users").insert(data).execute()
        return res
    except Exception as e:
        st.warning(f"データ保存をスキップしました: {e}")
        return None



# ======================================
# ページの基本設定
# ======================================
st.set_page_config(
    page_title="OTASUKE", #名前は適当です。その日の要点を詰めてるイメージの名前にしてみました
    page_icon="☀️",
    layout="centered",
)

#======================================
#CSS(UIデザイン - 春の花畑スタイル)
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
if "page" not in st.session_state:
    st.session_state.page = "onboarding"  # onboarding or dashboard

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
    render_header()
    load_dotenv()
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    today = datetime.today()
    
    st.markdown(
        f"**{today.strftime('%m月%d日（%a）')}**",
    )

    st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)

    # デモモードの表示
    st.markdown('<div style="font-size:11px; color:#9ca3af; text-align:center; margin-bottom:12px;">🎨 デモモード（サンプルデータ表示中）</div>', unsafe_allow_html=True)

    # 天気（ダミーデータ）
    home_pref = st.session_state.settings.get("home_pref") or "東京"
    
    # APIキーがあれば本物のデータを取得、なければダミー
    try:
        if os.getenv("OPENWEATHER_API_KEY"):
            telop, max_temp, min_temp = weather_api(home_pref)
        else:
            telop, max_temp, min_temp = "晴れ", 22, 15
    except:
        telop, max_temp, min_temp = "晴れ", 22, 15
    
    icon = get_weather_icon(telop)

    st.markdown(
        f"""
        <div class="info-card weather-card">
            <div style="font-size:14px; color:#FF8C00; font-weight:600; margin-bottom:8px;">☀️ 今日の天気</div>
            <div style="display:flex; align-items:center; gap:20px; margin-top:8px;">
                <div style="font-size:72px; line-height:1;">{icon}</div>
                <div>
                    <div style="font-size:16px; color:#666; margin-bottom:4px;">【{home_pref}】</div>
                    <div style="font-size:48px; font-weight:700; color:#FF6347; line-height:1;">{max_temp}°</div>
                    <div style="font-size:16px; color:#888; margin-top:4px;">最低気温 {min_temp}°</div>
                    <div style="font-size:15px; color:#666; margin-top:8px;">{telop}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 星占い （記載は一例、APIで取得できる情報を記載する）
    birth_month = st.session_state.settings.get("birth_month") or 1
    birth_day = st.session_state.settings.get("birth_day") or 1

    try:
        horoscope_result = get_horoscope(birth_month, birth_day)
    except:
        # ダミーデータ
        horoscope_result = {
            "sign": "おひつじ座",
            "rank": 1,
            "content": "今日は素敵な一日になりそうです！新しいチャレンジを楽しんでください。",
            "color": "ピンク",
            "item": "ハンカチ",
            "job": "★★★★☆",
            "money": "★★★☆☆",
            "love": "★★★★★",
            "total": "★★★★☆"
        }
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
    
    # ニュース取得（APIキーがなければダミーデータ）
    try:
        if NEWS_API_KEY:
            articles = news_get(NEWS_API_KEY, select_categories)
        else:
            # ダミーニュース
            articles = [
                {
                    "title": "新しいテクノロジーが日常生活を変える",
                    "description": "最新のAI技術により、私たちの生活がより便利になっています。",
                    "url": "https://example.com/news1",
                    "urlToImage": "",
                    "publishedAt": "2025-12-09T09:00:00Z"
                },
                {
                    "title": "健康的なライフスタイルのための5つのヒント",
                    "description": "毎日の小さな習慣が大きな変化をもたらします。",
                    "url": "https://example.com/news2",
                    "urlToImage": "",
                    "publishedAt": "2025-12-09T08:00:00Z"
                }
            ]
    except:
        articles = [
            {
                "title": "サンプルニュース1",
                "description": "これはデモ用のサンプルニュースです。",
                "url": "https://example.com",
                "urlToImage": "",
                "publishedAt": "2025-12-09T09:00:00Z"
            }
        ]
    
    for i in range(len(articles)):
        try:
            delta = diff_hour(articles[i]["publishedAt"])
        except:
            delta = 2  # デフォルト値
        img_url = articles[i].get("urlToImage", "")
        st.markdown(
            f"""
            <div class="news-card">
                {f'<img src="{img_url}" alt="ニュース画像">' if img_url else ''}
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
# メイン処理
# ======================================

TOTAL_STEPS = 4

def main():
    page = st.session_state.page
    step = st.session_state.step

    # -----------------------
    # 設定画面
    # -----------------------
    if page == "onboarding":
        render_header()
        render_progress(step, total=TOTAL_STEPS)

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
        col_back, col_center, col_next = st.columns([1, 1, 1])

        with col_back:
            if st.button("＜ 戻る", disabled=step == 1, use_container_width=False):
                if step > 1:
                    st.session_state.step -= 1
                    st.rerun()

        with col_next:
            if st.button("次へ ＞" if step < TOTAL_STEPS else "完了", use_container_width=False, key=f"next_btn_{step}"):
                if step < TOTAL_STEPS:
                    st.session_state.step += 1
                    st.rerun()
                else:
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

    # -----------------------
    # ダッシュボード画面
    # -----------------------
    elif page == "dashboard":
        render_dashboard()

        # 必要なら「設定をやり直す」ボタンも追加
        if st.button("設定を変更する"):
            st.session_state.page = "onboarding"
            st.session_state.step = 1
            st.rerun()


if __name__ == "__main__":
    main()
