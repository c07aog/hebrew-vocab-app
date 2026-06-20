from db import get_connection, initialize_database


def get_or_create_folder(cur, name, description):
    cur.execute(
        """
        SELECT id
        FROM folders
        WHERE name = %s
        """,
        (name,)
    )

    folder = cur.fetchone()

    if folder:
        return folder["id"]

    cur.execute(
        """
        INSERT INTO folders (name, description)
        VALUES (%s, %s)
        """,
        (name, description)
    )

    cur.execute(
        """
        SELECT id
        FROM folders
        WHERE name = %s
        """,
        (name,)
    )

    return cur.fetchone()["id"]


def get_or_create_word(cur, word):
    cur.execute(
        """
        SELECT id
        FROM words
        WHERE hebrew = %s
          AND english_meaning = %s
        """,
        (
            word["hebrew"],
            word["english_meaning"]
        )
    )

    existing_word = cur.fetchone()

    if existing_word:
        return existing_word["id"]

    cur.execute(
        """
        INSERT INTO words (
            hebrew,
            hebrew_pointed,
            hebrew_no_niqqud,
            transliteration,
            part_of_speech,
            english_meaning,
            example_hebrew,
            example_english
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            word["hebrew"],
            word["hebrew_pointed"],
            word["hebrew_no_niqqud"],
            word["transliteration"],
            word["part_of_speech"],
            word["english_meaning"],
            word["example_hebrew"],
            word["example_english"]
        )
    )

    cur.execute(
        """
        SELECT id
        FROM words
        WHERE hebrew = %s
          AND english_meaning = %s
        """,
        (
            word["hebrew"],
            word["english_meaning"]
        )
    )

    return cur.fetchone()["id"]


def seed_data():
    initialize_database()

    conn = get_connection()
    cur = conn.cursor()

    folder_id = get_or_create_folder(
        cur,
        "初級ヘブライ語",
        "最初に覚える基本単語"
    )

    words = [
        {
            "hebrew": "שָׁלוֹם",
            "hebrew_pointed": "שָׁלוֹם",
            "hebrew_no_niqqud": "שלום",
            "transliteration": "shalom",
            "part_of_speech": "noun / greeting",
            "english_meaning": "peace / hello",
            "example_hebrew": "שָׁלוֹם עֲלֵיכֶם",
            "example_english": "Peace be upon you."
        },
        {
            "hebrew": "סֵפֶר",
            "hebrew_pointed": "סֵפֶר",
            "hebrew_no_niqqud": "ספר",
            "transliteration": "sefer",
            "part_of_speech": "noun",
            "english_meaning": "book",
            "example_hebrew": "זֶה סֵפֶר טוֹב.",
            "example_english": "This is a good book."
        },
        {
            "hebrew": "בַּיִת",
            "hebrew_pointed": "בַּיִת",
            "hebrew_no_niqqud": "בית",
            "transliteration": "bayit",
            "part_of_speech": "noun",
            "english_meaning": "house / home",
            "example_hebrew": "זֶה הַבַּיִת שֶׁלִּי.",
            "example_english": "This is my house."
        },
        {
            "hebrew": "מֶלֶךְ",
            "hebrew_pointed": "מֶלֶךְ",
            "hebrew_no_niqqud": "מלך",
            "transliteration": "melekh",
            "part_of_speech": "noun",
            "english_meaning": "king",
            "example_hebrew": "הַמֶּלֶךְ גָּדוֹל.",
            "example_english": "The king is great."
        },
        {
            "hebrew": "טוֹב",
            "hebrew_pointed": "טוֹב",
            "hebrew_no_niqqud": "טוב",
            "transliteration": "tov",
            "part_of_speech": "adjective",
            "english_meaning": "good",
            "example_hebrew": "יוֹם טוֹב.",
            "example_english": "Good day."
        }
    ]

    for word in words:
        word_id = get_or_create_word(cur, word)

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

    print("初期データを登録しました。")


if __name__ == "__main__":
    seed_data()