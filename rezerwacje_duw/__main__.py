


import asyncio
from environs import Env

from rezerwacje_duw.consts import Services
from rezerwacje_duw.task_manager import TaskManager
from rezerwacje_duw.storage import UsersFileStorage
from rezerwacje_duw.conversations import start_bot


def print_notification(subscriber_id: int, service: Services, day: str):
    print(f"NOTIFICATION FOR {subscriber_id}: {service} is available at {day}")


async def monitor_users(storage):
    while True:
        print("Users:")
        print(storage.users)
        # for user in storage.users.values():
        #     print(f"\t{user.id} {user.subscribed_services}")
        await asyncio.sleep(1)


async def main():
    env = Env()
    env.read_env()
    task_manager = TaskManager()
    userstorage = UsersFileStorage(task_manager)
    task_manager.notifications_signal.add_observer(2, print_notification, raise_exc=False)
    asyncio.create_task(monitor_users(userstorage))
    asyncio.create_task(task_manager.run())
    await start_bot(userstorage, task_manager)


if __name__ == '__main__':
    asyncio.run(main())


# TODO:
# create fetcher file (signle service fetch task)
# pass task manager to user
# pass sender to user from bot
# trigger send from user callback
