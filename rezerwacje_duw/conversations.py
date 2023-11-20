import os
from functools import partial
from yaaiotg.bot import YaaiotgBot
from yaaiotg.types import KbdKey, KbdInlineKey
from yaaiotg.dialog import DialogActions
from yaaiotg.callback import CallbackActions
from yaaiotg.dialog_control import SubDialogRun
from yaaiotg.userstorage.base import UserStorageBase

from rezerwacje_duw.consts import Services
from rezerwacje_duw.storage import User
from rezerwacje_duw.task_manager import TaskManager


services_mapping = {service: str(i) for i, service in enumerate(Services)}
nums_mapping = {str(i): service for i, service in enumerate(Services)}


def _make_subscribe_button(service):
    return KbdInlineKey("Subscribe", slug="subscribe_"+services_mapping[service], callback=partial(subscribe, service=service))


def _make_unsubscribe_button(service):
    return KbdInlineKey("Unsubscribe", slug="unsubscribe_"+services_mapping[service], callback=partial(unsubscribe, service=service))


async def introduce_myself(dialog, initial_message=None):
    yield dialog.say("I'm bot informing when new tickets in DUW are available")
    yield dialog.return_(None)


async def subscribe(user: User, callback_actions: CallbackActions, service: Services):
    print(f"subscribe({user=}, {callback_actions=}, {service=})")
    if service not in Services:
        callback_actions.delete_message()
        return
    user.subscribe(service)
    callback_actions.edit_markup(new_markup=[_make_unsubscribe_button(service)])


async def unsubscribe(user: User, callback_actions: CallbackActions, service: Services):
    print(f"unsubscribe({user=}, {callback_actions=}, {service=})")
    if service not in Services:
        callback_actions.delete_message()
        return
    user.unsubscribe(service)
    callback_actions.edit_markup(new_markup=[_make_subscribe_button(service)])


async def queues(dialog: DialogActions, initial_message: str = None):
    for service in Services:
        if service in dialog.user.subscribed_services:
            yield dialog.say(service, inline_keyboard=[_make_unsubscribe_button(service)])
        else:
            yield dialog.say(service, inline_keyboard=[_make_subscribe_button(service)])


main_keyboard = [
    KbdKey(text="What do I do", callback=SubDialogRun(introduce_myself)),
    KbdKey(text="Queues status", callback=SubDialogRun(queues)),
]


async def talk(dialog, initial_message=None):
    yield dialog.say("Hi, I'm somebot")
    while True:
        action = yield dialog.ask("What do we do now?", keyboard=main_keyboard)
        if action:
            print('return', action)
            yield dialog.say("Just use my shiny buttons :)")


async def send_notification(bot: YaaiotgBot, subscriber_id: int, service: Services, day: str):
    chat = bot.bot.private(subscriber_id)
    await chat.send_text(f"There's available timeslots for '{service.value}' queue for {day}")


async def start_bot(userstorage: UserStorageBase, task_manager: TaskManager):
    token = os.getenv('TELEGRAM_TOKEN')
    bot = YaaiotgBot(userstorage=userstorage, api_token=token)
    # task_manager.notifications_signal.add_observer(1, partial(send_notification, bot=bot), raise_exc=False)
    bot.entry_point = talk
    await bot.run()
