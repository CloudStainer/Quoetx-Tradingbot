import re
import os
import json
import glob
import pycurl
import certifi
import urllib.parse
from io import BytesIO
from termcolor import colored



COOKIE_DIR = './cookies/'

def gstrb(from_str, to_str, strs, offset=0):
    offset_start = (strs.find(from_str, offset) + len(from_str)) if (offset_start := strs.find(from_str, offset)) != -1 else offset
    offset_end = strs.find(to_str, offset_start) if (offset_end := strs.find(to_str, offset_start)) != -1 else len(strs)
    return strs[offset_start:offset_end]

def curl_headers(custom_headers={}):
    default_headers = {
        'User-Agent': custom_headers.get('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko'),
        'Accept': custom_headers.get('Accept', '*/*'),
        'Accept-Language': custom_headers.get('Accept-Language', 'en-US,en;q=0.5'),
        'Upgrade-Insecure-Requests': custom_headers.get('Upgrade-Insecure-Requests', '1'),
        'Sec-Fetch-Dest': custom_headers.get('Sec-Fetch-Dest', 'document'),
        'Sec-Fetch-Mode': custom_headers.get('Sec-Fetch-Mode', 'navigate'),
        'Sec-Fetch-Site': custom_headers.get('Sec-Fetch-Site', 'same-origin'),
        'Sec-Fetch-User': custom_headers.get('Sec-Fetch-User', '?1'),
        'Priority': custom_headers.get('Priority', 'u=1')
    }

    for key, value in custom_headers.items():
        if key not in default_headers:
            default_headers[key] = value

    return [f'{key}: {value}' for key, value in default_headers.items()]

def curl_setup(params):
    c = pycurl.Curl()
    c.setopt(c.SSL_VERIFYHOST, 2)
    c.setopt(c.SSL_VERIFYPEER, 0)
    c.setopt(c.URL, params.get('url'))
    c.setopt(c.CAINFO, certifi.where())
    c.setopt(c.PROXY, params.get('proxy', ''))
    c.setopt(c.WRITEDATA, params.get('buffer'))
    c.setopt(c.ACCEPT_ENCODING, 'gzip, deflate')
    c.setopt(c.HTTPHEADER, params.get('headers', []))
    cookie_file = f"{COOKIE_DIR}{gstrb('//', '/', params.get('url'))}.txt"
    c.setopt(c.COOKIEJAR, cookie_file)
    c.setopt(c.COOKIEFILE, cookie_file)
    if params.get('postfields'):
        c.setopt(c.POSTFIELDS, params.get('postfields'))
    return c

async def get_data(url, proxy=''):
    buffer = BytesIO()
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    params = {
        'url': url,
        'proxy': proxy,
        'buffer': buffer,
        'headers': curl_headers(headers)
    }
    c = curl_setup(params)
    try:
        c.perform()
    except pycurl.error as e:
        return f'Error: {e}'
    finally:
        c.close()
    return buffer.getvalue().decode('utf-8')

def validate_email(email):
    if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        return True
    return False

def validate_pin_code(pincode):
    if re.match(r'^\d{6}$', pincode):
        return True
    return False

async def get_user_info(proxy=""):
    return await get_data ('https://qxbroker.com/api/v1/cabinets/digest', proxy)

def print_user_info_message(user_info):
    print('\nWelcome back!')
    print('User: ' + colored(user_info['data']['email'], 'blue'))
    print('Country: ' + colored(user_info['data']['countryName'], 'blue'))
    print('Token: ' + colored(user_info['data']['token'], 'blue'))
    print('LiveBalance: ' + colored(user_info['data']['liveBalance'], 'green'))
    print('DemoBalance: ' + colored(user_info['data']['demoBalance'], 'cyan'))

async def login(email='', password='', token='', code='', proxy=''):
    buffer = BytesIO()

    body = {
        '_token': token,
        'email': email,
        'password': password,
        'remember': '1'
    }
    if code:
        body['keep_code'] = '1'
        body['code'] = code

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    }
    if token:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

    params = {
        'url': 'https://qxbroker.com/en/sign-in/',
        'proxy': proxy,
        'buffer': buffer,
        'headers': curl_headers(headers),
    }
    if token:
        params['postfields'] = urllib.parse.urlencode(body)

    c = curl_setup(params)

    try:
        c.perform()
    except pycurl.error as e:
        return f'Error: {e}'
    finally:
        c.close()

    return buffer.getvalue().decode('utf-8')

async def signin(email='', password=''):
    logged = False
    [os.remove(f) for f in glob.glob(f'{COOKIE_DIR}*qxbroker.com.txt')]

    user_info = await get_user_info()
    

    if not logged and '{"message":"Unauthenticated."}' in user_info:
        sign_in_page = await login()
        if '<input type="hidden" name="_token" value="' in sign_in_page:
            token = gstrb ('<input type="hidden" name="_token" value="', '"', sign_in_page)
            sign_in_page = await login(email, password, token)
            if "Please enter the PIN-code we've just sent to your email" in sign_in_page:
                token = gstrb ('<input type="hidden" name="_token" value="', '"', sign_in_page)
                while True:
                    # Prompt for PIN-code
                    code = input("Please enter the PIN-code we've just sent to your email: ")
                    if validate_pin_code(code):
                        break # Exit the loop on valid selection
                    else:
                        print(colored('Invalid 6-digit code.\nPlease enter a valid 6-digit code.', 'yellow'))
                sign_in_page = await login(email, password, token, code)
            user_info = await get_user_info()
            if '{"data":{"' in user_info:
                user_info = json.loads(user_info)
                print_user_info_message(user_info)
                logged = True
    return logged