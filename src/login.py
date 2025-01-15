import streamlit as st
import json
import os
import hashlib
from chat import chat_screen  # 別ファイルのチャット機能をインポート

# ユーザーデータを格納するファイル
USER_DATA_FILE = "data/outputs/user_data.json"

# ユーザーデータをロードまたは初期化
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "w") as file:
        json.dump({}, file)  # 初期化

with open(USER_DATA_FILE, "r") as file:
    USER_DATA = json.load(file)

# ログイン状態の初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

if "register_mode" not in st.session_state:
    st.session_state.register_mode = False

if "reset_mode" not in st.session_state:
    st.session_state.reset_mode = False


# パスワードをハッシュ化
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ユーザーを登録
def register_user(username, password):
    if username in USER_DATA:
        st.warning("既に登録されているユーザー名です。")
    else:
        hashed_password = hash_password(password)
        USER_DATA[username] = hashed_password
        with open(USER_DATA_FILE, "w") as file:
            json.dump(USER_DATA, file)
        st.success("新しいユーザーを登録しました。ログインしてください。")
        st.session_state.register_mode = False


# ログイン機能
def login(username, password):
    hashed_password = hash_password(password)
    if username in USER_DATA and USER_DATA[username] == hashed_password:
        st.session_state.logged_in = True
        st.session_state.current_user = username
        return True
    else:
        return False


# パスワードリセット機能
def reset_password(username, new_password):
    if username in USER_DATA:
        hashed_password = hash_password(new_password)
        USER_DATA[username] = hashed_password
        with open(USER_DATA_FILE, "w") as file:
            json.dump(USER_DATA, file)
        st.success("パスワードがリセットされました。ログインしてください。")
        st.session_state.reset_mode = False
    else:
        st.error("そのユーザー名は登録されていません。")


# ログイン画面
def login_screen():
    st.set_page_config(
        page_title="BRECOBOT相談員用ログイン",
        page_icon=":female-doctor:",
        menu_items={
            "Get Help": "https://www.extremelycoolapp.com/help",
            "Report a bug": "https://www.extremelycoolapp.com/bug",
            "About": """
            # BRECOBOT相談員用チャットボット
            国立がん研究センターがん情報サービスの相談員用チャットボットです。""",
        },
    )
    st.image("./data/ganjoho_logo.png")
    st.title("BRECOBOT相談員用chatbot")
    st.header("ログイン画面")
    st.write(
        "調査に同意いただける方は、新規登録からユーザー名、パスワードの設定をお願いします。"
    )
    if st.button("新規登録の場合はこちら"):
        st.session_state.register_mode = True

    username = st.text_input("ユーザー名")
    password = st.text_input("パスワード", type="password")

    if st.button("ログイン"):
        if login(username, password):
            st.success("ログインに成功しました。")
            st.rerun()  # ログイン成功時にページを再描画してチャット画面へ遷移
        else:
            st.error("ユーザー名またはパスワードが間違っています。")

    if st.button("パスワードをお忘れの場合はこちら"):
        st.session_state.reset_mode = True


# 登録画面
def register_screen():
    st.set_page_config(
        page_title="BRECOBOT新規登録",
        page_icon=":female-doctor:",
    )
    st.image("./data/ganjoho_logo.png")
    st.title("BRECOBOT相談員用chatbot")
    st.header("新規登録")
    st.write("このたびは研究へのご協力をありがとうございます。")
    st.write(
        "研究内容の詳細についてはメールに添付した通りです。研究に協力していただける方のみ、新規登録にお進みいただき、ユーザー名、パスワードの設定をお願いします。"
    )
    # 赤字で注意書きを表示
    st.markdown(
        ":gray-background[ユーザー名：任意の名前（ひらがな、カタカナ、英数字）\u3000[例] いちごちゃん、happy777  など]"
    )
    st.markdown(":gray-background[パスワード：任意のパスワード（半角英数字）]")

    username = st.text_input("新しいユーザー名")
    password = st.text_input("新しいパスワード", type="password")

    if st.button("登録"):
        if username and password:
            register_user(username, password)
        else:
            st.warning("ユーザー名とパスワードを入力してください。")

    if st.button("ログイン画面に戻る"):
        st.session_state.register_mode = False


# パスワードリセット画面
def reset_screen():
    st.set_page_config(
        page_title="BRECOBOTパスワードリセット",
        page_icon=":female-doctor:",
    )
    st.image("./data/ganjoho_logo.png")
    st.title("BRECOBOT相談員用chatbot")
    st.header("パスワードリセット画面")

    st.markdown(
        ":gray-background[ユーザー名：任意の名前（ひらがな、カタカナ、英数字）\u3000[例] いちごちゃん、happy777  など]"
    )
    st.markdown(":gray-background[パスワード：任意のパスワード（半角英数字）]")

    username = st.text_input("登録したユーザー名")
    new_password = st.text_input("新しいパスワード", type="password")

    if st.button("パスワードをリセット"):
        if username and new_password:
            reset_password(username, new_password)
        else:
            st.warning("ユーザー名と新しいパスワードを入力してください。")

    if st.button("ログイン画面に戻る"):
        st.session_state.reset_mode = False


# メイン処理
if not st.session_state.logged_in:
    if st.session_state.register_mode:
        register_screen()
    elif st.session_state.reset_mode:
        reset_screen()
    else:
        login_screen()
else:
    chat_screen(st.session_state.current_user)  # ログイン後にチャット画面を表示
