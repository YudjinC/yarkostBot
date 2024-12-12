import sqlite3 as sq

db = sq.connect('tg.db')
cur = db.cursor()


async def db_start():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "tg_id INTEGER, "
        "fio TEXT, "
        "contact TEXT, "
        "email TEXT, "
        "birthday TEXT, "
        "product TEXT, "
        "photo TEXT, "
        "lucky_ticket TEXT)"
    )


async def cmd_start_db(user_id):
    user = cur.execute("SELECT * FROM users WHERE tg_id == ({key})".format(key=user_id)).fetchone()
    if not user:
        cur.execute("INSERT INTO users (tg_id) VALUES ({key})".format(key=user_id))
        db.commit()


async def add_item(state, user_id):
    async with state.proxy() as data:
        cur.execute(
            """
            UPDATE users
            SET fio = ?, contact = ?, email = ?, birthday = ?, product = ?, photo = ?, lucky_ticket = ?
            WHERE tg_id = ?
            """,
            (
                data['fio'],
                data['contact'],
                data['email'],
                data['birthday'],
                data['product'],
                data['photo'],
                data['lucky_ticket'],
                user_id
            )
        )
        db.commit()


async def additional_item(state, user_id):
    async with state.proxy() as data:
        cur.execute(
            """
            UPDATE users
            SET photo = ?, lucky_ticket = ?
            WHERE tg_id = ?
            """,
            (
                data['photo'],
                data['lucky_ticket'],
                user_id
            )
        )
        db.commit()


async def check_advanced_state(user_id):
    cur.execute(
        """
        SELECT fio, contact, email, birthday, product, photo, lucky_ticket
        FROM users
        WHERE tg_id = ?
        """,
        (user_id,)
    )
    result = cur.fetchone()
    if result and all(result):
        return True
    return False


async def personal_accoutn(user_id):
    cur.execute(
        """
        SELECT fio, lucky_ticket
        FROM users
        WHERE tg_id = ?
        """,
        (user_id,)
    )
    return cur.fetchone()
