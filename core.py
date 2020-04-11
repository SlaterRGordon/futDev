import requests, pickle
import urllib
from urlparse import urlparse
import json
import re
import time
from static import headers
from pin import Pin
count = 0

class Core(object):
    def __init__(self, email, password):
        """ Initialization """
        self.clientId = 'FIFA-20-WEBCLIENT'
        self.gameSku = 'FFA20PS4'
        self.sku = 'FUT20WEB'
        self.skuB = 'FFT20'
        self.gameUrl = 'ut/game/fifa20'
        self.futHost = 'utas.external.s2.fut.ea.com:443'
        self.__login__(email, password)
        self.__launch__(email, password)

    def __login__(self, email, password):
        """ Logs in and stores the access token """

        self.r = requests.Session()
        self.r.headers
        
        params = {
            'prompt': 'login',
            'accessToken': '',
            'client_id': 'FIFA-20-WEBCLIENT',
            'response_type': 'token',
            'display': 'web2/login',
            'locale': 'en_US',
            'redirect_uri': 'https://www.easports.com/fifa/ultimate-team/web-app/auth.html',
            'release_type': 'prod',
            'scope': 'basic.identity offline signin basic.entitlement basic.persona',
        }
        rc = self.r.get('https://accounts.ea.com/connect/auth', params=params, timeout=15)
        self.r.headers['Referer'] = rc.url

        data = {
            'email': email,
            'password': password,
            'pn_text': '',
            'passwordForPhone': '',
            'country': 'CA',
            'phoneNumber': '', 
            '_rememberMe': 'on',
            'rememberMe': 'on',
            '_eventId': 'submit',
            'gCaptchaResponse': '',
            'isPhoneNumberLogin': 'false',
            'isIncompletePhone': ''
        }
        rc = self.r.post(rc.url, data=data, timeout=15)

        if "'successfulLogin': false" in rc.text:
            print('unsuccessful login')

        if 'var redirectUri' in rc.text:
            rc = self.r.get(rc.url, params={'_eventId': 'end'})

        if 'FIFA Ultimate Team</strong> needs to update your Account to help protect your gameplay experience.' in rc.text:
            print("need to update account")
            self.r.headers['Referer'] = rc.url
            rc = self.r.post(rc.url.replace('s2', 's3'), {'_eventId': 'submit'}, timeout=15).content
            self.r.headers['Referer'] = rc.url
            rc = self.r.post(rc.url, {'twofactorType': 'EMAIL', 'country': 0, 'phoneNumber': '', '_eventId': 'submit'}, timeout=15)

        if 'Login Verification' in rc.text:
            print('Needs to be verified')

            data = {
                'codeType': 'EMAIL',
                '_eventId': 'submit'
            }
            rc = self.r.post(rc.url, data=data, timeout=15)

            while 'Too many attempts, retry in a few minutes' in rc.text:
                print('too many attempts will retry in 4 minutes')
                time.sleep(240)
                return self.__login__(email, password)
            
            if 'Enter your security code' in rc.text:
                code = input('Enter code: ')

                self.r.headers['Referer'] = rc.url
                rc = self.r.post(rc.url.replace('s3', 's4'), {'oneTimeCode': code, '_trustThisDevice': 'on', '_eventId': 'submit'}, timeout=15)
        
        print(rc.url)

        rc = re.match('https://www.easports.com/fifa/ultimate-team/web-app/auth.html#access_token=(.+?)&token_type=(.+?)&expires_in=[0-9]+', rc.url)
        if rc.group(1) and rc.group(2):
            self.accessToken = rc.group(1)
            self.tokenType = rc.group(2)
        else:
            print('couldn\'t find access token retrying login')
            return self.__login__(email, password)

    def __launch__(self, email, password):
        """ Accesses fut web application """
        
        self.r.headers = headers

        params = {
            'response_type': 'token',
            'redirect_uri': 'nucleus:rest',
            'prompt': 'none',
            'client_id': 'ORIGIN_JS_SDK'
        }
        rc = self.r.get('https://accounts.ea.com/connect/auth', params=params, timeout=15).json()
        self.accessToken = rc['access_token']
        self.tokenType = rc['token_type']

        self.r.headers['Referer'] = 'https://www.easports.com/fifa/ultimate-team/web-app/'
        self.r.headers['Accept'] = 'application/json'
        self.r.headers['Authorization'] = '%s %s' % (self.tokenType, self.accessToken)
        rc = self.r.get('https://gateway.ea.com/proxy/identity/pids/me').json()
        if rc.get('error') == 'invalid_access_token':
            print('invalid token')
        self.pidId = rc['pid']['externalRefValue']
        self.dob = rc['pid']['dob']
        

        del self.r.headers['Authorization']
        self.r.headers['Easw-Session-Data-Nucleus-Id'] = self.pidId
        params = {
            'filterConsoleLogin': 'true',
            'sku': self.sku,
            'returningUserGameYear': '2019'
        }
        rc = self.r.get('https://%s/%s/user/accountinfo' % (self.futHost, self.gameUrl), params=params).json()
        personas = rc['userAccountInfo']['personas']
        for p in personas:
            for c in p['userClubList']:
                if c['skuAccessList'] and self.gameSku in c['skuAccessList']:
                    self.personaId = p['personaId']
                    break
        if not hasattr(self, 'personaId'):
            print('error during launch, no persona found')
            self.__login__(email, password)
            return self.__launch__(email, password)

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
        self.authCode = rc['code']

        self.r.headers['Content-Type'] = 'application/json'
        data = {
            'isReadOnly': 'false',
            'sku': self.sku,
            'clientVersion': 1,
            'locale': 'en-US',
            'method': 'authCode',
            'priorityLevel': 4,
            'identification': {
                'authCode': self.authCode,
                'redirectUrl': 'nucleus:rest'
            },
            'authCode': self.authCode,
            'redirectUrl': 'nucleus:rest',
            'nucleusPersonaId': self.personaId,
            'gameSku': self.gameSku
        }
        rc = self.r.post('https://%s/ut/auth' % self.futHost, data=json.dumps(data), timeout=15)
        if rc.status_code == 401:
            print('multiple session')
        if rc.status_code == 500:
            print('Servers are probably temporary down.')
        
        rc = rc.json()
        self.r.headers['X-UT-SID'] = self.sid = rc['sid']

        self.r.headers['Easw-Session-Data-Nucleus-Id'] = self.pidId
        rc = self.r.get('https://%s/%s/phishing/question' % (self.futHost, self.gameUrl), timeout=15).json()
        if rc['code'] == 458:
            print('captcha to solve...')
        if rc['string'] != 'Already answered question' and rc['string'] != 'Feature Disabled':
            print('needs phishing token...')

        self.pin = Pin(pidId=self.pidId, personaId=self.personaId, dob=self.dob[:-3], sid=self.sid)
        events = [self.pin.event('login', status='success')]
        self.pin.send(events)

        events = [self.pin.event('page_view', 'Hub - Home')]
        self.pin.send(events)

    def __request__(self, method, url, data=None, params=None):
        """ Sends request and returns response in json format """

        global count
        print(count)
        if count == 30:
            time.sleep(240)
            count = 0

        data = data or {}
        params = params or {}
        url = 'https://%s/%s/%s' % (self.futHost, self.gameUrl, url)
        self.r.options(url, params=params)

        time.sleep(6)

        if method.upper() == 'GET':
            rc = self.r.get(url, data=data, params=params, timeout=15)
        elif method.upper() == 'POST':
            rc = self.r.post(url, data=data, params=params, timeout=15)
        elif method.upper() == 'PUT':
            print('request about to send')
            print(self.r.headers)
            rc = self.r.put(url, data=data, params=params, timeout=15)
            print('request sent')
            print(rc.url)
            print(data)
            print(params)
            print(rc.headers)
            print(rc.status_code)
            print(rc.cookies)
            print(rc.content)
        elif method.upper() == 'DELETE':
            rc = self.r.delete(url, data=data, params=params, timeout=15)

        
        if url == 'sbs/challenge/629/squad':
            print('request sent')
            print(rc.content)

        if not rc.ok:
            if rc.status_code == 401:
                print('expired session')
            elif rc.status_code == 409:
                print('conflict')
            elif rc.status_code == 426 or rc.status_code == 429:
                print('too many requests')
            elif rc.status_code == 458:
                print('error, logging out')
            elif rc.status_code == 460 or rc.status_code == 461:
                print('permission denied')
            elif rc.status_code == 494:
                print('market locked')
            elif rc.status_code in (512, 521):
                print('512/521 Temporary ban or just too many requests.')
            elif rc.status_code == 478:
                print('no trade existing error')
            else:
                print('some error')

        if rc.text == '':
            return {}
        else:
            print('has text')
            print(rc.json())
            return rc.json()

    def bronzePackMethod(self):
        """ opens bronze packs and sells items """

        # TODO: - I need to make it check transfer list size to make sure isn't full
        #       - Add other leagues to clear() and send to tradepile
        #       - create method that finds price

        rc = self.unassigned()

        if rc != {}:
            print('clearing unassigned items')
            self.clear(rc)
        
        rc = self.buyPack(100)

        if rc != {}:
            print('clearing pack items')
            self.clear(rc)
        else:
            rc = self.unassigned()
            self.clear(rc)

    def buyPack(self, packId):
        """ opens a pack """

        method = 'POST'
        url = 'purchased/items'

        events = [self.pin.event('page_view', 'Hub - Store')]
        self.pin.send(events)

        data = {
            'packId': 100,
            'currency': 'COINS'
        }
        rc = self.__request__(method, url, data=json.dumps(data))

        return rc

    def addToSbc(self, leagueId, clubId, itemId, setId):
        """ adds player to league sbc """

        # TODO: check if sbc is full ? tradepile : add
        method = 'GET'
        url = 'sbs/sets'
        rc = self.__request__(method, url)
        events = [self.pin.event('page_view', 'Hub - SBC')]
        self.pin.send(events)

        url = 'sbs/setId/%s/challenges' % setId
        rc = self.__request__(method, url)
        events = [self.pin.event('page_view', 'SBC - Challenges')]
        self.pin.send(events)

        challengeId = ''
        for challenge in rc['challenges']:
            for item in challenge['elgReq']:
                if item['type'] == 'CLUB_ID':
                    if item['eligibilityValue'] == clubId:
                        print('same club')
                        challengeId = challenge['challengeId']
                    break
            if challengeId != '':
                print(challengeId)
                break
   
        if challengeId != '':
            method = 'GET'
            url = 'sbs/challenge/%s/squad' % challengeId
            print(url)
            rc = self.__request__(method, url)

            if not ('squad' in rc):
                print('starting challenge')
                method = 'POST'
                url = 'sbs/challenge/%s' % challengeId
                rc = self.__request__(method, url)
                method = 'GET'
                url = 'sbs/challenge/%s/squad' % challengeId
                rc = self.__request__(method, url)


            events = [self.pin.event('page_view', 'SBC - Squad')]
            self.pin.send(events)

            n = 0
            moved = False
            players = []
            for item in rc['squad']['players']:
                if item['itemData']['id'] == itemId:
                    print('item already in sbc, sending to tradepile')
                    self.sendToPile('trade', itemId)
                    return
                if item['itemData']['id'] == 0 and not moved:
                    print('item has now been moved')
                    print(itemId)
                    item['itemData']['id'] = itemId
                    moved = True
                
                if item['itemData']['id'] == 0:
                    players.append({"index": n, "itemData": {"id": str(item['itemData']['id']), "dream": False}})
                else:
                    players.append({"index": n, "itemData": {"id": str(item['itemData']['id']), "dream": False}})

                
                n += 1

            data = {'players': players}
            method = 'PUT'

            print(data)

            if not moved:
                print('sbc full, sending to tradepile')
                self.sendToPile('trade', itemId)
            else:
                print('added to sbc')
                self.__request__(method, url, data=json.dumps(data))

    def autoSnipe(self):
        """ tries to snipe a certain query """

        # TODO: Needs a buyItem(self, ...etc) method
        # TODO: Needs to determine how often to send request (any other ways to make undetectable?)  

    def unassigned(self):
        """ Returns unassigned items """

        method = 'GET'
        url = 'purchased/items'

        rc = self.__request__(method, url)

        events = [self.pin.event('page_view', 'Unassigned Items - List View')]
        if rc.get('itemData'):
            events.append(self.pin.event('page_view', 'Item - Detail View'))
        self.pin.send(events)

        return rc

    def tradepile(self):
        """ Returns items from trade pile """

        method = 'GET'
        url = 'tradepile'

        rc = self.__request__(method, url)

        events = [self.pin.event('page_view', 'Hub - Transfers'), self.pin.event('page_view', 'Transfer List - List View')]
        if rc.get('auctionInfo'):
            events.append(self.pin.event('page_view', 'Item - Detail View'))
        self.pin.send(events)

        return rc

    def clear(self, rc):
        """ Deals with unassigned items """

        if 'itemList' in rc:
            listName = 'itemList'
        elif 'itemData' in rc:
            listName = 'itemData'
        else:
            print('why tf is u here bro!!!')
            self.bronzePackMethod()

        for item in rc[listName]:
            if item['itemType'] == 'player':
                if item['leagueId'] == 16: # ligue1
                    print('adding ligue1 player to sbc')
                    self.sendToPile('club', item['id'])
                    self.addToSbc(item['leagueId'], item['teamid'], item['id'], 116)
                elif item['leagueId'] == 13: # prem
                    print('adding prem player to sbc')
                    self.sendToPile('club', item['id'])
                    self.addToSbc(item['leagueId'], item['teamid'], item['id'], 262)
                elif item['leagueId'] == 19: # bundes 
                    print('adding bundes player to sbc')
                    self.sendToPile('club', item['id'])
                    self.addToSbc(item['leagueId'], item['teamid'], item['id'], 95)
                elif item['leagueId'] == 53: # la liga
                    print('adding la liga player to sbc')
                    self.sendToPile('club', item['id'])
                    self.addToSbc(item['leagueId'], item['teamid'], item['id'], 367)
                elif item['leagueId'] == 31: # serie a
                    print('adding serieA player to sbc')
                    self.sendToPile('club', item['id'])
                    self.addToSbc(item['leagueId'], item['teamid'], item['id'], 156)
                elif item['leagueId'] == 39: # mls
                    print('adding mls player to sbc')
                    self.sendToPile('club', item['id'])
                    self.addToSbc(item['leagueId'], item['teamid'], item['id'], 149)
                elif item['rareflag'] == 52:
                    print('sending carnibal player to tradepile')
                    self.sendToPile('trade', item['id'])
                else:
                    print('quick selling player')
                    self.quickSell(item['id'])
                continue
            elif 'resourceId' in item:
                if item['resourceId'] == 5002004:
                    print('sending squad fitness to trade pile')
                    self.sendToPile('trade', item['id'])
                    continue
            elif 'name' in item:
                if item['name'] == 'FreeCredits':
                    print('redeeming free coins')
                    self.redeem(item['id'])
                    continue
                else:
                    print(item['name'])
            
            print('quick selling item')
            self.quickSell(item['id'])

    def tradepileClear(self):
        """ Removes all sold items from tradepile """
        
        method = 'DELETE'
        url = 'trade/sold'

        self.__request__(method, url)

    def quickSell(self, itemId):
        """ Quick sells items """

        method = 'DELETE'
        url = 'item'

        if not isinstance(itemId, (list, tuple)):
            itemId = (itemId,)
        itemId = (str(i) for i in itemId)
        params = {'itemIds': ','.join(itemId)}

        self.__request__(method, url, params=params)

    def sendToPile(self, pile, itemId=None):
        """ Sends item to pile """

        method = 'PUT'
        url = 'item'

        if not isinstance(itemId, (list, tuple)):
            itemId = (itemId,)
        data = {"itemData": [{'pile': pile, 'id': str(i)} for i in itemId]}

        rc = self.__request__(method, url, data=json.dumps(data))

        if rc['itemData'][0]['success']:
            print('moved to %s pile' % pile)
        else:
            print('couldn\'t be moved to %s pile because %s' % pile, rc['itemData'][0]['reason'])

        return rc['itemData'][0]['success']

    

    

        

        