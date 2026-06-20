import random
import unicodedata

import streamlit as st

from db import get_connection
from seed import seed_data


st.set_page_config(
    page_title="Hebrew Vocabulary",
    layout="centered"
)

seed_data()


PART_OF_SPEECH_OPTIONS = [
    "",
    "名詞",
    "動詞",
    "形容詞",
    "副詞",
    "前置詞",
    "接続詞",
    "代名詞",
    "数詞",
    "挨拶",
    "その他",
]


WORD_COLUMNS = [
    "id",
    "hebrew",
    "hebrew_pointed",
    "hebrew_no_niqqud",
    "transliteration",
    "part_of_speech",
    "english_meaning",
    "japanese_meaning",
    "example_hebrew",
    "example_english",
    "notes",
    "created_at",
    "updated_at",
]
WORD_FIELDS = ", ".join(WORD_COLUMNS)
QUALIFIED_WORD_FIELDS = ", ".join(
    f"words.{column}" for column in WORD_COLUMNS
)


def normalize_optional(value):
    if value is None:
        return None

    stripped_value = value.strip()
    return stripped_value or None


def strip_niqqud(text):
    return "".join(
        char for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )


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

    cur.execute(f"""
        SELECT
            {QUALIFIED_WORD_FIELDS}
        FROM words
        JOIN folder_words
            ON words.id = folder_words.word_id
        WHERE folder_words.folder_id = %s
        ORDER BY words.id
    """, (folder_id,))

    words = cur.fetchall()
    conn.close()

    return words


def get_word(word_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT {WORD_FIELDS}
        FROM words
        WHERE id = %s
    """, (word_id,))

    word = cur.fetchone()
    conn.close()

    return word


def get_part_of_speech_values(words):
    values = sorted({
        word["part_of_speech"]
        for word in words
        if word["part_of_speech"]
    })
    return ["すべて"] + values


def create_word(folder_id, form_data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO words (
            hebrew,
            hebrew_pointed,
            hebrew_no_niqqud,
            transliteration,
            part_of_speech,
            english_meaning,
            japanese_meaning,
            example_hebrew,
            example_english,
            notes,
            updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """,
        (
            form_data["hebrew"],
            normalize_optional(form_data["hebrew_pointed"]),
            strip_niqqud(form_data["hebrew"]),
            normalize_optional(form_data["transliteration"]),
            normalize_optional(form_data["part_of_speech"]),
            form_data["english_meaning"],
            normalize_optional(form_data["japanese_meaning"]),
            normalize_optional(form_data["example_hebrew"]),
            normalize_optional(form_data["example_english"]),
            normalize_optional(form_data["notes"]),
        )
    )

    cur.execute(
        """
        SELECT id
        FROM words
        WHERE hebrew = %s
          AND english_meaning = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (form_data["hebrew"], form_data["english_meaning"])
    )
    word_id = cur.fetchone()["id"]

    cur.execute(
        """
        INSERT INTO folder_words (folder_id, word_id)
        VALUES (%s, %s)
        ON CONFLICT(folder_id, word_id) DO NOTHING
        """,
        (folder_id, word_id)
    )

    conn.commit()
    conn.close()
    return word_id


def update_word(word_id, form_data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE words
        SET hebrew = %s,
            hebrew_pointed = %s,
            hebrew_no_niqqud = %s,
            transliteration = %s,
            part_of_speech = %s,
            english_meaning = %s,
            japanese_meaning = %s,
            example_hebrew = %s,
            example_english = %s,
            notes = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (
            form_data["hebrew"],
            normalize_optional(form_data["hebrew_pointed"]),
            strip_niqqud(form_data["hebrew"]),
            normalize_optional(form_data["transliteration"]),
            normalize_optional(form_data["part_of_speech"]),
            form_data["english_meaning"],
            normalize_optional(form_data["japanese_meaning"]),
            normalize_optional(form_data["example_hebrew"]),
            normalize_optional(form_data["example_english"]),
            normalize_optional(form_data["notes"]),
            word_id,
        )
    )

    conn.commit()
    conn.close()


def delete_word(word_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM reviews WHERE word_id = %s", (word_id,))
    cur.execute("DELETE FROM folder_words WHERE word_id = %s", (word_id,))
    cur.execute("DELETE FROM words WHERE id = %s", (word_id,))

    conn.commit()
    conn.close()


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
        VALUES (%s, %s, %s, %s)
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
    <div dir="rtl" style="
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


def set_page(page, word_id=None):
    st.session_state.word_page = page
    st.session_state.selected_word_id = word_id


def render_word_form(mode, folder_id, word=None):
    is_edit = mode == "edit"
    title = "単語を編集" if is_edit else "新しい単語を登録"
    submit_label = "更新する" if is_edit else "登録する"

    st.subheader(title)
    st.caption("必須項目は「ヘブライ語の単語」と「英語の意味」です。")

    with st.form(f"word_form_{mode}"):
        hebrew = st.text_input(
            "ヘブライ語の単語（必須）",
            value=word["hebrew"] if word else "",
            help="右から左に入力されます。",
            placeholder="例: שָׁלוֹם"
        )
        st.markdown(
            "<style>input[aria-label='ヘブライ語の単語（必須）'], "
            "textarea[aria-label='例文（ヘブライ語）'] "
            "{direction: rtl; text-align: right;}</style>",
            unsafe_allow_html=True,
        )
        hebrew_pointed = st.text_input(
            "母音記号付き表記（任意）",
            value=word["hebrew_pointed"] if word and word["hebrew_pointed"] else "",
            placeholder="例: שָׁלוֹם"
        )
        transliteration = st.text_input(
            "読み方・発音表記（任意）",
            value=word["transliteration"] if word and word["transliteration"] else "",
            placeholder="例: shalom"
        )
        english_meaning = st.text_input(
            "英語の意味（必須）",
            value=word["english_meaning"] if word else "",
            placeholder="例: peace / hello"
        )
        japanese_meaning = st.text_input(
            "日本語の意味（任意）",
            value=word["japanese_meaning"] if word and word["japanese_meaning"] else "",
            placeholder="例: 平和、こんにちは"
        )
        current_pos = word["part_of_speech"] if word and word["part_of_speech"] else ""
        part_of_speech_options = list(PART_OF_SPEECH_OPTIONS)
        if current_pos in part_of_speech_options:
            pos_index = part_of_speech_options.index(current_pos)
        else:
            part_of_speech_options.append(current_pos)
            pos_index = len(part_of_speech_options) - 1
        part_of_speech = st.selectbox(
            "品詞（任意）",
            part_of_speech_options,
            index=pos_index,
            format_func=lambda value: "選択しない" if value == "" else value,
        )
        example_hebrew = st.text_area(
            "例文（ヘブライ語）",
            value=word["example_hebrew"] if word and word["example_hebrew"] else "",
            placeholder="例: שָׁלוֹם עֲלֵיכֶם"
        )
        example_english = st.text_area(
            "例文の英訳または日本語訳（任意）",
            value=word["example_english"] if word and word["example_english"] else "",
            placeholder="例: Peace be upon you."
        )
        notes = st.text_area(
            "メモ（任意）",
            value=word["notes"] if word and word["notes"] else "",
            placeholder="覚え方や語根など"
        )

        col_submit, col_back = st.columns([1, 1])
        submitted = col_submit.form_submit_button(submit_label, type="primary")
        back = col_back.form_submit_button("キャンセル")

    if back:
        set_page("detail" if is_edit else "list", word["id"] if is_edit else None)
        st.rerun()

    if submitted:
        errors = []
        if not hebrew.strip():
            errors.append("ヘブライ語の単語を入力してください。")
        if not english_meaning.strip():
            errors.append("英語の意味を入力してください。")

        if errors:
            for error in errors:
                st.error(error)
            return

        form_data = {
            "hebrew": hebrew.strip(),
            "hebrew_pointed": hebrew_pointed,
            "transliteration": transliteration,
            "part_of_speech": part_of_speech,
            "english_meaning": english_meaning.strip(),
            "japanese_meaning": japanese_meaning,
            "example_hebrew": example_hebrew,
            "example_english": example_english,
            "notes": notes,
        }

        try:
            with st.spinner("保存しています..."):
                if is_edit:
                    update_word(word["id"], form_data)
                    word_id = word["id"]
                    st.success("単語を更新しました。")
                else:
                    word_id = create_word(folder_id, form_data)
                    st.success("単語を登録しました。")
            set_page("detail", word_id)
            st.rerun()
        except Exception as exc:
            st.error(f"保存に失敗しました: {exc}")


def render_word_detail(word):
    if not word:
        st.error("単語が見つかりませんでした。")
        if st.button("一覧へ戻る"):
            set_page("list")
            st.rerun()
        return

    st.button("← 一覧へ戻る", on_click=set_page, args=("list",))
    st.markdown(hebrew_html(word["hebrew"], size=56), unsafe_allow_html=True)

    if word["japanese_meaning"]:
        st.caption(word["japanese_meaning"])
    st.markdown(f"### {word['english_meaning']}")

    detail_items = [
        ("読み方・発音", word["transliteration"]),
        ("品詞", word["part_of_speech"]),
        ("母音記号付き表記", word["hebrew_pointed"]),
        ("メモ", word["notes"]),
        ("作成日時", word["created_at"]),
        ("更新日時", word["updated_at"]),
    ]

    for label, value in detail_items:
        if value:
            st.write(f"**{label}:** {value}")

    if word["example_hebrew"] or word["example_english"]:
        st.divider()
        st.write("**例文**")
        if word["example_hebrew"]:
            st.markdown(
                hebrew_html(word["example_hebrew"], size=28),
                unsafe_allow_html=True,
            )
        if word["example_english"]:
            st.write(word["example_english"])

    st.divider()
    col_edit, col_delete = st.columns([1, 1])
    if col_edit.button("編集する", type="primary"):
        set_page("edit", word["id"])
        st.rerun()
    if col_delete.button("削除へ", type="secondary"):
        set_page("delete", word["id"])
        st.rerun()


def render_delete_confirmation(word):
    if not word:
        st.error("単語が見つかりませんでした。")
        if st.button("一覧へ戻る"):
            set_page("list")
            st.rerun()
        return

    st.warning("この単語を削除します。元に戻すことはできません。")
    st.markdown(hebrew_html(word["hebrew"], size=42), unsafe_allow_html=True)
    st.write(f"**英語の意味:** {word['english_meaning']}")

    col_cancel, col_delete = st.columns([1, 1])
    if col_cancel.button("キャンセル"):
        set_page("detail", word["id"])
        st.rerun()
    if col_delete.button("削除する", type="secondary"):
        try:
            with st.spinner("削除しています..."):
                delete_word(word["id"])
            st.success("単語を削除しました。")
            set_page("list")
            st.rerun()
        except Exception as exc:
            st.error(f"削除に失敗しました: {exc}")


def render_word_list(words):
    st.subheader("単語一覧")
    st.button("＋ 新規単語を登録", type="primary", on_click=set_page, args=("new",))

    if not words:
        st.info("まだ単語が登録されていません。最初の単語を登録しましょう。")
        return

    search = st.text_input("単語を検索", placeholder="ヘブライ語、読み方、英語、日本語、品詞で検索")
    pos_filter = st.selectbox("品詞で絞り込み", get_part_of_speech_values(words))

    filtered_words = words
    if search:
        search_lower = search.lower()
        filtered_words = [
            word for word in filtered_words
            if search in word["hebrew"]
            or search in (word["hebrew_no_niqqud"] or "")
            or search_lower in (word["transliteration"] or "").lower()
            or search_lower in word["english_meaning"].lower()
            or search_lower in (word["japanese_meaning"] or "").lower()
            or search_lower in (word["part_of_speech"] or "").lower()
        ]

    if pos_filter != "すべて":
        filtered_words = [
            word for word in filtered_words
            if word["part_of_speech"] == pos_filter
        ]

    st.write(f"表示単語数: {len(filtered_words)}語 / 登録単語数: {len(words)}語")

    if not filtered_words:
        st.info("条件に一致する単語はありません。検索条件を変更してください。")
        return

    for word in filtered_words:
        with st.container(border=True):
            col_hebrew, col_meaning = st.columns([1, 2])
            with col_hebrew:
                st.markdown(hebrew_html(word["hebrew"], size=34), unsafe_allow_html=True)
                if word["transliteration"]:
                    st.caption(word["transliteration"])
            with col_meaning:
                st.write(f"**英語:** {word['english_meaning']}")
                if word["japanese_meaning"]:
                    st.write(f"**日本語:** {word['japanese_meaning']}")
                if word["part_of_speech"]:
                    st.write(f"**品詞:** {word['part_of_speech']}")
                if st.button("詳細を見る", key=f"detail_{word['id']}"):
                    set_page("detail", word["id"])
                    st.rerun()


st.title("Hebrew-English Vocabulary")

folders = get_folders()

if not folders:
    st.error("フォルダがありません。先に python seed.py を実行してください。")
    st.stop()

folder_names = [folder["name"] for folder in folders]
selected_folder_name = st.selectbox("単語フォルダを選択", folder_names)
selected_folder = next(folder for folder in folders if folder["name"] == selected_folder_name)
folder_id = selected_folder["id"]
words = get_words_in_folder(folder_id)

if "word_page" not in st.session_state:
    st.session_state.word_page = "list"
if "selected_word_id" not in st.session_state:
    st.session_state.selected_word_id = None

tab_words, tab_study = st.tabs(["単語管理", "学習"])

with tab_words:
    if selected_folder["description"]:
        st.caption(selected_folder["description"])

    current_page = st.session_state.word_page
    selected_word_id = st.session_state.selected_word_id

    if current_page == "new":
        render_word_form("new", folder_id)
    elif current_page in {"detail", "edit", "delete"}:
        word = get_word(selected_word_id)
        if current_page == "detail":
            render_word_detail(word)
        elif current_page == "edit":
            if word:
                render_word_form("edit", folder_id, word)
            else:
                render_word_detail(word)
        else:
            render_delete_confirmation(word)
    else:
        render_word_list(words)

with tab_study:
    st.subheader("フラッシュカード学習")

    if not words:
        st.warning("このフォルダには単語がありません。")
        st.stop()

    if "study_words" not in st.session_state:
        st.session_state.study_words = random.sample(list(words), len(words))

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
        if current_word["japanese_meaning"]:
            st.write(f"**日本語:** {current_word['japanese_meaning']}")
        st.write(f"**品詞:** {current_word['part_of_speech'] or '未登録'}")
        st.write(f"**読み:** {current_word['transliteration'] or '未登録'}")

        if current_word["example_hebrew"]:
            st.write("**例文:**")
            st.markdown(
                hebrew_html(current_word["example_hebrew"], size=24),
                unsafe_allow_html=True
            )

        if current_word["example_english"]:
            st.write(current_word["example_english"])

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("不正解"):
                save_review(current_word["id"], folder_id, "wrong")
                st.session_state.current_word_index = (current_index + 1) % len(study_words)
                st.rerun()

        with col2:
            if st.button("正解"):
                save_review(current_word["id"], folder_id, "correct")
                st.session_state.current_word_index = (current_index + 1) % len(study_words)
                st.rerun()

        with col3:
            if st.button("シャッフル"):
                st.session_state.study_words = random.sample(list(words), len(words))
                st.session_state.current_word_index = 0
                st.rerun()
