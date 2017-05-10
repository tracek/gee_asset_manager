import sys
import requests
from bs4 import BeautifulSoup

if sys.version_info > (3, 0):
    from urllib.parse import unquote
else:
    from urllib import unquote

google_accounts_url = 'https://accounts.google.com'
authentication_url = 'https://accounts.google.com/ServiceLoginAuth'

session = requests.session()

login_html = session.get(google_accounts_url)
soup_login = BeautifulSoup(login_html.content, 'html.parser').find('form').find_all('input')
payload = {}
for u in soup_login:
    if u.has_attr('value'):
        payload[u['name']] = u['value']

payload['Email'] = raw_input("Enter your email: ")
payload['Passwd'] = raw_input("Enter your password (WARNING! GOES IN CLEAR TEXT!!!): ")

auto = login_html.headers.get('X-Auto-Login')
follow_up = unquote(unquote(auto)).split('continue=')[-1]
galx = login_html.cookies['GALX']

payload['continue'] = follow_up
payload['GALX'] = galx

session.post(authentication_url, data=payload)

_ = session.get('https://ee-api.appspot.com/assets/upload/geturl?')
r = session.get('https://ee-api.appspot.com/assets/upload/geturl?')

print(r.text)