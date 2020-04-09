import requests

rc = requests.get('https://www.easports.com/fifa/ultimate-team/web-app/config/config.json').json()
authUrl = rc['authURL']
pinUrl = rc['pinURL']
clientId = rc['eadpClientId']
releaseType = rc['releaseType']
funCaptchaPublicKey = rc['funCaptchaPublicKey']

rc = requests.get('https://www.easports.com/fifa/ultimate-team/web-app/content/7D49A6B1-760B-4491-B10C-167FBC81D58A/2019/fut/config/companion/remoteConfig.json').json()
if rc['pin'] != {"b": True, "bf": 500, "bs": 10, "e": True, "r": 3, "rf": 300}:
    print('>>> WARNING: ping variables changed: %s' % rc['pin'])
if rc['futweb_maintenance']:
    print('Futweb maintenance, please retry in few minutes.')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip,deflate,sdch, br',
    'Accept-Language': 'en-US,en;q=0.8',
    'DNT': '1',
}

