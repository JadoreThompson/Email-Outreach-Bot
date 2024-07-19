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

load_dotenv('.env')
api_key = os.getenv('API_KEY')
url = "https://places.googleapis.com/v1/places:searchText"
header = {
    'X-Goog-Api-Key': api_key,
    'X-Goog-FieldMask': 'places.displayName,places.name,places.id,places.websiteUri,places.nationalPhoneNumber,places.rating,nextPageToken',
    'Content-Type': 'application/json'
}
email_sender =os.getenv('EMAIL_SENDER')
email_password = os.getenv('EMAIL_PASSWORD')


async def get_companies(next_page_token):
    global payload

    payload = {
        'textQuery': 'Restaurants',
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
        rsp = requests.post(url, headers=header, data=json.dumps(payload))
        print(json.dumps(rsp.json(), indent=4))
        return rsp.json()

    else:
        rsp = requests.post(url, headers=header, data=json.dumps(payload))
        print(json.dumps(rsp.json(), indent=4))
        return rsp.json()


async def get_emails(companies):
    for company in companies['places']:
        try:
            rsp = requests.get(company['websiteUri'])
            if rsp.status_code == 200:
                text = rsp.text

                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text)
                email_domains = ['.co.uk', '.com']

                emails = list(set(email for email in emails if any(domain in email for domain in email_domains)))
                if emails:
                    for email in emails:
                        yield email
                else:
                    print(f"No emails found for '{company}'")
                    continue

            else:
                print(f"Error fetching site for '{company}'")
                continue
        except Exception as e:
            print(f"Error fetching emails for '{company}': {str(e)}")


async def send_emails(host_email, recipient_email):
    email = Email(
        email_sender=os.getenv('EMAIL_SENDER'),
        email_password=os.getenv('EMAIL_PASSWORD'),
        email_recipient=recipient_email,
        body='Sorry wrong email address',
        subject='Accident'
    )

    try:
        em = EmailMessage()
        em['From'] = host_email
        em['To'] = email.email_recipient
        em['Subject'] = email.subject
        em.set_content(email.body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(host_email, email_password)
            server.sendmail(host_email, email.email_recipient, em.as_string())

        time.sleep(300)
        print("Email sent successfully")
        return True

    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False




async def main():
    next_page_token = None
    while True:
        companies = await get_companies(next_page_token)
        if 'places' not in companies:
            print("No more pages to fetch")
            break

        async for email in get_emails(companies):
            outcome = await send_emails(email_sender, email)
            if outcome:
                print("Successful send")
            else:
                print("Failed to send")

        if 'nextPageToken' not in companies:
            print("No more pages to fetch.")
            break

        next_page_token = companies['nextPageToken']
        print("Sleeping for 5 minutes...")


if __name__ == '__main__':
    asyncio.run(main())
