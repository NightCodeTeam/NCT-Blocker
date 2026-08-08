import asyncio
import sys, os
import shutil

import redis
from src.database import get_session, DataBase
from src.settings import settings


async def get_db():
    async with get_session() as session:
        yield DataBase(session)


def sizes():
    """
    Выводит размеры кэша, логов и базы данных.
    """
    def get_dir_size(path='.'):
        total_size = 0
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    #print(f'cache size: {get_dir_size('./cache') / 1024 / 1024:.2f} MB')
    print(f'log size: {get_dir_size('./logs') / 1024 / 1024:.2f} MB')
    print(f'db size: {os.path.getsize('ffw_eve.sqlite3') / 1024 / 1024:.2f} MB')


def clear_cache():
    """
    Очищает кэш.
    """
    r = redis.Redis(
        host=settings.REDIS_URL.split(':')[1],
        port=settings.REDIS_URL.split(':')[2],
        db=0,
        decode_responses=True
    )
    prefix = settings.REDIS_PREFIX

    # Использование pipeline для ускорения удаления
    pipe = r.pipeline()
    count = 0

    for key in r.scan_iter(match=prefix):
        pipe.delete(key)
        count += 1
        # Отправляем пачками по 500 ключей
        if count % 500 == 0:
            pipe.execute()

    # Удаляем остаток
    pipe.execute()


async def bans():
    async with get_session() as session:
        db = DataBase(session)
        bans_all = await db.bans.all()
        print(f'Всего банов: {len(bans_all)}')
        for b in bans_all:
            print(f'{b.ip} - {b.reason}')


async def remove_ban(ip: str):
    async with get_session() as session:
        db = DataBase(session)
        return await db.bans.delete_by_ip(ip)


def help():
    """
    Выводит список доступных команд.
    """
    print('Использование: python manage.py {команда}')
    print('Команды:')
    print('  sizes - выводит размеры кэша, логов и базы данных')
    print('  clear_cache - очищает кэш')
    print('  bans - выводит список банов')
    print('  remove_ban - удаляет бан по IP')



async def main():
    if len(sys.argv) > 1:
        match sys.argv[1]:
            case "help" | "--help" | "--h":
                help()
            case "sizes":
                sizes()
            case "clear_cache":
                clear_cache()
            case "bans":
                await bans()
            case "remove_ban":
                if len(sys.argv) > 2:
                    await remove_ban(sys.argv[2])
                else:
                    print('IP address is required')
            case _:
                print(f'Unknown command: {sys.argv[1]}')
                help()
    else:
        help()


if __name__ == "__main__":
    asyncio.run(main())
