import requests, pickle
import urllib
from urlparse import urlparse
import json
import re
import time
from static import headers

def getPrice(itemId):
    rc = requests.get('https://www.futbin.com/20/playerPrices', params={'player': str(itemId)})
    
    try:
        print('got futbin price')
        rc = rc.json()
    except:
        print('something went wrong getting futbin price')

    rc = rc[str(itemId)]['prices']
    if isinstance(rc['ps']['LCPrice'], basestring):
        rc['ps']['LCPrice'] = rc['ps']['LCPrice'].replace(',', '')

    print(int(rc['ps']['LCPrice']))

    return int(rc['ps']['LCPrice'])