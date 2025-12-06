import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

def news_get(api_key, categories):
    # API_KEY = "YOUR_API_KEY"  # 取得したAPIキーを設定
    BASE_URL = "https://newsapi.org/v2/everything"  # NewsAPIのエンドポイント

    now = datetime.now()
    two_days_ago = now - timedelta(days=2)
    from_time = two_days_ago.strftime("%Y-%m-%dT%H:%M:%S")
    to_time = now.strftime("%Y-%m-%dT%H:%M:%S")

    key_word = ""
    for id, category in enumerate(categories):
        if id == len(categories) - 1:
            key_word = key_word + category
        else:
            key_word = key_word + category + " OR "
                
    # パラメータ設定
    params = {
        "q": key_word,
        "language": "jp",  #言語
        "from": from_time,       # 開始日時
        "to": to_time,         # 終了日時
        "sortBy": "popularity",               # ソート順
        "pageSize": 5,                       # 取得件数
        "apiKey": api_key
    }

    # APIリクエスト
    response = requests.get(BASE_URL, params=params)

    # レスポンスを出力
    if response.status_code == 200:
        articles = response.json().get("articles", [])
        return articles
        # for i, article in enumerate(articles):
        #     print(f"{i + 1}. {article['title']} - {article['source']['name']}")
    else:
        "Error"