import asyncio
import logging

import aiohttp

from .exceptions import OutOfTries, UnableToAccess
from .response import ResponseData, Method


class HttpMakerAsync:
    def __init__(
        self,
        base_url: str = '',
        base_headers: None | dict = None,
        base_params: None | dict = None,
        tries_to_reconnect: int = 3,
        timeout_in_sec: int = 10,
    ):
        self._base_url = base_url

        self._headers = base_headers
        self._params = base_params

        self._tries_to_reconnect = tries_to_reconnect
        self._timeout = timeout_in_sec

    def get_full_path(self, path: str) -> str:
        if path == '':
            return self._base_url
        return f'{self._base_url}/{path if not path.startswith('/') else path[1:]}'

    async def __execute(
        self,
        path: str,
        method: Method,
        data: dict | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
    ) -> ResponseData:
        logging.debug(
            f'{self.__class__.__name__} {method} -> {path} ? {params}',
        )
        for _ in range(self._tries_to_reconnect):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self._timeout)) as session:
                    http_method = getattr(session, method.lower())

                    # Совмещаем заголовки
                    if headers is None and self._headers is not None:
                        headers = self._headers
                    if headers is None and self._headers is not None:
                        headers = self._headers
                    if headers is not None and self._headers is not None:
                        headers.update(self._headers)

                    # Совмещаем параметры
                    if params is None and self._params is not None:
                        params = self._params
                    if params is None and self._params is not None:
                        headers = self._params
                    if params is not None and self._params is not None:
                        params.update(self._params)

                    async with http_method(
                        url=self.get_full_path(path) if not path.startswith('http') else path,
                        headers=headers,
                        params=params,
                        data=data,
                        json=json,
                    ) as res:
                        return await self.__get_response_data(res)
            except aiohttp.ClientConnectorError as e:
                logging.error(f'{self.__class__.__name__} > Client connection error {e}')
                if try_wait_if_error:
                    await asyncio.sleep(10)
                    continue
                return None
            except aiohttp.ConnectionTimeoutError as e:
                logging.error(f'{self.__class__.__name__} > Connection error: {e}')
                if try_wait_if_error:
                    await asyncio.sleep(20)
                    continue
                return None
            except aiohttp.ClientError as e:
                logging.critical(f'{self.__class__.__name__} > Client error: {e}')
                if try_wait_if_error:
                    await asyncio.sleep(60)
                    continue
                return None
            except AttributeError as e:
                logging.critical(f'{self.__class__.__name__} > Uncaught error: {e}')
                return None
        logging.critical(f'{self.__class__.__name__} > Tries out but no return')
        raise OutOfTries(path)

    async def _make(
        self,
        url: str = '',
        method: Method = 'GET',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
    ) -> ResponseData:
        logging.debug(f'{self.__class__.__name__} > make -> {self.get_full_path(url)}\n')

        res = await self.__execute(
            path=url,
            method=method,
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error,
        )
        return res

    async def __get_response_data(
        self,
        response: aiohttp.ClientResponse,
    ) -> ResponseData:
        # Получаем тип контента (проверяем оба варианта регистра)
        try:
            content_type = (
                response.headers.get('Content-Type') or
                {name.lower(): val for name, val in response.headers}.get('content-type')
            )
        except ValueError:
            logging.warning(f'{self.__class__.__name__} > no content-type header, set empty')
            content_type = 'empty'

        try:
            match content_type.split(';')[0].strip().lower():
                case 'application/json' | 'text/html':
                    data = await response.json(content_type=None if 'html' in content_type else 'json')
                    if type(data) is not dict:
                        data = {'data': data}
                case 'empty':
                    data = await response.json(content_type='json')
                case _:
                    logging.warning(f'{self.__class__.__name__} > unreadable content type: {content_type}')
                    raise UnableToAccess(response.url)
            return ResponseData(
                url=str(response.url),
                status=response.status,
                headers=dict(response.headers),
                json=data,
            )
        except aiohttp.ContentTypeError as e:
            logging.error(e)
            raise UnableToAccess(response.url)
