import os
import aiohttp
import asyncio
import logging
import traceback
from datetime import date, timedelta

from bs4 import BeautifulSoup
from rezerwacje_duw.consts import Services, services_map


log = logging.getLogger()


USER = os.getenv("USER", None)
PASS = os.getenv("PASS", None)
if not USER or not PASS:
    raise KeyError("No credentials defined in application. Please, define USER= and PASS= environment variables")


def _get_login_data(body: str) -> dict:
    root = BeautifulSoup(body, 'html.parser')
    form = root.find(id="LoginForm")
    if not form:
        return
    inputs = form.find_all("input")
    return {i["name"]: i.get("value", None) for i in inputs if i.get("name", None)}


def _get_status(body: str) -> bool:
    assert "wow404.png" not in body, "404 page"
    root = BeautifulSoup(body, 'html.parser')
    status = root.find("h4", class_="alert-heading")
    if not status:
        return False, root.prettify()
    return "Brak wolnych terminów." not in status.string, status


async def _make_login(session: aiohttp.ClientSession) -> None:
    res = await session.get("https://rezerwacje.duw.pl/pol/login", ssl=False)
    assert res.status == 200, f"Wrong status: {res.status=}"
    login_data = _get_login_data(await res.text())
    login_data["data[User][email]"] = USER
    login_data["data[User][password]"] = PASS
    res = await session.post("https://rezerwacje.duw.pl/pol/login", ssl=False, data=aiohttp.FormData(login_data), allow_redirects=False)
    assert res.status in [301, 302], f"Wrong status: {res.status=}"


async def _get_status_for_day(session: aiohttp.ClientSession, service_postfix: str, day: str) -> bool:
    res = await session.get(f"https://rezerwacje.duw.pl/pol/queues/{service_postfix}/{day}", ssl=False, headers={"X-Requested-With": "XMLHttpRequest"})
    assert res.status == 200, f"Wrong status: {res.status=}"
    return _get_status(await res.text())


async def fetch_queues_availability(services: list[Services]) -> dict[Services, set[str]]:
    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0"}, timeout=aiohttp.ClientTimeout(3)) as s:
        await _make_login(s)

        days = [(date.today() + timedelta(days=i)).isoformat() for i in range(10)]
        results = {}

        for service in services:
            service_result = set()
            service_postfix = services_map[service]
            for day in days:
                try:
                    status, data = await _get_status_for_day(s, service_postfix, day)
                    log.info(f"Status for {day} at {service}: {data}")
                    if status:
                        service_result.add(day)
                except AssertionError:
                    break
                except Exception as e:
                    log.error(f"Exception during _get_status_for_day() for service '{service}' (day {day})")
                    log.error(traceback.format_exc())
                    break
            if service_result:
                results[service] = service_result

        return results
