import asyncpg

from datetime import date
from dotenv import load_dotenv
import os
load_dotenv()

DB_CONFIG = {
    'user': os.getenv('PG_USER'),
    'password': os.getenv('PG_PASS'),
    'database': os.getenv('PG_DB'),
    'host': os.getenv('PG_HOST'),
    'port': os.getenv('PG_PORT', 5432)
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
                product TEXT[],
                photo TEXT[],
                lucky_ticket TEXT[]
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS promo_codes(
                id SERIAL PRIMARY KEY,
                code VARCHAR(50) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL
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
                SET fio = $1,
                    contact = $2,
                    email = $3,
                    birthday = $4,
                    product = COALESCE(product, ARRAY[]::TEXT[]) || $5,
                    photo = COALESCE(photo, ARRAY[]::TEXT[]) || $6,
                    lucky_ticket = COALESCE(lucky_ticket, ARRAY[]::TEXT[]) || $7
                WHERE tg_id = $8
                """,
                data['fio'],
                data['contact'],
                data['email'],
                data['birthday'],
                [data['product']],
                [data['photo']],
                [data['lucky_ticket']],
                user_id
            )


async def additional_item(pool, state, user_id):
    async with pool.acquire() as conn:
        async with state.proxy() as data:
            await conn.execute(
                """
                UPDATE users
                SET product = COALESCE(product, ARRAY[]::TEXT[]) || $1,
                    photo = COALESCE(photo, ARRAY[]::TEXT[]) || $2,
                    lucky_ticket = COALESCE(lucky_ticket, ARRAY[]::TEXT[]) || $3
                WHERE tg_id = $4
                """,
                [data['product']],
                [data['photo']],
                [data['lucky_ticket']],
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
        if result:
            return all(
                field and (not isinstance(field, list) or len(field) > 0)
                for field in result
            )
        return False


async def personal_account(pool, user_id):
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT fio, lucky_ticket
            FROM users
            WHERE tg_id = $1
            """,
            user_id
        )
        lucky_tickets = result["lucky_ticket"]
        tickets_text = "\n".join(lucky_tickets)
        return {
            "fio": result['fio'],
            "tickets": tickets_text
        }


async def add_promo(pool, promo_code: str, start_date: date, end_date: date):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO promo_codes (promo, start_date, end_date)
            VALUES ($1, $2, $3)
            """,
            promo_code,
            start_date,
            end_date
        )
