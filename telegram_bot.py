import os
from dotenv import load_dotenv

import requests
import json


load_dotenv('.env')

token = os.getenv('TELE_API_KEY')
base_url = f"https://api.telegram.org/bot{token}/"
chat_id = "-1002160260782"


def notify_tele_phone_numbers(company, phone):
    message = f"{company} has no website.\nHere's their phone number\n{phone}"
    url = base_url + f"sendMessage?chat_id={chat_id}&text={message}"

    rsp = requests.get(url)

    outcome = rsp.json()
    if outcome["ok"]:
        return True

    return False


def notify_tele_complete(message):
    message = "Scraping complete"
    gif_url = "https://gifdb.com/images/high/spongebob-squarepants-done-and-done-2de4g1978uus7pp6.gif"
    url = base_url + f"sendAnimation?chat_id={chat_id}&caption={message}&animation={gif_url}"

    rsp = requests.get(url)

    outcome = rsp.json()
    if outcome["ok"]:
        return True

    return False


if __name__ == '__main__':
    notify_tele_complete('Scraping Complete')
