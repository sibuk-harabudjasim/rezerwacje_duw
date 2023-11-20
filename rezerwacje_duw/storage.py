import json
import os

from yaaiotg.userstorage.base import UserStorageBase, User as BaseUser

from rezerwacje_duw.consts import Services, USERS_FILENAME
from rezerwacje_duw.task_manager import TaskManager


class User(BaseUser):
    subscribed_services: set(Services)

    def __init__(self, user_id: int, task_manager: TaskManager, user_meta: dict | None = None, subscribed_services: list[str] = None) -> None:
        super().__init__(user_id, user_meta)
        self.task_manager = task_manager
        self.subscribed_services = set(subscribed_services or [])
        self._subscribe_for_services_at_startup()

    def _subscribe_for_services_at_startup(self):
        for service in self.subscribed_services:
            self.task_manager.subscribe(service, self.id)

    def to_dict(self) -> dict:
        return {
            "user_id": self.id,
            "user_meta": self.user_meta,
            "subscribed_services": list(self.subscribed_services),
        }

    @classmethod
    def from_dict(cls, task_manager: TaskManager, data: dict) -> "User":
        return User(task_manager=task_manager, **data)

    def subscribe(self, service: Services) -> None:
        self.task_manager.subscribe(service, self.id)
        self.subscribed_services.add(service)

    def unsubscribe(self, service: Services) -> None:
        self.task_manager.unsubscribe(service, self.id)
        if service in self.subscribed_services:
            self.subscribed_services.remove(service)


class UsersFileStorage(UserStorageBase):
    users: dict[int, User]

    def __init__(self, task_manager: TaskManager) -> None:
        super().__init__()
        self.task_manager = task_manager
        self.users = self.load_file()

    def load_file(self) -> dict[int, User]:
        if not os.path.exists(USERS_FILENAME):
            return {}
        with open(USERS_FILENAME, "r") as f:
            data = json.load(f)
        return {id: User.from_dict(self.task_manager, userdata) for id, userdata in data}

    def save_file(self) -> None:
        data = [[id, user.to_dict()] for id, user in self.users.items()]
        with open(USERS_FILENAME, "w") as f:
            json.dump(data, f)

    async def get_or_create(self, user_id: int, user_meta: dict | None = None) -> User:
        if user_id not in self.users:
            self.users[user_id] = User(user_id, self.task_manager, user_meta)
        return self.users[user_id]

    async def save(self, user: User) -> None:
        self.users[user.id] = user
        self.save_file()

    def get_watched_topics(self) -> set(Services):
        return set([service for user in self.users.values() for service in user.subscribed_services])
