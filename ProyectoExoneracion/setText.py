import requests
from bs4 import BeautifulSoup as bs


def get_login_token(raw_resp):
    soup = bs(raw_resp.text, 'lxml')
    token = [n['value'] for n in soup.find_all('input')
             if n['name'] == 'formPrincipal:identificacion']
    return token[0]

payload = {
    'cedula': '0102835691',
    'captcha': '1234'
    }

with requests.session() as s:
    resp = s.get('https://www.senescyt.gob.ec/web/guest/consultas')
    payload['wpLoginToken'] = get_login_token(resp)

    response_post = s.post('http://en.wikipedia.org/w/index.php?title=Special:UserLogin&action=submitlogin&type=login',
                           data=payload)
    response = s.get('http://en.wikipedia.org/wiki/Special:Watchlist')