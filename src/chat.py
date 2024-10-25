import streamlit as st
import warnings
import logging
import csv
from datetime import datetime
import pandas as pd
import os
from fqa_service import find_answer, find_option

# Hide Streamlit deprecation warnings
logging.getLogger("streamlit").setLevel(logging.ERROR)

# Continue with your app logic
st.query_params.update({"step": 0})

# Suppress the specific deprecation warning for st.experimental_set_query_params
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=DeprecationWarning)
    st.query_params.update({"step": 0})


if "again_user_choice" not in st.session_state:
    st.session_state.again_user_choice = ""  # 初期値の設定

# CSVファイルのパス
CSV_FILE_PATH = "data/outputs/counselor_log.csv"


def add_message(user, role, message):
    st.session_state.messages.append({"role": role, "message": message})
    # write csv
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, "a") as f:
            writer = csv.writer(f)
            writer.writerow(["user", "role", "message", "timestamp"])
            writer.writerow([user, role, message, timestamp])
    with open(CSV_FILE_PATH, "a") as f:
        writer = csv.writer(f)
        writer.writerow([user, role, message, timestamp])


# メッセージを表示する関数
def display_messages():

    # LINE風のスタイルを適用
    st.markdown(
        """
        <style>
        .chatbox {
            max-width: 70%;
            margin: 10px;
            padding: 10px;
            border-radius: 10px;
            clear: both;
        }
        .chatbox-bot {
            background-color: #DCF8C6;
            text-align: left;
            float: left;
            border-radius: 10px 10px 10px 0;
        }
        .chatbox-user {
            background-color: #E6E6E6;
            text-align: right;
            float: right;
            border-radius: 10px 10px 0 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    for message in st.session_state.messages:
        if message["role"] == "bot":
            st.markdown(
                f'<div class="chatbox chatbox-bot">{message["message"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chatbox chatbox-user">{message["message"]}</div>',
                unsafe_allow_html=True,
            )


# CSVファイルからチャット履歴を読み込む関数
def load_chat_history(user):
    if os.path.exists(CSV_FILE_PATH):
        df = pd.read_csv(CSV_FILE_PATH)
        # ログイン中のユーザーのチャット履歴をフィルタリング
        df_user = df[df["user"] == user].reset_index(drop=True)

        if not df_user.empty:
            return df_user.to_dict(orient="records"), st.session_state.step
        else:
            st.session_state.step = 1
            return [], st.session_state.step
    else:
        st.session_state.step = 1
        return [], st.session_state.step


# チャットの履歴を表示する関数
def chat_screen(user):

    # セッションステートの初期化
    if "step" not in st.session_state:
        st.session_state.step = 0  # 初期ステップ
    if "messages" not in st.session_state:
        st.session_state.messages = []  # チャットのログを保持

    # メッセージを表示
    with st.container():
        display_messages()

    chat_history, st.session_state.step = load_chat_history(user)

    if st.session_state.step == 0:
        for chat in chat_history:
            if chat["role"] == "bot":
                st.session_state.messages.append(
                    {"role": "bot", "message": chat["message"]}
                )
            else:
                st.session_state.messages.append(
                    {"role": "user", "message": chat["message"]}
                )
        st.session_state.step = 2
        st.rerun()

    # ステップごとの処理
    if st.session_state.step == 1:
        # 初回の挨拶と同意取得
        if len(st.session_state.messages) == 0:
            add_message(
                user,
                "bot",
                "初めまして！私の名前はBRECOBOTです。乳がんに関する情報を提供するチャットボットです。",
            )
            add_message(
                user,
                "bot",
                "チャットを始める前に、この調査の目的について少し説明させてください。",
            )
            add_message(
                user,
                "bot",
                "このチャットボットは乳がんに関する根拠に基づいた情報を提供します。同意いただけますか？",
            )

        agreement = st.radio(
            "調査に同意いただけますか？", ["同意する", "同意しない"], key="agreement"
        )

        if st.button("送信", key="agreement_btn"):
            add_message(user, "user", agreement)
            if agreement == "同意しない":
                add_message(
                    user, "bot", "調査を終了します。ご協力ありがとうございました。"
                )
                st.stop()
            else:
                st.session_state.step = 2
                st.rerun()

    if st.session_state.step == 2:
        # 質問の入力
        user_input = st.text_input(
            "乳がんに関する質問を入力してください", key="user_input"
        )

        if st.button("送信", key="user_input_btn"):
            if user_input:
                add_message(user, "bot", "乳がんに関する質問を入力してください")
                add_message(user, "user", user_input)
                answer, option, again_user_choice, index = find_option(user_input)
                if option != "":
                    add_message(user, "bot", answer[0])
                    st.session_state.again_user_choice = again_user_choice
                    st.session_state.step = 2.5
                    st.rerun()
                else:
                    for ans in answer:
                        add_message(user, "bot", ans)
                    st.session_state.step = 3
                    st.rerun()

    if st.session_state.step == 2.5:
        user_choice = st.radio(
            "以下から聞きたいことを選択してください",
            [
                st.session_state.again_user_choice[0],
                st.session_state.again_user_choice[1],
            ],
            key="user_choice",
        )
        if st.button("選択送信", key="user_choice_btn"):
            add_message(user, "user", user_choice)
            again_answer, again_option, again2_user_choice, again_index = find_option(
                user_choice
            )
            for ans in again_answer:
                add_message(user, "bot", ans)
            st.session_state.step = 3
            st.rerun()

    if st.session_state.step == 3:
        # フィードバックを求める
        feedback = st.radio(
            "私の回答は適切でしたか？",
            [
                "チャットボットが掲示した回答は適切だった",
                "チャットボットが掲示した回答は適切だったが、もっと詳しい情報が欲しかった",
                "掲示した回答は適切ではなかった",
            ],
            key="feedback",
        )

        if st.button("フィードバック送信", key="feedback_btn"):
            add_message(user, "bot", "私の回答は適切でしたか？")
            add_message(user, "user", feedback)

            if feedback == "掲示した回答は適切ではなかった":
                add_message(
                    user,
                    "bot",
                    "申し訳ございません。適切な情報が提供できませんでした。改善いたします。",
                )
                st.session_state.step = 4
                st.rerun()
            else:
                st.session_state.step = 5
                st.rerun()

    if st.session_state.step == 4:
        # URLの入力を求める
        feedback_url = st.text_input(
            "可能な範囲で、適切な回答または該当するがん情報サービスおよび「患者さんのための乳がん診療ガイドライン2023年版」のURLを入力してください。",
            key="feedback_url",
        )
        if st.button("URL送信", key="feedback_url_btn"):
            if feedback_url:
                add_message(
                    user,
                    "bot",
                    "可能な範囲で、適切な回答または該当するがん情報サービスおよび「患者さんのための乳がん診療ガイドライン2023年版」のURLを入力してください。",
                )
                add_message(user, "user", feedback_url)

                st.session_state.step = 5
                st.rerun()

    if st.session_state.step == 5:
        # 質問入力に戻るかどうか
        return_choice = st.radio(
            "質問入力に戻りますか？", ["はい", "いいえ"], key="return_choice"
        )

        if st.button("選択送信", key="return_choice_btn"):
            add_message(user, "bot", "質問入力に戻りますか？")
            add_message(user, "user", return_choice)
            if return_choice == "はい":
                st.session_state.step = 2
                st.rerun()
            else:
                add_message(
                    user,
                    "bot",
                    "ご利用いただきありがとうございました。最終フィードバックにご協力ください。",
                )
                st.session_state.step = 6
                st.rerun()

    if st.session_state.step == 6:
        # 利用後のフィードバック
        usability_feedback = st.radio(
            "チャットボットを実際の相談の中で使えそうですか？",
            ["使えそう", "改良すれば使える", "相談に使うのは難しい"],
            key="usability_feedback",
        )

        if st.button("送信", key="usability_feedback_btn"):
            add_message(user, "bot", "チャットボットを実際の相談の中で使えそうですか？")
            add_message(user, "user", usability_feedback)

            st.session_state.step = 7
            st.rerun()

    if st.session_state.step == 7:
        # 理由の入力
        selection_feedback = st.text_area(
            "選択した理由を入力してください",
            key="final_feedback",
        )
        if st.button("送信1", key="final_feedback_btn"):
            add_message(user, "bot", "選択した理由を入力してください。")
            add_message(user, "user", selection_feedback)

            st.session_state.step = 8
            st.rerun()

    if st.session_state.step == 8:
        # 今後の利用意向
        future_use = st.radio(
            "今後、チャットボットを実際の相談の中で使いたいと思いますか？",
            ["使いたい", "どちらともいえない", "使いたくない"],
            key="future_use",
        )

        if st.button("送信2", key="future_use_btn"):
            add_message(
                user,
                "bot",
                "今後、チャットボットを実際の相談の中で使いたいと思いますか？",
            )
            add_message(user, "user", future_use)

            st.session_state.step = 9
            st.rerun()

    if st.session_state.step == 9:
        # 理由の入力
        selection_feedback = st.text_area(
            "選択した理由を入力してください",
            key="selection_feedback",
        )
        if st.button("送信3", key="selection_feedback_btn"):
            add_message(user, "bot", "選択した理由を入力してください。")
            add_message(user, "user", selection_feedback)

            st.session_state.step = 10
            st.rerun()

    if st.session_state.step == 10:
        # 最後のフィードバック
        final_feedback = st.text_area(
            "最後に私を使ってみてのご感想など、ご自由にお書きください。",
            key="final_feedback",
        )

        if st.button("送信4", key="final_feedback_btn"):
            add_message(
                user,
                "bot",
                "最後に私を使ってみてのご感想など、ご自由にお書きください。",
            )
            add_message(user, "user", final_feedback)

            if final_feedback:
                add_message(
                    user, "bot", "調査は以上です。ご意見ありがとうございました。"
                )
                st.session_state.step = 11
                st.rerun()


if __name__ == "__main__":
    chat_screen("user1")  # ユーザー名を指定してチャット画面を表示