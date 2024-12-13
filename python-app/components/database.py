import asyncpg

from dotenv import load_dotenv
import os
load_dotenv()

DB_CONFIG = {
    'user': os.getenv('PG_USER'),
    'password': os.getenv('PG_PASS'),
    'database': os.getenv('PG_DB'),
    'host': os.getenv('PG_HOST')
}


async def create_db_pool():
    return await asyncpg.create_pool(**DB_CONFIG)


async def db_start(pool):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                id SERIAL PRIMARY KEY,
                tg_id BIGINT UNIQUE,
                fio TEXT,
                contact TEXT,
                email TEXT,
                birthday TEXT,
                product TEXT,
                photo TEXT,
                lucky_ticket TEXT
            )
            """
        )


async def cmd_start_db(pool, user_id):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE tg_id = $1", user_id)
        if not user:
            await conn.execute("INSERT INTO users (tg_id) VALUES ($1)", user_id)


async def add_item(pool, state, user_id):
    async with pool.acquire() as conn:
        async with state.proxy() as data:
            await conn.execute(
                """
                UPDATE users
                SET fio = $1, contact = $2, email = $3, birthday = $4, product = $5, photo = $6, lucky_ticket = $7
                WHERE tg_id = $8
                """,
                data['fio'],
                data['contact'],
                data['email'],
                data['birthday'],
                data['product'],
                data['photo'],
                data['lucky_ticket'],
                user_id
            )


async def additional_item(pool, state, user_id):
    async with pool.acquire() as conn:
        async with state.proxy() as data:
            await conn.execute(
                """
                UPDATE users
                SET photo = $1, lucky_ticket = $2
                WHERE tg_id = $3
                """,
                data['photo'],
                data['lucky_ticket'],
                user_id
            )


async def check_advanced_state(pool, user_id):
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT fio, contact, email, birthday, product, photo, lucky_ticket
            FROM users
            WHERE tg_id = $1
            """,
            user_id
        )
        if result and all(result):
            return True
        return False


async def personal_account(pool, user_id):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT fio, lucky_ticket
            FROM users
            WHERE tg_id = $1
            """,
            user_id
        )
