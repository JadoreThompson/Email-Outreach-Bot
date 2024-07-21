import os
from dotenv import load_dotenv

import requests
import json

import asyncio

load_dotenv('.env')

token = os.getenv('TELE_API_KEY')
base_url = f"https://api.telegram.org/bot{token}/"
chat_id = "-1002160260782"


async def notify_tele_phone_numbers(company, phone, session):
    message = f"{company} has no website.\nHere's their phone number\n{phone}"
    url = base_url + f"sendMessage?chat_id={chat_id}&text={message}"

    async with await session.get(url) as rsp:
        if rsp.status == 200:
            outcome = await rsp.json()
            if outcome["ok"]:
                return True

        return False


async def notify_tele_complete(session):
    message = "Scraping complete"
    gif_url = "https://gifdb.com/images/high/spongebob-squarepants-done-and-done-2de4g1978uus7pp6.gif"
    url = base_url + f"sendAnimation?chat_id={chat_id}&caption={message}&animation={gif_url}"

    async with await session.get(url) as rsp:
        if rsp.status == 200:
            outcome = await rsp.json()
            if outcome["ok"]:
                return True

    return False


if __name__ == '__main__':
    pass
