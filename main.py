import streamlit as st
from datetime import date, datetime
from weather import weather_api, get_weather_icon
import os
from dotenv import load_dotenv
from news_api import news_get
from hour_calc import diff_hour

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
.info-card {
    background-color: #FFFFFF;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.05);
    margin-bottom: 20px;
}

.news-card {
    background-color: #FFFFFF;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.05);
    margin-bottom: 16px;
}

[data-testid="stAppViewContainer"] {
    background: #FFFFEF;  /* うすい黄色背景 */
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
        st.markdown("### OTASUKE")
    with cols[1]:
        st.markdown(
            """
            <div style="text-align:right;font-size:22px;">
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
            <div style="font-size:13px;color:#6b7280;">{step} / {total}</div>
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
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("#### 生年月日を入力してください")
    st.caption("星座占いや年齢に合わせた情報をお届けします")

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

    st.markdown("</div>", unsafe_allow_html=True)

# ======================================
# ステップ2：居住地域/勤務地
# ======================================
def step_home_region():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("#### お住まいの地域を教えてください")
    st.caption("地域の天気予報をお届けします")

    home = st.selectbox("都道府県", options=["選択してください"] + PREF_LIST)
    st.session_state.settings["home_pref"] = home if home != "選択してください" else None

    st.markdown("</div>", unsafe_allow_html=True)

# ======================================
# (ステップ3)：勤務地
# ======================================
def step_work_region():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("#### 勤務地を教えてください")
    st.caption("勤務先周辺の天気をお届けします")

    work = st.selectbox("都道府県", options=["選択してください"] + PREF_LIST)
    st.session_state.settings["work_pref"] = work if work != "選択してください" else None

    st.markdown("</div>", unsafe_allow_html=True)

# ======================================
# ステップ4：ニュースジャンル
# ======================================
def step_categories():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("#### 興味のあるニュースジャンルを選択")
    st.caption("複数選択可能です。選択したジャンルを優先的にお届けします")

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

    # 天気
    home_pref = st.session_state.settings.get("home_pref") or "東京" #選択された地域
    telop, max_temp, min_temp = weather_api(home_pref)
    icon = get_weather_icon(telop)

    st.markdown(
        f"""
        <div class="info-card weather-card">
            <div style="font-size:13px;">{icon} 今日の天気</div>
            <div style="font-size:14px;margin-top:4px;">{home_pref}</div>
            <div style="font-size:32px;font-weight:600;margin-top:4px;">
                {max_temp}° <span style="font-size:18px;">/ {min_temp}°</span>
            </div>
            <div style="font-size:13px;margin-top:4px;">{icon}{telop}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 星占い （記載は一例、APIで取得できる情報を記載する）
    st.markdown(
        """
        <div class="info-card fortune-card">
            <div style="font-size:13px;">✨ 今日の運勢（星座名）</div>
            <div style="font-size:14px;margin-top:4px;">
                星占いのメッセージをここに表示します。
            </div>
            <div style="font-size:13px;margin-top:4px;">
                総合運：★★★★★　ラッキーカラー：青
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 🔸 あなたへのおすすめニュース")

    select_categories = st.session_state.settings["categories"]
    articles = news_get(NEWS_API_KEY, select_categories)

    # ニュースカード（ダミーを2件ほど）
    
    for i in range(len(articles)):
        delta = diff_hour(articles[i]["publishedAt"])
        st.image(
            articles[i]["urlToImage"],
            caption="Web上の画像",  # キャプション（画像の説明）を追加できます
            use_container_width=True # 列幅に合わせて画像を自動調整します
        )
        st.markdown(
            f"""
            <div class="news-card">
                <div style="font-size:15px;font-weight:600;margin-bottom:4px;">
                    {articles[i]["title"]}
                </div>
                <div style="font-size:13px;color:#4b5563;margin-bottom:6px;">
                    {articles[i]["description"]}
                </div>
                <div style="font-size:11px;color:#4b5563;margin-bottom:6px;">
                    {delta}時間前
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button(
            label="記事詳細へ", # ボタンに表示するテキスト
            url=articles[i]["url"],           # リンク先のURL
            help="クリックすると記事の詳細ページに移動します" # ツールチップとして表示されるテキスト
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
                    # ここでダッシュボードに遷移
                    st.session_state.page = "dashboard"
                    st.rerun()

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


