import os
from dotenv import load_dotenv

import json

import requests
from bs4 import BeautifulSoup

import re

import asyncio


load_dotenv('.env')
api_key = os.getenv('API_KEY')
url = "https://places.googleapis.com/v1/places:searchText"
header = {
    'X-Goog-Api-Key': api_key,
    'X-Goog-FieldMask': 'places.displayName,places.name,places.id,places.websiteUri,places.nationalPhoneNumber,places.rating,nextPageToken',
    'Content-Type': 'application/json'
}


async def get_clients():
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

    rsp = requests.post(url, headers=header, data=json.dumps(payload))

    return rsp.json()


async def get_email(url):
    try:
        rsp = requests.get(url)

        if rsp.status_code == 200:
            text = rsp.text

            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            email_domains = ['.co.uk', '.com']

            emails = list(set(email for email in emails if any(domain in email for domain in email_domains)))
            return emails
        else:
            raise Exception(f'Error fetching email address')

    except Exception as e:
        print(f'Error fetching email: {str(e)}')
        return None


async def get_next_page():
    places = await get_clients()
    if places['nextPageToken']:
        payload['pageToken'] = places['nextPageToken']

        rsp = requests.post(url, headers=header, data=json.dumps(payload))
        print(json.dumps(rsp.json(), indent=4))

        return rsp.json()

    else:
        print('No more pages to fetch')
        return None


if __name__ == '__main__':
    asyncio.run(get_next_page())
