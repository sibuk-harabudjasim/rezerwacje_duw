import asyncio
import os
import json
import logging
import traceback
from datetime import datetime

from rezerwacje_duw.consts import Services, TASKS_FILENAME
from rezerwacje_duw.core.signal import Signal
from rezerwacje_duw.fetcher import fetch_queues_availability


log = logging.getLogger()


class TaskManager:
    QUERY_SERVICES_EACH_SECONDS = 60
    LOOP_SLEEP_SECONDS = 5
    notifications_map: dict[Services, set[int]]
    tasks_context_map: dict
    notifications_signal: Signal

    def __init__(self) -> None:
        self.notifications_map = {s: set() for s in Services}
        self.notifications_signal = Signal("notifications")  # subscriber_id, service, day

    def subscribe(self, service: Services, subscriber_id: int) -> None:
        self.notifications_map[service].add(subscriber_id)

    def unsubscribe(self, service: Services, subscriber_id: int) -> None:
        if subscriber_id in self.notifications_map[service]:
            self.notifications_map[service].remove(subscriber_id)

    def _load_tasks(self) -> dict[int, dict]:
        if not os.path.exists(TASKS_FILENAME):
            return {}
        with open(TASKS_FILENAME, "r") as f:
            return json.load(f)

    def _save_tasks(self, tasks_map: dict) -> None:
        with open(TASKS_FILENAME, "w") as f:
            json.dump(tasks_map, f)

    def _get_services_to_query(self) -> dict[Services, set[int]]:
        result = {}
        now = datetime.now().timestamp()
        for service, subscribers in self.notifications_map.items():
            if not subscribers:
                continue
            last_updated = self.tasks_context_map.get(service, 0)
            if now - last_updated < self.QUERY_SERVICES_EACH_SECONDS:
                continue
            result[service] = subscribers
        return result

    def _update_tasks_context(self, queried_services: list) -> None:
        now = datetime.now().timestamp()
        for service in queried_services:
            self.tasks_context_map[service] = now
        self._save_tasks(self.tasks_context_map)

    async def run(self) -> None:
        self.tasks_context_map = self._load_tasks()
        while True:
            await asyncio.sleep(self.LOOP_SLEEP_SECONDS)
            services = self._get_services_to_query()
            if not services:
                continue
            log.info(f"Fetching data for services: {services.keys()}")
            try:
                available_days = await fetch_queues_availability(services)
            except Exception as e:
                log.error(f"Error during fetching data: {str(e)}")
                log.error(traceback.format_exc())
                continue
            self._update_tasks_context(services)
            if available_days:
                for service, days in available_days.items():
                    for day in days:
                        for subscriber_id in services[service]:
                            self.notifications_signal.emit(subscriber_id=subscriber_id, service=service, day=day)
