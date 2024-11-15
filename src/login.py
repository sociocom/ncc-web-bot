import streamlit as st
from chat import chat_screen  # 別ファイルのチャット機能をインポート

# 仮のユーザー名とパスワード
USER_DATA = {
    "user1": "password1",
    "user2": "password2",
    "user3": "password3",
    "user4": "password4",
    "user5": "password5",
}

# ログイン状態の初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None


# ログイン機能
def login(username, password):
    if username in USER_DATA and USER_DATA[username] == password:
        st.session_state.logged_in = True
        st.session_state.current_user = username
        return True
    else:
        return False


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
    st.header("ログイン")
    username = st.text_input("ユーザー名")
    password = st.text_input("パスワード", type="password")

    if st.button("ログイン"):
        if login(username, password):
            st.success("ログインに成功しました。")
            st.rerun()  # ログイン成功時にページを再描画してチャット画面へ遷移
        else:
            st.error("ユーザー名またはパスワードが間違っています。")


# メイン処理
if not st.session_state.logged_in:
    login_screen()
else:
    chat_screen(st.session_state.current_user)  # ログイン後にチャット画面を表示
