import aiohttp, aiosqlite, ssl, certifi
from datetime import datetime, timezone, timedelta
from pathlib import Path
import asyncio
import logging
import time
from services.work_with_database import init_db

CSFLOAT_ME_URL     = "https://csfloat.com/api/v1/me"
CSFLOAT_TRADES_URL = "https://csfloat.com/api/v1/me/trades"
DB_PATH = Path("storage/trades.db")

cash_timeout = 15 * 60
user_cache: dict[int, dict[str, dict[str, float]]] = {}
steam_id_cache = {}

http_timeout = aiohttp.ClientTimeout(total=15)
ssl_ctx = ssl.create_default_context(cafile=certifi.where())

async def get_steam_id(auth_key: str) -> str | None:
    """Возвращает steam-id для заданного API-ключа или None, если не удалось."""
    if auth_key in steam_id_cache:
        logging.debug(f"CACHE HIT - ключ {auth_key}")
        return steam_id_cache[auth_key]

    headers = {"Authorization": auth_key}
    try:
        async with aiohttp.ClientSession(
                timeout=http_timeout,
                connector=aiohttp.TCPConnector(ssl=ssl_ctx)) as session:
            async with session.get(CSFLOAT_ME_URL, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    steam_id = data["user"]["steam_id"]
                    steam_id_cache[auth_key] = steam_id            # кешируем
                    logging.debug(f"Получен steam_id {steam_id}")
                    return steam_id
                else:
                    body = await resp.text()
                    logging.warning(f"CSFloat {resp.status} – {body[:100]}")
    except asyncio.TimeoutError:
        logging.warning("Таймаут при обращении к CSFloat /me")
    except aiohttp.ClientError as e:
        logging.warning(f"Сетевая ошибка CSFloat: {e}")

    logging.debug(f"Не удалось получить SteamID для ключа {auth_key}")
    return None

async def fetch_all_sales(steam_id: str, auth_key: str, user_id: int, time_limit=None):
    """Функция для сбора статистики аккаунта и выгрузки в датабазу"""
    headers = {"Authorization": auth_key}
    if time_limit:
        table = f'trades_{steam_id}_{time_limit}'
    else:
        table = f'trades_{steam_id}_all_time'

    now = time.time()
    entry = user_cache.get(user_id, {}).get(table)
    if entry:
        created   = entry["created"]
        # если прошло < 15 мин с момента СОЗДАНИЯ таблицы, то используем кэш
        if now - created < cash_timeout:
            entry["accessed"] = now            # только обновляем «обращение»
            logging.info("Кэш свеж => API не трогаем")
            return

    unix_border = 0
    await init_db(steam_id, time_limit)
    if time_limit:
        unix_border = (datetime.now() - timedelta(weeks=time_limit)).timestamp()

    async with aiohttp.ClientSession(
        timeout=http_timeout,
        connector=aiohttp.TCPConnector(ssl=ssl_ctx)
    ) as session, aiosqlite.connect(DB_PATH) as db:
        page = 0
        while True:
            params = {"page": page, "limit": 100}
            try:
                async with session.get(CSFLOAT_TRADES_URL, headers=headers, params=params) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logging.warning(f"CSFloat {resp.status} – {body[:120]}")
                        break

                    data = await resp.json()
            except asyncio.TimeoutError:
                logging.warning(f"Таймаут при запросе trades page={page}")
                break
            except aiohttp.ClientError as e:
                logging.warning(f"Сетевая ошибка CSFloat: {e}")
                break

            trades = data.get("trades", [])
            if not trades:
                break  # пустая страница

            rows_to_insert = []
            for item in trades:
                if item["state"] != "verified":
                    continue

                # время сделки → UNIX
                dt = datetime.strptime(item["verified_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                unix_ts = dt.timestamp()
                if time_limit and unix_ts < unix_border:
                    continue

                price = round(float(item["contract"]["price"]) / 100, 2)
                item_info = item["contract"]["item"]

                action = "Purchase" if item["seller_id"] != steam_id else "Sale"
                attribute = (
                    "MISC" if item_info["is_commodity"] else
                    "Статтрек" if item_info["is_stattrak"] else
                    "Сувенирный" if item_info["is_souvenir"] else
                    "Обычный"
                )
                wear_name = item_info.get("wear_name", "MISC")

                rows_to_insert.append((
                    item_info["item_name"],
                    action,
                    item_info["rarity_name"],
                    wear_name,
                    attribute,
                    price,
                    item["verified_at"]
                ))

            await db.executemany(f"""
                                INSERT INTO {table}
                                (item_name, action, rarity_name, wear_name, attribute, price, verified_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, rows_to_insert)
            await db.commit()

            if len(trades) < 100:
                break  # последняя страница
            page += 1

        user_cache.setdefault(user_id, {})[table] = {
            "created": now,
            "accessed": now
        }



