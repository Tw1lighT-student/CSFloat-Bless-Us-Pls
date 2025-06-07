import json
import aiofiles
import os
import logging

data_file = "storage/data.json"
ban_list = "storage/ban_list.json"

async def get_user_key_by_id(user_id: int | str, path=data_file):
    try:
        async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content)
        return data.get(str(user_id))['api_key'], data.get(str(user_id))['steam_id']
    except (FileNotFoundError, json.JSONDecodeError):
        return None, None

async def save_user_key(chat_id: int, key: str, steam_id):
    data = {}

    if os.path.exists(data_file):
        try:
            async with aiofiles.open(data_file, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
        except json.JSONDecodeError:
            pass

    if str(chat_id) in data:
        logging.info(f"Обновлён API-ключ для chat_id={chat_id}")
    else:
        logging.info(f"Сохранён новый API-ключ для chat_id={chat_id}")

    data[str(chat_id)] = {"api_key": key, "steam_id": steam_id}

    async with aiofiles.open(data_file, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, indent=2, ensure_ascii=False))

async def is_user_registered(user_id: int) -> bool:
    if not os.path.exists(data_file):
        return False

    try:
        async with aiofiles.open(data_file, "r", encoding="utf-8") as f:
            content = await f.read()
            users = json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return False

    return str(user_id) in users

async def is_user_banned(user_id: int) -> bool:
    if not os.path.exists(ban_list):
        return False

    try:
        async with aiofiles.open(ban_list, "r", encoding="utf-8") as f:
            content = await f.read()
            user_ids = json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return False

    return user_id in user_ids