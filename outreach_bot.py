import asyncio
import pickle

import os

import aiohttp
import aiosmtplib
from dotenv import load_dotenv

import json
import requests

import re

import smtplib
from email.message import EmailMessage
import ssl

import time
from datetime import timedelta, datetime

from telegram_bot import notify_tele_phone_numbers, notify_tele_complete


load_dotenv('.env')

places_api_key = os.getenv('PLACES_API_KEY')
url = "https://places.googleapis.com/v1/places:searchText"
header = {
    'X-Goog-Api-Key': places_api_key,
    'X-Goog-FieldMask': 'places.displayName,places.name,places.id,places.websiteUri,places.nationalPhoneNumber,places.rating,nextPageToken',
    'Content-Type': 'application/json'
}

email_sender = os.getenv('EMAIL_SENDER')
email_password = os.getenv('EMAIL_PASSWORD')

tele_api_key = os.getenv('TELE_API_KEY')
base_url = f"https://api.telegram.org/bot{tele_api_key}/"

CACHE_DIR = './cache_collection'
os.makedirs(CACHE_DIR, exist_ok=True)


def get_companies(industry, next_page_token=None):
    payload = {
        'textQuery': industry,
        'locationBias': {
            'circle': {
                'center': {'latitude': 51.5964, 'longitude': 0.0349},
                'radius': 50000.0
            }
        },
        'pageSize': 100
    }

    if next_page_token:
        payload['pageToken'] = next_page_token

    rsp = requests.post(url, headers=header, json=payload)
    return rsp.json()


def save_cache(email, cache_file):
    with open(cache_file, 'wb') as f:
        pickle.dump({'timestamp': datetime.now(), 'data': email}, f)


def load_cache(cache_expiry, cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            cache = pickle.load(f)
        if datetime.now() - cache['timestamp'] < cache_expiry:
            return True
    return False


async def get_company_details(session, company):
    cache_file = os.path.join(CACHE_DIR, f"{company['displayName']['text']}.pkl")
    cache_expiry = timedelta(hours=720)

    def check_phone_and_website():
        number = company.get('nationalPhoneNumber')
        website = company.get('websiteUri')

        if website:
            return True

        if website is None:
            if number:
                asyncio.create_task(notify_tele_phone_numbers(company['displayName']['text'], number, session))

        return False

    cache = load_cache(cache_expiry, cache_file)
    if cache:
        return

    check_phone_and_website()

    try:
        async with session.get(company['websiteUri']) as rsp:
            if rsp.status == 200:
                company_html = await rsp.text()

                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, company_html)
                email_domains = ['.co.uk', '.com']

                emails = list(set(email for email in emails if any(domain in email for domain in email_domains)))
                if emails:
                    for email in emails:
                        save_cache(email, cache_file)
                        yield email

    except Exception as e:
        print(f"Failed to fetch details for '{company['displayName']['text']}': {str(e)}")


async def send_email(recipient):
    try:
        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = recipient
        em['Subject'] = 'sorry'
        em.set_content('***')

        await aiosmtplib.send(em, hostname='smtp.gmail.com', username=email_sender, password=email_password, port=465, use_tls=True)

        print("Email sent successfully")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False


async def outreach_to_company(session, company):
    async for email in get_company_details(session, company):
        await send_email(email)
        await asyncio.sleep(10)


async def main():
    industries = ['restaurants', 'barbers', 'cafes', 'gyms']

    async with aiohttp.ClientSession() as session:
        for industry in industries:
            next_page_token = None
            while True:
                companies = get_companies(industry, next_page_token)
                if not companies or 'places' not in companies:
                    print('Nothing to scrape')
                    break

                tasks = [outreach_to_company(session, company) for company in companies['places']]
                print(tasks)
                await asyncio.gather(*tasks)

                if 'nextPageToken' not in companies:
                    print('No nextPageToken')
                    break

                next_page_token = companies['nextPageToken']
                await asyncio.sleep(10)

        await notify_tele_complete(session)


if __name__ == '__main__':
    asyncio.run(main())
