from enum import Enum


class Services(str, Enum):
    PASSPORT_APPLY = "złożenie wniosku o wydanie paszportu (wejście główne DUW)"
    PASSPORT_RECEIVE = "odbiór paszportu SALA B (wejście od Bulwaru)"
    PERMIT_RECEIVE = "Odbiór karty pobytu"
    PERMIT_RECEIVE_SAT = "Odbiór karty pobytu ( Soboty– FAMI )"
    INFORMATION = "Punkt informacyjny - legalizacja pobytu ( UKR - uchodźca )"
    PERMIT_RECEIVE_EVENING = "Odbiór karty wieczory informacyjne FAMI"
    PERMIT_RECEIVE_EXTRA = "Odbiór karty pobytu - dodatkowe bilety"


services_map = {
    Services.PASSPORT_APPLY: "99/18",
    Services.PASSPORT_RECEIVE: "100/19",
    Services.PERMIT_RECEIVE: "112/29",
    Services.PERMIT_RECEIVE_SAT: "113/31",
    Services.INFORMATION: "115/41",
    Services.PERMIT_RECEIVE_EVENING: "118/43",
    Services.PERMIT_RECEIVE_EXTRA: "119/44",
}


USERS_FILENAME = "/tmp/bot_users_storage.json"
TASKS_FILENAME = "/tmp/bot_tasks_storage.json"
