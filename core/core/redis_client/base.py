from typing import Any
import json
import logging

import redis.asyncio as redis
from redis.exceptions import ConnectionError

from .exceptions import UnsupportedAnswer, UnsupportedType



KeysType = list[str | int] | tuple[str | int]


class RedisClient:
    def __init__(self, redis_pool: redis.ConnectionPool, prefix: str, expire: int = 3600):
        self.__client = redis.Redis(connection_pool=redis_pool)

        self.__prefix = prefix
        self.__expire = expire

    def __insert_prefix_key(self, key: str | int, spec_app_prefix: str | None = None) -> str:
        if spec_app_prefix is None:
            return f'{str(self.__prefix)}_{str(key)}'
        return f'{str(spec_app_prefix)}_{str(key)}'

    def __parse_ans(self, ans: str | bytes):
        if ans is None:
            return None
        match ans[0]:
            case 'b':
                return True if ans == 'b1' else False
            case 'B':
                return ans[1:]
            case 's':
                return ans[1:]
            case 'i':
                return int(ans[1:])
            case 'f':
                return float(ans[1:])
            case 'L':
                return str(ans[1:]).split("&")
        raise UnsupportedAnswer(ans)

    def __type_pointer(self, value) -> str:
        t = type(value)
        if t is str:
            return f's{value}'
        elif t is bytes:
            return f'B{value}'
        elif t is int:
            return f'i{value}'
        elif t is float:
            return f'f{value}'
        elif t is bool:
            return 'b1' if value else 'b0'
        elif t is list or t is tuple:
            return f'L{"&".join(map(str, value))}'
        raise UnsupportedType(value)

    async def get(self, key: str | int, spec_app_prefix: str | None = None):
        return self.__parse_ans(await self.__client.get(
            self.__insert_prefix_key(key, spec_app_prefix=spec_app_prefix)
        ))

    async def set(self, key: str, value: Any):
        return await self.__client.set(
            self.__insert_prefix_key(key),
            self.__type_pointer(value),
            ex=self.__expire
        )

    async def delete(self, key: str | int):
        return await self.__client.delete(self.__insert_prefix_key(key))

    def multiple_keys(self, keys: KeysType):
        return f'{self.__prefix}_{":".join(map(str, keys))}'

    async def set_json(self, key: str, data: dict, debug: bool = False):
        if debug:
            print(f'set_json: {key}')
        try:
            await self.__client.set(
                self.__insert_prefix_key(key),
                json.dumps(data),
                ex=self.__expire
            )
        except ConnectionError:
            return None

    async def get_json(
        self,
        key: str,
        spec_app_prefix: str | None = None,
        debug: bool = False
    ) -> dict | None:
        if debug:
            print(f'get_json: {key}')
        key = self.__insert_prefix_key(key, spec_app_prefix=spec_app_prefix)
        try:
            ans = await self.__client.get(key)
            if ans is None:
                return None
            return json.loads(ans)
        except ConnectionError:
            return None
