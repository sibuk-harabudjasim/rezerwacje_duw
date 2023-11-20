# -*- coding: utf-8 -*-
import asyncio
import logging
import traceback
from typing import Callable


log = logging.getLogger()


class Signal:
    name: str
    observers: dict[int, tuple]

    def __init__(self, name: str):
        self.name = name
        self.observers = {}

    def add_observer(self, id: int, callable: Callable, raise_exc: bool = False) -> None:
        self.observers[id] = (callable, raise_exc)

    def remove_observer(self, id: int) -> None:
        self.observers.pop(id, None)

    def emit(self, *args, **kwargs) -> None:
        asyncio.ensure_future(self._emit(*args, **kwargs))

    async def _emit(self, *args, **kwargs) -> None:
        for callable, raise_exc in self.observers.values():
            try:
                if asyncio.iscoroutinefunction(callable):
                    await callable(*args, **kwargs)
                else:
                    callable(*args, **kwargs)
            except Exception as e:
                log.error(f"{self} exception: {str(e)}")
                log.error(traceback.format_exc())
                if raise_exc:
                    raise

    def __repr__(self):
        return f"<Signal {self.name}>"


__author__ = 'manitou'
