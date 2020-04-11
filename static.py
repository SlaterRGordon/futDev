
import requests
import json

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'DNT': '1',
    'Host': 'accounts.ea.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
    'Referer': 'https://www.easports.com/fifa/ultimate-team/web-app/'
}

rc = requests.get('https://www.easports.com/fifa/ultimate-team/web-app/config/config.json').json()
authUrl = rc['authURL']
pinUrl = rc['pinURL']
clientId = rc['eadpClientId']
releaseType = rc['releaseType']
funCaptchaPublicKey = rc['funCaptchaPublicKey']