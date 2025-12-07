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

        # Supabase に insert
        res = supabase.table("users").insert(data).execute()
        return res


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

    # 追加
    # 開発中は True、本番テストは False にする（API100回制限ありのため）
    USE_TEST_DATA = True
    if USE_TEST_DATA:
        # ----------------------------
        # test_news.txt を読み込む
        # ----------------------------
        with open("test_news.txt", "r", encoding="utf-8") as f:
            news_data = f.read()
            st.info("📝 開発モード：test_news.txt を使っています（API未使用）")
    else:
        # ----------------------------
        # 本番 API を呼び出す
        # ----------------------------
        news_data = call_news_api(NEWS_API_KEY)
        st.success("本番モード：APIを使用しています")

    # 読み込んだニュースを表示する処理（あなたの UI に合わせて）
    st.write(news_data)

    # 天気
    home_pref = st.session_state.settings.get("home_pref") or "東京"
    # st.write("DEBUG - home_pref:", home_pref)

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
    birth_month = st.session_state.settings["birth_month"]
    birth_day = st.session_state.settings["birth_day"]

    horoscope_result = get_horoscope(birth_month, birth_day)
    st.markdown(
        f"""
        <div class="info-card fortune-card">
            <div style="font-size:13px;">✨ 今日の運勢（{horoscope_result["sign"]}）</div>
            <div style="font-size:14px;margin-top:4px;">
                {horoscope_result["sign"]}：{horoscope_result["rank"]}位
            </div>
            <div style="font-size:14px;margin-top:4px;">
                {horoscope_result["sign"]}のあなた。{horoscope_result["content"]}
            </div>
            <div style="font-size:13px;margin-top:4px;">
                <ul>
                    <li>ラッキーカラー：{horoscope_result["color"]}</li>
                    <li>ラッキーアイテム：{horoscope_result["item"]}</li>
                </ul>
            </div>
            <div style="font-size:13px;margin-top:4px;">
                <ul>
                    <li>仕事：{horoscope_result["job"]}</li>
                    <li>お金：{horoscope_result["money"]}</li>
                    <li>恋愛：{horoscope_result["love"]}</li>
                    <li>総合：{horoscope_result["total"]}</li>
                </ul>
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
                st.write("DEBUG: 保存後 page =", st.session_state.page)
                st.rerun()
    
#=====================================
#認証用の関数
#======================================
def sign_up(email,password):
    try:
        user = supabase.auth.sign_up({"email": email, "password": password})
        if user and user.user:
            # ← ここでユーザーIDをセッションに保存
            st.session_state["auth_user_id"] = user.user.id
        return user
    except Exception as e:
        st.error(f"サインアップ中にエラーが発生しました: {e}")
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
        sign-out()
        st.session_state.user_email = None
        st.session_state.page = "auth"
        st.rerun()
    
#======================================
#  認証画面
#======================================
def auth_screen():
    st.title("OTASUKEへようこそ！")
    option = st.selectbox("選択してください", ["ログイン", "サインアップ"])
    email = st.text_input("メールアドレス")
    password = st.text_input("パスワード", type="password")

    #======================================    
    #ログイン処理
    #======================================
    if option == "ログイン" and st.button("ログイン"):
        user = sign_in(email,password)
        if user and user.user:
            st.session_state.user_email = user.user.email
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


    # 画面遷移
    if st.session_state.page == "auth":
        auth_screen()
    elif st.session_state.page == "onboarding":
        onboarding_screen()
    elif st.session_state.page == "dashboard":
        render_dashboard()

# ======================================
# 実行
# ======================================     
if __name__ == "__main__":
    main()


