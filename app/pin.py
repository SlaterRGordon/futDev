import json
import re
import time
from datetime import datetime
from random import random

import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip,deflate,sdch, br',
    'Accept-Language': 'en-US,en;q=0.8',
    'DNT': '1',
}

class Pin(object):
    def __init__(self, sku=None, sid='', nucleusId=0, personaId='', dob=False, platform=False):
        self.sid = sid
        self.nucleusId = nucleusId
        self.personaId = personaId
        self.dob = dob
        self.platform = platform

        self.taxv = '1.1'
        self.tidt = 'easku'
        rc = requests.get('https://www.easports.com/fifa/ultimate-team/web-app/config/config.json').json()

        self.sku = 'FUT20WEB'
        self.rel = rc['releaseType']
        self.gid = 0
        self.plat = 'web'
        self.et = 'client'
        self.pidt = 'persona'
        self.v = '20.4.2'

        self.r = requests.Session()
        self.r.headers = headers
        self.r.headers['Origin'] = 'https://www.easports.com'
        self.r.headers['Referer'] = 'https://www.easports.com/fifa/ultimate-team/web-app/'
        self.r.headers['x-ea-game-id'] = self.sku
        self.r.headers['x-ea-game-id-type'] = self.tidt
        self.r.headers['x-ea-taxv'] = self.taxv

        self.custom = {"networkAccess": "G"}  # wifi?
        # TODO?: full boot process when there is no session (boot start)

        self.custom['service_plat'] = platform[:3]
        self.s = 2  # event id  |  before "was sent" without session/persona/nucleus id so we can probably omit

    def __ts(self):
        # TODO: add ability to random something
        ts = datetime.utcnow()
        ts = ts.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        return ts

    def event(self, en, pgid=False, status=False, source=False, endReason=False):  # type=False
        data = {
            "core": {
                "en": en,
                "pid": self.personaId,
                "pidm": {"nucleus": self.nucleusId},
                "pidt": self.pidt,
                "s": self.s,
                "ts_event": self.__ts()
            }
        }
        if self.dob:
            data['core']['dob'] = self.dob
        if pgid:
            data['pgid'] = pgid
        if status:
            data['status'] = status
        if source:
            data['source'] = source
        if endReason:
            data['endReason'] = endReason

        if en == 'login':
            data['type'] = 'utas'
            data['userid'] = self.personaId
        elif en == 'page_view':
            data['type'] = 'menu'
        elif en == 'error':
            data['server_type'] = 'utas'
            data['errid'] = 'server_error'
            data['type'] = 'disconnect'
            data['sid'] = self.sid

        self.s += 1

        return data

    def send(self, events, fast=False):
        time.sleep(0.5 + random() / 50)
        data = {
            "custom": self.custom,
            "et": self.et,
            "events": events,
            "gid": self.gid,
            "is_sess": self.sid != '',
            "loc": "en_US",
            "plat": self.plat,
            "rel": self.rel,
            "sid": self.sid,
            "taxv": self.taxv,
            "tid": self.sku,
            "tidt": self.tidt,
            "ts_post": self.__ts(),
            "v": self.v
        }
        # print(data)  # DEBUG
        rc = requests.get('https://www.easports.com/fifa/ultimate-team/web-app/config/config.json').json()
        pinUrl = rc['pinURL']
        print(pinUrl)
        if not fast:
            self.r.options(pinUrl)
        rc = self.r.post(pinUrl, data=json.dumps(data)).json()
        if rc['status'] != 'ok':
            raise FutError('PinEvent is NOT OK, probably they changed something.')
        return True