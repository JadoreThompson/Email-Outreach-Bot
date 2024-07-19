from bs4 import BeautifulSoup
import requests
import re

url = "https://lovesaffronstreet.com/"
rsp = requests.get(url)
text = rsp.text

email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
emails = re.findall(email_pattern, text)
email_domains = ['.com', 'co.uk']
emails = list(set(email for email in emails if any(domain in email for domain in email_domains)))
print(emails)


# email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
# print(email_pattern)
