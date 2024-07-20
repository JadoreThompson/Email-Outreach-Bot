import pickle

import os
from dotenv import load_dotenv

import json

import requests
import aiohttp
from bs4 import BeautifulSoup

import re

import asyncio

import smtplib
from email.message import EmailMessage
import ssl

from models import Email
from typing import List, Optional

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

tele_link = "https://t.me/nexifysolutions_bot"
tele_api_key = os.getenv('TELE_API_KEY')
base_url = f"https://api.telegram.org/bot{tele_api_key}/"


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


def get_company_details(company):
    cache_file = f"{company['displayName']['text']}.pkl"
    cache_expiry = timedelta(hours=720)

    def save_cache(email):
        with open(cache_file, 'wb') as f:
            pickle.dump({'timestamp': datetime.now(), 'data': email}, f)

    def load_cache():
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                cache = pickle.load(f)
            if datetime.now() - cache['timestamp'] < cache_expiry:
                return True
        return False

    def check_phone_and_website():
        number = company.get('nationalPhoneNumber')
        website = company.get('websiteUri')

        if website:
            return True

        if website is None:
            if number:
                notify_tele_phone_numbers(company['displayName']['text'], number)

        return False

    if load_cache():
        return False

    check_phone_and_website()

    try:
        rsp = requests.get(url)
        if rsp.status_code == 200:
            company_html = rsp.text

            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, company_html)
            email_domains = ['.co.uk', '.com']

            emails = list(set(email for email in emails if any(domain in email for domain in email_domains)))
            if emails:
                for email in emails:
                    save_cache(email)
                    yield email

            print(json.dumps(company, indent=4))

    except Exception as e:
        print(f"Failed to fetch details for '{company['displayName']['text']}': {str(e)}")
        return False


def send_email(recipient):
    try:
        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = recipient
        em['Subject'] = 'sorry'
        em.set_content('***')

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(email_sender, email_password)
            server.sendmail(email_sender, recipient, em.as_string())

        print("Email sent successfully")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False


def main():
    # industries = [
    #     'restaurants',
    #     'barbers',
    #     'cafes'
    # ]

    industries = ['planes']
    for industry in industries:
        next_page_token = None
        while True:
            companies = get_companies(industry, next_page_token)
            if not companies or 'places' not in companies:
                print('Nothing to scrape')
                break
            for company in companies['places']:
                for email in get_company_details(company):
                    send_email(email)
                    time.sleep(10)

            # after it's all done then check if we can go next page
            if 'nextPageToken' not in companies:
                print('No nextPageToken')
                break

            next_page_token = companies['nextPageToken']
            time.sleep(10)

    notify_tele_complete('Scraping completed')


if __name__ == '__main__':
    main()
