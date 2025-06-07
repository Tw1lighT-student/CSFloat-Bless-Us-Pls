import aiosqlite, statistics
from pathlib import Path

DB_PATH = Path("storage/trades.db")

def price_stats(rows):
    """Статистика по каждому разделу (Покупка / продажа)"""
    if not rows:
        return {"count": 0, "sum": 0, "max": None, "min": None, "median": None}
    prices = [row[1] for row in rows]
    return {
        "count": len(rows),
        "sum": round(sum(prices), 2),
        "max": {"item": rows[-1][0], "price": rows[-1][1]},
        "min": {"item": rows[0][0], "price": rows[0][1]},
        "median": round(statistics.median(prices), 2),
    }

async def get_stats(table: str, db_path: Path = DB_PATH):
    """Вытаскиваем интересующие нас данные с датабазы"""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f"SELECT SUM(price), COUNT(*) FROM {table}") as cursor:
            total_sum, total_cnt = await cursor.fetchone()

        sales_rows  = await db.execute_fetchall(
            f"SELECT item_name, price FROM {table} WHERE action='Sale' ORDER BY price"
        )
        purch_rows  = await db.execute_fetchall(
            f"SELECT item_name, price FROM {table} WHERE action='Purchase' ORDER BY price"
        )

    return {
        "total": {"count": total_cnt or 0, "sum": round(total_sum or 0, 2)},
        "sales": price_stats(sales_rows),
        "purchases": price_stats(purch_rows),
    }

async def init_db(steam_id, weeks):
    """"Для начала сделаем проверку на само существование таблицы предметов данного steamid"""
    if not weeks:
        weeks = 'all_time'

    table = f'trades_{steam_id}_{weeks}'
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"DROP TABLE IF EXISTS {table}")

        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                action TEXT,
                rarity_name TEXT,
                wear_name TEXT,
                attribute TEXT,
                price REAL,
                verified_at TEXT         
            )
        """)
        await db.commit()