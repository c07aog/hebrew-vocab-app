import random
import streamlit as st

from db import get_connection
from seed import seed_data


st.set_page_config(
    page_title="Hebrew Vocabulary",
    layout="centered"
)

seed_data()


def get_folders():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, description
        FROM folders
        ORDER BY id
    """)

    folders = cur.fetchall()
    conn.close()

    return folders


def get_words_in_folder(folder_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            words.id,
            words.hebrew,
            words.hebrew_pointed,
            words.hebrew_no_niqqud,
            words.transliteration,
            words.part_of_speech,
            words.english_meaning,
            words.example_hebrew,
            words.example_english
        FROM words
        JOIN folder_words
            ON words.id = folder_words.word_id
        WHERE folder_words.folder_id = ?
        ORDER BY words.id
    """, (folder_id,))

    words = cur.fetchall()
    conn.close()

    return words


def save_review(word_id, folder_id, result):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO reviews (
            word_id,
            folder_id,
            mode,
            result
        )
        VALUES (?, ?, ?, ?)
    """, (
        word_id,
        folder_id,
        "hebrew_to_english",
        result
    ))

    conn.commit()
    conn.close()


def hebrew_html(text, size=32):
    return f"""
    <div style="
        direction: rtl;
        text-align: right;
        font-size: {size}px;
        font-weight: bold;
        margin-top: 8px;
        margin-bottom: 8px;
    ">
        {text}
    </div>
    """


st.title("Hebrew-English Vocabulary")

folders = get_folders()

if not folders:
    st.error("フォルダがありません。先に python seed.py を実行してください。")
    st.stop()

folder_names = [folder["name"] for folder in folders]

selected_folder_name = st.selectbox(
    "単語フォルダを選択",
    folder_names
)

selected_folder = next(
    folder for folder in folders
    if folder["name"] == selected_folder_name
)

folder_id = selected_folder["id"]

words = get_words_in_folder(folder_id)

tab_list, tab_study = st.tabs([
    "単語一覧",
    "学習"
])


with tab_list:
    st.subheader(selected_folder["name"])

    if selected_folder["description"]:
        st.caption(selected_folder["description"])

    search = st.text_input("単語を検索")

    filtered_words = words

    if search:
        search_lower = search.lower()

        filtered_words = [
            word for word in words
            if search in word["hebrew"]
            or search in word["hebrew_no_niqqud"]
            or search_lower in word["english_meaning"].lower()
            or search_lower in word["transliteration"].lower()
        ]

    st.write(f"登録単語数: {len(filtered_words)}語")

    for word in filtered_words:
        st.markdown(
            hebrew_html(word["hebrew"], size=34),
            unsafe_allow_html=True
        )

        st.write(f"**読み:** {word['transliteration']}")
        st.write(f"**品詞:** {word['part_of_speech']}")
        st.write(f"**意味:** {word['english_meaning']}")

        if word["example_hebrew"]:
            st.write("**例文:**")

            st.markdown(
                hebrew_html(word["example_hebrew"], size=24),
                unsafe_allow_html=True
            )

        if word["example_english"]:
            st.write(word["example_english"])

        st.divider()


with tab_study:
    st.subheader("フラッシュカード学習")

    if not words:
        st.warning("このフォルダには単語がありません。")
        st.stop()

    if "study_words" not in st.session_state:
        st.session_state.study_words = random.sample(
            list(words),
            len(words)
        )

    if "current_word_index" not in st.session_state:
        st.session_state.current_word_index = 0

    study_words = st.session_state.study_words
    current_index = st.session_state.current_word_index
    current_word = study_words[current_index]

    st.caption(f"{current_index + 1} / {len(study_words)}")

    st.markdown(
        hebrew_html(current_word["hebrew"], size=52),
        unsafe_allow_html=True
    )

    show_answer = st.checkbox(
        "答えを見る",
        key=f"answer_{current_word['id']}"
    )

    if show_answer:
        st.write(f"**意味:** {current_word['english_meaning']}")
        st.write(f"**品詞:** {current_word['part_of_speech']}")
        st.write(f"**読み:** {current_word['transliteration']}")

        if current_word["example_hebrew"]:
            st.write("**例文:**")

            st.markdown(
                hebrew_html(
                    current_word["example_hebrew"],
                    size=24
                ),
                unsafe_allow_html=True
            )

        if current_word["example_english"]:
            st.write(current_word["example_english"])

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("不正解"):
                save_review(
                    current_word["id"],
                    folder_id,
                    "wrong"
                )

                st.session_state.current_word_index = (
                    current_index + 1
                ) % len(study_words)

                st.rerun()

        with col2:
            if st.button("正解"):
                save_review(
                    current_word["id"],
                    folder_id,
                    "correct"
                )

                st.session_state.current_word_index = (
                    current_index + 1
                ) % len(study_words)

                st.rerun()

        with col3:
            if st.button("シャッフル"):
                st.session_state.study_words = random.sample(
                    list(words),
                    len(words)
                )

                st.session_state.current_word_index = 0

                st.rerun()