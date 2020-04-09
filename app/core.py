import requests, pickle
import json
import re
import time
from app.urls import headers, authUrl, pinUrl, clientId, releaseType, funCaptchaPublicKey
from app.pin import Pin

endpoint = 'https://utas.external.s2.fut.ea.com/ut/game/fifa20'

class Core(object):
    def __init__(self, email, password):
        self.r = requests.Session()
        self.gameSku = 'FFA20PS4'
        self.sku = 'FUT20WEB'
        self.skuB = 'FFT20'
        self.gameUrl = 'ut/game/fifa20'
        self.futHost = 'utas.external.s2.fut.ea.com:443'
        self.login(email, password)
        self.launch(email, password)

    def login(self, email, password):
        params = {
            'prompt': 'login',
            'accessToken': 'null',
            'client_id': clientId,
            'response_type': 'token',
            'display': 'web2/login',
            'locale': 'en_US',
            'redirect_uri': 'https://www.easports.com/fifa/ultimate-team/web-app/auth.html',
            'release_type': 'prod',
            'scope': 'basic.identity offline signin'
        }
        self.r.headers['Referer'] = 'https://www.easports.com/fifa/ultimate-team/web-app/'
        rc = self.r.get('https://accounts.ea.com/connect/auth', params=params, timeout=15)
        
        
        self.r.headers['Referer'] = rc.url
        data = {
            'email': email,
            'password': password,
            'country': 'CA',
            'phoneNumber': '',
            'passwordForPhone': '',
            'gCaptchaResponse': '',
            'isPhoneNumberLogin': 'false',
            'isIncompletePhone': '',
            '_rememberMe': 'on',
            'rememberMe': 'on',
            '_eventId': 'submit'
        }
        rc = self.r.post(rc.url, data=data, timeout=15)

        if "'successfulLogin': false" in rc.text:
                failedReason = re.search('general-error">\s+<div>\s+<div>\s+(.*)\s.+', rc.text).group(1)
                print(failedReason)

        if 'var redirectUri' in rc.text:
            rc = self.r.get(rc.url, params={'_eventId': 'end'})

        if 'FIFA Ultimate Team</strong> needs to update your Account to help protect your gameplay experience.' in rc:
            print("need to update account")
            self.r.headers['Referer'] = rc.url
            rc = self.r.post(rc.url.replace('s2', 's3'), {'_eventId': 'submit'}, timeout=15).content
            self.r.headers['Referer'] = rc.url
            rc = self.r.post(rc.url, {'twofactorType': 'EMAIL', 'country': 0, 'phoneNumber': '', '_eventId': 'submit'}, timeout=15)

        if 'Login Verification' in rc.text:
            print('Needs Login Verification')
            rc = self.r.post(rc.url, {'_eventId': 'submit', 'codeType': 'EMAIL'})

        if 'Too many attempts, retry in a few minutes' in rc.text:
                print('too many attempts')

        if 'Enter your security code' in rc.text:
            code = input('Enter code: ')

            self.r.headers['Referer'] = url = rc.url
            rc = self.r.post(url.replace('s3', 's4'), {'oneTimeCode': code, '_trustThisDevice': 'on', '_eventId': 'submit'}, timeout=15)

            if 'Incorrect code entered' in rc.text or 'Please enter a valid security code' in rc.text:
                print('wrong code')

        rc = re.match('https://www.easports.com/fifa/ultimate-team/web-app/auth.html#access_token=(.+?)&token_type=(.+?)&expires_in=[0-9]+', rc.url)
        if rc.group(1) and rc.group(2):
            self.accessToken = rc.group(1)
            self.tokenType = rc.group(2)
        else:
            return login(email, password)
        
    def launch(self, email, password):
        params = {
            'accessToken': self.accessToken,
            'client_id': clientId,
            'response_type': 'token',
            'release_type': 'prod',
            'display': 'web2/login',
            'locale': 'en_US',
            'redirect_uri': 'https://www.easports.com/fifa/ultimate-team/web-app/auth.html',
            'scope': 'basic.identity offline signin'
        }
        rc = self.r.get('https://accounts.ea.com/connect/auth', params=params)
        rc = re.match('https://www.easports.com/fifa/ultimate-team/web-app/auth.html#access_token=(.+?)&token_type=(.+?)&expires_in=[0-9]+', rc.url)
        if rc.group(1) and rc.group(2):
            self.accessToken = rc.group(1)
            self.tokenType = rc.group(2)

        rc = self.r.get('https://www.easports.com/fifa/ultimate-team/web-app/', timeout=15).text

        self.r.headers['Referer'] = 'https://www.easports.com/fifa/ultimate-team/web-app/'
        self.r.headers['Accept'] = 'application/json'
        self.r.headers['Authorization'] = '%s %s' % (self.tokenType, self.accessToken)
        rc = self.r.get('https://gateway.ea.com/proxy/identity/pids/me').json()
        if rc.get('error') == 'invalid_access_token':
            print('invalid token')
            self.login(email, password)
            return self.launch(email, password)

        self.nucleusId = rc['pid']['externalRefValue']
        self.dob = rc['pid']['dob']

        del self.r.headers['Authorization']
        self.r.headers['Easw-Session-Data-Nucleus-Id'] = self.nucleusId

        data = {
            'filterConsoleLogin': 'true',
            'sku': self.sku,
            'returningUserGameYear': '2019'
        }
        rc = self.r.get('https://%s/%s/user/accountinfo' % (self.futHost, self.gameUrl), params=data).json()
        personas = rc['userAccountInfo']['personas']
        for p in personas:
            for c in p['userClubList']:
                if c['skuAccessList'] and self.gameSku in c['skuAccessList']:
                    self.personaId = p['personaId']
                    break

        if not hasattr(self, 'personaId'):
            print('no persona found')

        del self.r.headers['Easw-Session-Data-Nucleus-Id']
        self.r.headers['Origin'] = 'http://www.easports.com'

        params = {
            'client_id': 'FOS-SERVER',
            'redirect_uri': 'nucleus:rest',
            'response_type': 'code',
            'access_token': self.accessToken,
            'release_type': 'prod'
        }
        rc = self.r.get('https://accounts.ea.com/connect/auth', params=params).json()
        authCode = rc['code']

        self.r.headers['Content-Type'] = 'application/json'
        data = {
            'isReadOnly': 'false',
            'sku': self.sku,
            'clientVersion': 1,
            'nucleusPersonaId': self.personaId,
            'gameSku': self.gameSku,
            'locale': 'en-US',
            'method': 'authcode',
            'priorityLevel': 4,
            'identification': {
                'authCode': authCode,
                'redirectUrl': 'nucleus:rest'
            }
        }
        rc = self.r.post('https://%s/ut/auth' % self.futHost, data=json.dumps(data), timeout=15)
        if rc.status_code == 401:
            print('multiple session')
        if rc.status_code == 500:
            print('Servers are probably temporary down.')
        rc = rc.json()
        if rc.get('reason'):
            print('reason: ')
            print(rc.get('reason'))

        self.r.headers['X-UT-SID'] = self.sid = rc['sid']
        self.r.headers['Easw-Session-Data-Nucleus-Id'] = self.nucleusId
        rc = self.r.get('https://%s/%s/phishing/question' % (self.futHost, self.gameUrl), timeout=15).json()
        
        self.pin = Pin(sid=self.sid, nucleusId=self.nucleusId, personaId=self.personaId, dob=self.dob[:-3], platform='ps4')
        events = [self.pin.event('login', status='success')]
        self.pin.send(events)

        print('pin sent')

        self._usermassinfo = self.r.get('https://%s/%s/usermassinfo' % (self.futHost, self.gameUrl), timeout=15).json()
        if self._usermassinfo['userInfo']['feature']['trade'] == 0:
            print('Transfer market is probably disabled on this account.')

        events = [self.pin.event('page_view', 'Hub - Home')]
        self.pin.send(events)

    def request(self, method, url, data=None, params=None):    

        data = data or {}
        params = params or {}
        url = 'https://%s/%s/%s' % (self.futHost, self.gameUrl, url)

        time.sleep(3)
        self.r.options(url, params=params)

        if method.upper() == 'GET':
            rc = self.r.get(url, data=data, params=params, timeout=15)
        elif method.upper() == 'POST':
            rc = self.r.post(url, data=data, params=params, timeout=15)
        elif method.upper() == 'PUT':
            rc = self.r.put(url, data=data, params=params, timeout=15)
        elif method.upper() == 'DELETE':
            rc = self.r.delete(url, data=data, params=params, timeout=15)

        if not rc.ok:
            if rc.status_code == 401:
                return 'login'
                print('expired session')
            elif rc.status_code == 409:
                print('conflict')
            elif rc.status_code == 426 or rc.status_code == 429:
                print('too many requests')
            elif rc.status_code == 458:
                print('error, logging out')
                if url != 'https://%s/ut/auth' % self.futHost:
                    events = [self.pin.event('error')]
                    self.pin.send(events)
                    self.r.delete('https://%s/ut/auth' % self.futHost, timeout=15)
            elif rc.status_code == 460 or rc.status_code == 461:
                print('permission denied')
            elif rc.status_code == 494:
                print('market locked')
            elif rc.status_code in (512, 521):
                print('512/521 Temporary ban or just too many requests.')
                time.sleep(360)
                # clearUnused()
                return 'restart'
            elif rc.status_code == 478:
                print('no trade existing error')
            elif rc.status_code == 471:
                # TODO: self.clearUnusedPile()
                print('clear unused')

        if rc.text:
            print(rc.content)
            rc = rc.json()
        else:
            rc = {}

        return rc

    def bronzePackMethod(self):
        rc = self.buyPack()
        if rc == 'restart':
            return self.bronzePackMethod()
        elif rc == 'login':
            self.login('slats1999@gmail.com', '$Logan1992')
            self.launch('slats1999@gmail.com', '$Logan1992')
            return self.bronzePackMethod()

        print('bronzepackmethod')

        if 'itemList' in rc:
            print('in rc')
            for item in rc['itemList']:
                if item['itemType'] == 'player':
                    print('player')
                    print(item['leagueId'])
                    if item['leagueId'] == 16: # ligue1
                        print('adding ligue1 player to sbc')
                        self.addToSbc(item['leagueId'], item['teamid'], item['id'], 116)
                    elif item['leagueId'] == 13: # prem
                        print('adding prem player to sbc')
                        self.addToSbc(item['leagueId'], item['teamid'], item['id'], 262)
                    elif item['leagueId'] == 19: # bundes 
                        print('adding bundes player to sbc')
                        self.addToSbc(item['leagueId'], item['teamid'], item['id'], 95)
                    elif item['leagueId'] == 53: # la liga
                        print('adding la liga player to sbc')
                        self.addToSbc(item['leagueId'], item['teamid'], item['id'], 367)
                    elif item['leagueId'] == 31: # serie a
                        print('adding serieA player to sbc')
                        self.addToSbc(item['leagueId'], item['teamid'], item['id'], 156)
                    elif item['leagueId'] == 39: # mls
                        print('adding mls player to sbc')
                        self.addToSbc(item['leagueId'], item['teamid'], item['id'], 149)
                    elif item['untradeable'] == 'true':
                        self.quickSell(item['id'])
                    elif item['rareflag'] == 52:
                        self.sendTradePile(item['id'])
                    else:
                        self.quickSell(item['id'])
                    continue
                elif 'resourceId' in item:
                    if item['resourceId'] == 5002004:
                        self.sendTradePile(item['id'])
                        continue
                elif 'name' in item:
                    if item['name'] == 'FreeCredits':
                        self.redeem(item['id'])
                        continue
                    else:
                        print(item['name'])
                
                print('not player')
                self.quickSell(item['id'])
        else:
            self.bronzePackMethod()
                    

    def buyPack(self):
        method = 'POST'
        url = 'purchased/items'

        events = [self.pin.event('page_view', 'Hub - Store')]
        self.pin.send(events)

        data = {
            'packId': 100,
            'currency': 'COINS'
        }
        rc = self.request(method, url, data=json.dumps(data))

        return rc

    def sellPlayer(self, id, bid, bin):
        method = 'POST'
        url = 'auctionhouse'

        data = {'buyNowPrice': bin, 'startingBid': bid, 'duration': 3600, 'itemData': {'id': id}}
        rc = self.request(method, url, data=json.dumps(data), params={'sku_b': self.skuB})

    def sendTradePile(self, itemId):
        method = 'PUT'
        url = 'item'

        data = {
            "itemData": [{
                'pile': 'trade', 'id': itemId
            }]
        }

        rc = self.request(method, url, data=json.dumps(data))
        if rc['itemData'][0]['success']:
            print('moved to trade pile')
        else:
            print('not moved')

    def addToSbc(self, leagueId, clubId, itemId, setId):
        print('adding to sbc')
        method = 'GET'
        url = 'sbs/sets'
        rc = self.request(method, url)
        events = [self.pin.event('page_view', 'Hub - SBC')]
        self.pin.send(events)

        url = 'sbs/setId/%s/challenges' % setId
        rc = self.request(method, url)
        events = [self.pin.event('page_view', 'SBC - Challenges')]
        self.pin.send(events)

        print(rc.content)

        challengeId = ''
        for challenge in rc['challenges']:
            print('has challenges')
            for item in challenge['elgReq']:
                if item['type'] == 'CLUB_ID' and item['eligibilityValue'] == clubId:
                    print('same club')
                    challengeId = challenge['challengeId']
                    print(challengeId)

        if challengeId != '':
            print('challengeId: ' + challengeId)
            method = 'GET'
            url = 'sbs/challenge/%s/squad' % challengeId
            rc = self.request(method, url)

            events = [self.pin.event('page_view', 'SBC - Squad')]
            self.pin.send(events)

            n = 0
            players = []

            for item in rc['squad']['players']:
                if item['itemData']['id'] == itemId:
                    print('item already in sbc')
                    return False
                if item['itemData']['id'] == 0:
                    item['itemData']['id'] = itemId
                
                players.append({
                    "index": n,
                    "itemData": {
                        "id": item['itemData']['id'],
                        "dream": False
                    }
                })
                n += 1

            data = {'players': players}
            method = 'PUT'
            rc = self.request(method, url, data=json.dumps(data))

    def quickSell(self, itemId):
        method = 'DELETE'
        url = 'item'

        params = {'itemIds': itemId}

        rc = self.request(method, url, params=params)
        
        print('quick sold')

    def redeem(self, itemId):
        method = 'POST'
        url = 'item/' + itemId

        params = {'apply': []}

        rc = self.request(method, url, params=params)

        print('redeem free coins')

    def unassigned(self):
        """Return Unassigned items (i.e. buyNow items)."""
        method = 'GET'
        url = 'purchased/items'

        rc = self.request(method, url)

        # pinEvents
        events = [self.pin.event('page_view', 'Unassigned Items - List View')]
        if rc.get('itemData'):
                events.append(self.pin.event('page_view', 'Item - Detail View'))
        self.pin.send(events)

        return [itemParse({'itemData': i}) for i in rc.get('itemData', ())]

    def itemParse(self, itemData):
        returnData = {
            'tradeId': itemData.get('tradeId'),
            'buyNowPrice': itemData.get('buyNowPrice'),
            'tradeState': itemData.get('tradeState'),
            'bidState': itemData.get('bidState'),
            'startingBid': itemData.get('startingBid'),
            'id': itemData.get('itemData', {'id': None})['id'] or itemData.get('item', {'id': None})['id'],
            'offers': itemData.get('offers'),
            'currentBid': itemData.get('currentBid'),
            'expires': itemData.get('expires'),  # seconds left
            'sellerEstablished': itemData.get('sellerEstablished'),
            'sellerId': itemData.get('sellerId'),
            'sellerName': itemData.get('sellerName'),
            'watched': itemData.get('watched'),
            'resourceId': itemData.get('resourceId'),  # consumables only?
            'discardValue': itemData.get('discardValue'),  # consumables only?
        }
        return returnData