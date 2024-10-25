# ref. https://github.com/line/line-bot-sdk-python/blob/master/examples/fastapi-echo/main.py

import os
import sys

from fastapi import Request, FastAPI, HTTPException

from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import sqlite3
from datetime import datetime
import schedule
import time

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    raise ValueError("Specify LINE_CHANNEL_SECRET as environment variable.")
if channel_access_token is None:
    raise ValueError("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")

configuration = Configuration(access_token=channel_access_token)

app = FastAPI()
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)


# データベースの初期設定
def init_db():
    conn = sqlite3.connect("breast_cancer_bot.db")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            research_id TEXT,
            start_time TIMESTAMP,
            pre_survey_completed BOOLEAN,
            post_survey_completed BOOLEAN
        )
    """
    )
    conn.commit()
    conn.close()


# ユーザー情報をデータベースに保存
def save_user(user_id, research_id=None, start_time=None):
    conn = sqlite3.connect("breast_cancer_bot.db")
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users (user_id, research_id, start_time, pre_survey_completed, post_survey_completed) VALUES (?, ?, ?, ?, ?)",
        (user_id, research_id, start_time, False, False),
    )
    conn.commit()
    conn.close()


# ユーザーのアンケート状況を更新
def update_survey_status(user_id, pre_survey=None, post_survey=None):
    conn = sqlite3.connect("breast_cancer_bot.db")
    c = conn.cursor()
    if pre_survey is not None:
        c.execute(
            "UPDATE users SET pre_survey_completed = ? WHERE user_id = ?",
            (pre_survey, user_id),
        )
    if post_survey is not None:
        c.execute(
            "UPDATE users SET post_survey_completed = ? WHERE user_id = ?",
            (post_survey, user_id),
        )
    conn.commit()
    conn.close()


# 初回メッセージ送信時にタイムスタンプを記録
def record_start_time(user_id):
    conn = sqlite3.connect("breast_cancer_bot.db")
    c = conn.cursor()
    start_time = datetime.now()
    c.execute(
        "UPDATE users SET start_time = ? WHERE user_id = ?", (start_time, user_id)
    )
    conn.commit()
    conn.close()


# リマインドメッセージを送る関数
def send_reminder(user_id, message):
    line_bot_api.push_message(user_id, TextSendMessage(text=message))


# リマインドスケジュール設定
def schedule_reminders(user_id, start_time):
    # 3日後のリマインド
    schedule.every().day.at((start_time + timedelta(days=3)).strftime("%H:%M")).do(
        send_reminder,
        user_id,
        "3日後のリマインドメッセージです。調子はいかがですか？何か乳がんについて知りたいことがありましたら私までお気軽におたずねください。",
    )

    # 1週間後のリマインド
    schedule.every().day.at((start_time + timedelta(days=7)).strftime("%H:%M")).do(
        send_reminder,
        user_id,
        "1週間後のリマインドメッセージです。調子はいかがですか？何か乳がんについて知りたいことがありましたら私までお気軽におたずねください。",
    )

    # 2週間後のリマインド
    schedule.every().day.at((start_time + timedelta(days=14)).strftime("%H:%M")).do(
        send_reminder,
        user_id,
        "2週間後のリマインドメッセージです。調子はいかがですか？何か乳がんについて知りたいことがありましたら私までお気軽におたずねください。",
    )

    # 3週間後のリマインド
    schedule.every().day.at((start_time + timedelta(days=21)).strftime("%H:%M")).do(
        send_reminder,
        user_id,
        "3週間後のリマインドメッセージです。調子はいかがですか？何か乳がんについて知りたいことがありましたら私までお気軽におたずねください。",
    )


@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        # LINE以外からアクセスされた場合に弾かれるようになってる
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if not isinstance(event, MessageEvent):
            # メッセージイベントの場合通過
            continue
        if not isinstance(event.message, TextMessageContent):
            # テキストメッセージ（スタンプ等ではない）の場合通過
            continue

        text = event.message.text
        user_id = event.source.user_id
        # メッセージフローの処理
        if text == "初めまして":
            reply_text = "初めまして！私の名前はBRECOBOTです。お友達登録していただきありがとうございます。"
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply_text)
            )
            # 初回のやり取り時にタイムスタンプを記録
            record_start_time(user_id)
            # リマインドスケジュールの設定
            conn = sqlite3.connect("breast_cancer_bot.db")
            c = conn.cursor()
            c.execute("SELECT start_time FROM users WHERE user_id = ?", (user_id,))
            start_time = c.fetchone()[0]
            schedule_reminders(
                user_id, datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f")
            )

        elif text == "アンケートの回答は終了しましたか？":
            # クイックリプライボタンを表示
            quick_reply = QuickReply(
                items=[
                    QuickReplyButton(action=MessageAction(label="はい", text="はい")),
                    QuickReplyButton(
                        action=MessageAction(label="いいえ", text="いいえ")
                    ),
                ]
            )
            reply_text = "アンケートの回答は終了しましたか？"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text, quick_reply=quick_reply),
            )

        elif text == "はい":
            reply_text = "ご入力ありがとうございました。乳がんに関して知りたいこと（知りたかったこと）を入力してください。"
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply_text)
            )

        elif text == "いいえ":
            reply_text = "アンケートへの回答をお願い致します。下記のURLにアクセスしてください。\nhttp://example.com"
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply_text)
            )

        elif "乳がん" in text:
            reply_text = (
                f"乳がんに関する情報はこちらです。\nガイドライン http://example.com"
            )
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply_text)
            )

        elif text == "利用終了":
            reply_text = "本日で利用期間が終了です。ご利用ありがとうございました。最後に、下記のURLにアクセスし、アンケートにお答えください。\nhttp://example.com"
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply_text)
            )

        else:
            reply_text = "ご質問があればお答えしますので、何でもお尋ねください。"
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply_text)
            )

        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text)],
            )
        )

    return "OK"


# スケジューリングを別スレッドで実行
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)
