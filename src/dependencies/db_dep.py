from typing import Annotated

from fastapi import Depends

from src.database import async_session
from src.utils.db_manager import DBManager


async def get_db():
    async with DBManager(session_factory=async_session) as db:
        yield db


DBDep = Annotated[DBManager, Depends(get_db)]
