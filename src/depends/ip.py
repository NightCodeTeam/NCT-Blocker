from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status


async def ip_correct(ip: str) -> str:
    """
    Проверяет корректность IP-адреса.
    """
    ip_s = ip.split('.')
    if len(ip_s) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid IP address'
        )
    try:
        for i in ip_s:
            n = int(i)
            if not 0 <= n <= 255:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Invalid IP address'
                )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid IP address'
        )
    return ip


IPDep = Annotated[str, Depends(ip_correct)]
