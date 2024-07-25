import google.generativeai as genai

import os
from dotenv import load_dotenv


load_dotenv('.env')

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')


def create_ai_mail(company_name, industry):
    prompt = os.getenv('GEMINI_PROMPT')
    prompt = prompt.replace('{company_name}', company_name).replace('{industry}', industry)
    prompt = prompt.replace('[email]', '').replace('[phone number]', '07532 65414\n07878 942071').replace('[website]', '')

    rsp = model.generate_content(prompt)
    rsp = rsp.text

    return rsp


if __name__ == '__main__':
    create_ai_mail('', '')