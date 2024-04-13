"""
参考にしたプログラムは以下
https://github.com/line/line-bot-sdk-python/tree/master/examples/fastapi-echo
"""

import os
import csv
import sys
from dotenv import load_dotenv
import random
import pandas as pd
from fastapi import Request, FastAPI, HTTPException
from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from find_answer import find_answer, find_option

load_dotenv()

channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

configuration = Configuration(access_token=channel_access_token)

app = FastAPI()
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)


def save_chat(
    user_message,
    response,
    again_user_choice,
    again_response,
    version,
    file_name="./data/outputs/line_chat_history.csv",
):
    # CSVファイルが存在しない場合は、ヘッダーを含む新しいファイルを作成
    if not os.path.exists(file_name):
        with open(file_name, "w", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "user_message",
                    "response",
                    "again_user_choice",
                    "again_response",
                    "version",
                ]
            )

    # CSVファイルにデータを追記
    with open(file_name, "a", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [user_message, response, again_user_choice, again_response, version]
        )


last_chat = {
    "user_message": "",
    "response": "",
    "again_user_choice": "",
    "again_response": "",
}


@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessageContent):
            continue
        answer, option, again_user_choice = find_option(event.message.text)

        last_chat["user_message"] = event.message.text
        last_chat["response"] = "\t".join(answer)

        if option != "":
            print("聞き返し")
            print("option:", option)
            quick_reply = QuickReply(
                items=[
                    QuickReplyItem(
                        action=MessageAction(label=option[0], text=again_user_choice[0])
                    ),
                    QuickReplyItem(
                        action=MessageAction(label=option[1], text=again_user_choice[1])
                    ),
                ]
            )
            await line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=answer[0], quick_reply=quick_reply)],
                )
            )
            last_chat["again_user_choice"] = event.message.text
            last_chat["again_response"] = "\t".join(answer)
        else:
            await line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=ans) for ans in answer],
                )
            )
            if last_chat["again_user_choice"]:
                last_chat["user_message"] = last_chat["again_user_choice"]
                last_chat["response"] = last_chat["again_response"]
                last_chat["again_user_choice"] = event.message.text
                last_chat["again_response"] = "\t".join(answer)
            save_chat(
                last_chat["user_message"],
                last_chat["response"],
                last_chat["again_user_choice"],
                last_chat["again_response"],
                version="sample",
            )

    return "OK"
