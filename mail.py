import spf
import dns

import asyncio
import traceback

import pickle

import os
from dotenv import load_dotenv

import aiohttp
from aiohttp_retry import RetryClient, ExponentialRetry


import aiosmtplib
import psycopg2
from psycopg2 import sql

import json
import requests

import re

import smtplib
from email.message import EmailMessage
import ssl

import time
from datetime import timedelta, datetime


from tele import notify_tele_phone_numbers, notify_tele_complete
from db import conn_params
from ai import create_ai_mail

load_dotenv('.env')

places_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
url = "https://places.googleapis.com/v1/places:searchText"
header = {
    'X-Goog-Api-Key': places_api_key,
    'X-Goog-FieldMask': 'places.displayName,places.name,places.id,places.websiteUri,places.nationalPhoneNumber,places.rating,nextPageToken',
    'Content-Type': 'application/json'
}

email_sender = os.getenv('EMAIL_SENDER')
# email_sender = "sneakyredditpage@gmail.com"

email_password = os.getenv('EMAIL_PASSWORD')
# email_password = "Jadore10@"

tele_api_key = os.getenv('TELE_API_KEY')
base_url = f"https://api.telegram.org/bot{tele_api_key}/"

CACHE_DIR = './cache_collection'
os.makedirs(CACHE_DIR, exist_ok=True)


# Getting list of companies from places API
async def get_companies(industry, session, next_page_token):
    if session is None:
        raise ValueError("Session object is None")

    payload = {
        'textQuery': industry,
        'locationBias': {
            'circle': {
                'center': {'latitude': 51.5416043, 'longitude': 0.0349},
                'radius': 50000.0
            }
        },
        'pageSize': 100
    }

    if next_page_token:
        payload['pageToken'] = next_page_token

    async with session.post(url, headers=header, json=payload) as rsp:
        if rsp.status == 200:
            data = await rsp.json()
            return data
        else:
            print("[GET COMPANIES]: ", rsp.status)


# Infinite looping over all companies within an industry
async def process_industry(industry, session, next_page_token=None):
    all_companies = []

    while True:
        companies = await get_companies(industry, session, next_page_token)
        if 'places' not in companies:
            break

        all_companies.extend(companies['places'])

        if 'nextPageToken' not in companies:
            break

        next_page_token = companies['nextPageToken']

    print("[PROCESS INDUSTRY]: ", all_companies)
    return all_companies


# Getting outreach data points
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

    # def check_phone_and_website():
    #     number = company.get('nationalPhoneNumber')
    #     website = company.get('websiteUri')
    #
    #     if website:
    #         return True
    #
    #     if website is None:
    #         if number:
    #             # Sending telegram a notification that the business has no website but has a +44
    #             asyncio.create_task(notify_tele_phone_numbers(company['displayName']['text'], number, session))
    #
    #     return False

    cache = load_cache(cache_expiry, cache_file)
    if cache:
        return

    # check_phone_and_website()

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


# Outreaching
async def send_email(recipient, company, industry, user_id):
    try:
        company_name = company['displayName']['text'].title()
        calendly_link = "https://calendly.com/quantissol/30min"

        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = recipient
        em['Subject'] = f"Quantis | {company_name}"
        em.set_content(f"Hi {company_name},\n\nWe've worked with businesses like yours to indentify and eliminate inefficiencie. Would you be open to a brief Zoom calll to discuss potential areas for improvement?\n\nIf you're interested select a convient time for you.\n\n{calendly_link}\n\nBest regards,\nQuantis Solutions")
        em.set_content(create_ai_mail(company_name, industry))

        await aiosmtplib.send(em, hostname='smtp.gmail.com', username=email_sender, password=email_password, port=465, use_tls=True)

        print("Email sent successfully")
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                db_query = sql.SQL("""
                    SELECT email FROM users WHERE email = %s;
                """)
                cur.execute(db_query, (user_id, ))
                row = cur.fetchone()
                print("[SEND EMAIL]: ", row)
                if not row:
                    return

                insert_script = sql.SQL("""
                    INSERT INTO sent_mail(recipient, author, b_name, site)
                    VALUES (%s, %s, %s, %s);
                """)
                cur.execute(insert_script, (recipient, row[0], company['displayName']['text'], company['websiteUri']), )

        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False


# Merging the function to get email and send email
async def outreach_to_company(session, company, industry, limit, user_id):
    async for email in get_company_details(session, company):
        await send_email(email, company, industry, user_id)
        time.sleep(1)


async def get_phone_numbers(session, industries):
    phone_leads = []

    for industry in industries:
        print("[PHONE NUMBERS]: ", industry)
        companies = await process_industry(industry, session)
        print("[PHONE NUMBERS]: ", companies)
        for company in companies:
            if 'nationalPhoneNumber' in company and 'websiteUri' not in company:
                print("[PHONE NUMBERS]: ", company['nationalPhoneNumber'])

                phone_leads.append({
                    'company': company['displayName']['text'],
                    'phone': company['nationalPhoneNumber']
                })

    print("[PHONE NUMBERS]: ", phone_leads)
    print("[PHONE NUMBERS]: ", len(phone_leads))
    return phone_leads


async def mail_main(user_id="quantissol@gmail.com"):
    industries = ['barbers', 'gyms', 'salons', 'restaurants', 'retail_stores', 'hotels', 'dental_clinics', 'auto_repair', 'accountants', 'private dental', 'watch dealership']
    next_page_token = None

    timeout = aiohttp.ClientTimeout(total=1000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        retry_options = ExponentialRetry(attempts=3)
        retry_client = RetryClient(client_session=session, retry_options=retry_options)

        phone_leads = await get_phone_numbers(retry_client, industries)
        for lead in phone_leads:
            lead['session'] = session
            await asyncio.create_task(notify_tele_phone_numbers(**lead))
            print(f"[PHONE NUMBERS]: Successfully sent notification for {lead['company']}")
            await asyncio.sleep(5)

        for industry in industries:
            companies = await process_industry(industry, session, next_page_token)
            print("[PROCESS INDUSTRY]: ", companies)

            for company in companies:
                await outreach_to_company(session, company, industry, 4380, user_id)

        await notify_tele_complete(session)


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(mail_main())
    