import asyncpg
from aiogram.types import InputFile

from datetime import datetime, date
from dotenv import load_dotenv
import csv
import os

TEMP_DIR = "/temp"

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
                promo TEXT[],
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
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            tg_id BIGINT UNIQUE NOT NULL, -- Telegram ID администратора
            fio TEXT, -- Имя администратора
            created_at TIMESTAMP DEFAULT NOW()
            )
            """
        )


async def cmd_start_db(pool, user_id):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE tg_id = $1", user_id)
        if not user:
            await conn.execute("INSERT INTO users (tg_id) VALUES ($1)", user_id)


async def is_admin_user(pool, tg_id):
    """
    Проверяет, является ли пользователь администратором.
    """
    async with pool.acquire() as conn:
        query = """
        SELECT EXISTS(
            SELECT 1 
            FROM admins 
            WHERE tg_id = $1
        )
        """
        result = await conn.fetchval(query, tg_id)
    return result


async def registration_with_photos(pool, state, shared_data, user_id):
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
                shared_data['photos'],
                [data['lucky_ticket']],
                user_id
            )


async def registration_with_promo(pool, state, user_id):
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
                    promo = COALESCE(promo, ARRAY[]::TEXT[]) || $6,
                    lucky_ticket = COALESCE(lucky_ticket, ARRAY[]::TEXT[]) || $7
                WHERE tg_id = $8
                """,
                data['fio'],
                data['contact'],
                data['email'],
                data['birthday'],
                [data['product']],
                [data['promo']],
                [data['lucky_ticket']],
                user_id
            )


async def additional_with_photos(pool, state, shared_data, user_id):
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
                shared_data['photos'],
                [data['lucky_ticket']],
                user_id
            )


async def additional_with_promo(pool, state, user_id):
    async with pool.acquire() as conn:
        async with state.proxy() as data:
            await conn.execute(
                """
                UPDATE users
                SET product = COALESCE(product, ARRAY[]::TEXT[]) || $1,
                    promo = COALESCE(promo, ARRAY[]::TEXT[]) || $2,
                    lucky_ticket = COALESCE(lucky_ticket, ARRAY[]::TEXT[]) || $3
                WHERE tg_id = $4
                """,
                [data['product']],
                [data['promo']],
                [data['lucky_ticket']],
                user_id
            )


async def check_advanced_state(pool, user_id):
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT lucky_ticket
            FROM users
            WHERE tg_id = $1
            """,
            user_id
        )
        if result:
            lucky_ticket = result["lucky_ticket"]
            if isinstance(lucky_ticket, list) and any(ticket is not None for ticket in lucky_ticket):
                return True
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
            INSERT INTO promo_codes (code, start_date, end_date)
            VALUES ($1, $2, $3)
            """,
            promo_code,
            start_date,
            end_date
        )


async def select_promo(pool):
    async with pool.acquire() as conn:
        result = await conn.fetch(
            """
            SELECT code, start_date, end_date 
            FROM promo_codes
            """
        )
    return result


async def select_one_promo(pool, promo_code):
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT code, start_date, end_date 
            FROM promo_codes
            WHERE code = $1
            """,
            promo_code
        )
    return result


async def update_promo(pool, promo_code: str, start_date: date, end_date: date):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE promo_codes
            SET start_date = $1,
                end_date = $2
            WHERE code = $3
            """,
            start_date,
            end_date,
            promo_code
        )


async def check_user_promo(pool, promo_code):
    async with pool.acquire() as conn:
        current_date = datetime.now().date()
        result = await conn.fetchrow(
            """
            SELECT code, start_date, end_date 
            FROM promo_codes
            WHERE code = $1
              AND start_date <= $2
              AND end_date >= $2
            """,
            promo_code,
            current_date
        )
    return result


async def upload_users_database(pool, bot, admin_id):
    """
    Выгружает данные из таблицы users в CSV и отправляет администратору.
    """
    os.makedirs(TEMP_DIR, exist_ok=True)

    csv_file_path = os.path.join(TEMP_DIR, "users_export.csv")

    headers = ["id", "tg_id", "fio", "contact", "email", "birthday", "product", "promo", "photo", "lucky_ticket"]

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM users")

            with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)

                writer.writerow(headers)

                for row in rows:
                    writer.writerow([
                        row["id"],
                        row["tg_id"],
                        row["fio"],
                        row["contact"],
                        row["email"],
                        row["birthday"],
                        ",".join(row["product"] or []),
                        ",".join(row["promo"] or []),
                        ",".join(row["photo"] or []),
                        ",".join(row["lucky_ticket"] or []),
                    ])

        await bot.send_document(admin_id, InputFile(csv_file_path), caption="Экспорт пользователей из БД")

    except Exception as e:
        await bot.send_message(admin_id, f"Ошибка при экспорте данных: {e}")

    finally:
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)


async def upload_users_database_with_promo(pool, bot, admin_id, promo):
    os.makedirs(TEMP_DIR, exist_ok=True)

    csv_file_path = os.path.join(TEMP_DIR, "users_export.csv")

    headers = ["id", "tg_id", "fio", "contact", "email", "birthday", "product", "promo", "photo", "lucky_ticket"]

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * 
                FROM users
                WHERE $1 = ANY(promo);
                """,
                promo
            )
            with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)

                writer.writerow(headers)

                for row in rows:
                    writer.writerow([
                        row["id"],
                        row["tg_id"],
                        row["fio"],
                        row["contact"],
                        row["email"],
                        row["birthday"],
                        ",".join(row["product"] or []),
                        ",".join(row["promo"] or []),
                        ",".join(row["photo"] or []),
                        ",".join(row["lucky_ticket"] or []),
                    ])
        await bot.send_document(admin_id, InputFile(csv_file_path), caption="Экспорт пользователей из БД по промокоду")

    except Exception as e:
        await bot.send_message(admin_id, f"Ошибка при экспорте данных: {e}")

    finally:
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)
