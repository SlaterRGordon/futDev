import requests, random, urlparse, json, time
from datetime import datetime

from pin import Pin


class Core(object):
    
    """
    STARTING METHODS

    """
    def __init__(self, email, password):
        """ Initialize
        """

        self.email = email
        self.password = password
        
        resp = requests.get('https://www.easports.com/fifa/ultimate-team/web-app/config/config.json').json()
        self.authUrl = resp['authURL']
        self.pinUrl = resp['pinURL']
        self.clientId = resp['eadpClientId']
        self.releaseType = resp['releaseType']

        self.gameUrl = 'ut/game/fifa20'
        self.futHost = 'utas.external.s2.fut.ea.com:443'
        self.clientId = 'FIFA-20-WEBCLIENT'
        self.gameSku = 'FFA20PS4'
        self.sku = 'FUT20WEB'
        self.skuB = 'FFT20'

        self.pack = None
        self.count = 0
        
        self.r = requests.Session()
        self.r.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'accounts.ea.com',
            'Origin': 'https://www.easports.com',
            'Referer': 'https://www.easports.com/fifa/ultimate-team/web-app/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'
        }

        self.login()

    def login(self):
        """ Login 
        """

        params = {
            'prompt': 'login',
            'accessToken': '',
            'client_id': self.clientId,
            'response_type': 'token',
            'display': 'web2/login',
            'locale': 'en_US',
            'redirect_uri': 'https://www.easports.com/fifa/ultimate-team/web-app/auth.html',
            'release_type': 'prod',
            'scope': 'basic.identity offline signin basic.entitlement basic.persona'
        }
        resp = self.r.get('https://accounts.ea.com/connect/auth', params=params)
        self.r.headers['Referer'] = resp.url

        data = {
            'email': self.email,
            'password': self.password,
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
        resp = self.r.post(resp.url, data=data, timeout=15)
        resp = self.r.get(resp.url, params={'_eventId': 'end'}, timeout=15)

        if 'Login Verification' in resp.text:
            data = {
                'codeType': 'EMAIL',
                '_eventId': 'submit'
            }
            resp = self.r.post(resp.url, data=data, timeout=15)
            self.r.headers['Referer'] = resp.url
            
            code = input('Enter code: ')
            data = {
                'oneTimeCode': code,
                '_trustThisDevice': 'on',
                'trustThisDevice': 'on',
                '_eventId': 'submit'
            }
            resp = self.r.post(resp.url, data=data, timeout=15)
            print(resp.url)

        resp = urlparse.parse_qs(urlparse.urlparse(resp.url).fragment)
        self.accessToken = resp['access_token'][0]
        self.tokenType = resp['token_type'][0]

        params = {
            'response_type': 'token',
            'redirect_uri': 'nucleus:rest',
            'prompt': 'none',
            'client_id': 'ORIGIN_JS_SDK'
        }
        self.r.headers['Referer'] = 'https://www.easports.com/fifa/ultimate-team/web-app/'
        resp = self.r.get('https://accounts.ea.com/connect/auth', params=params, timeout=15).json()
        self.accessToken = resp['access_token']
        self.tokenType = resp['token_type']

        self.r.headers['Referer'] = 'https://www.easports.com/fifa/ultimate-team/web-app/'
        self.r.headers['Accept'] = 'application/json'
        self.r.headers['Authorization'] = '%s %s' % (self.tokenType, self.accessToken)
        resp = self.r.get('https://gateway.ea.com/proxy/identity/pids/me').json()
        del self.r.headers['Authorization']

        self.dob = resp['pid']['dob']
        self.r.headers['Easw-Session-Data-Nucleus-Id'] = self.pidId = resp['pid']['externalRefValue']
        params = {
            'filterConsoleLogin': 'true',
            'sku': self.sku,
            'returningUserGameYear': '2019'
        }
        resp = self.r.get('https://%s/%s/user/accountinfo' % (self.futHost, self.gameUrl), params=params, timeout=15).json()
        personas = resp['userAccountInfo']['personas']
        for p in personas:
            for c in p['userClubList']:
                if c['skuAccessList'] and self.gameSku in c['skuAccessList']:
                    self.personaId = p['personaId']
                    break

        params = {
            'client_id': 'FOS-SERVER',
            'redirect_uri': 'nucleus:rest',
            'response_type': 'code',
            'access_token': self.accessToken,
            'release_type': 'prod',
            'client_sequence': 'ut-auth'
        }
        self.r.headers['Content-Type'] = 'application/json'
        resp = self.r.get('https://accounts.ea.com/connect/auth', params=params, timeout=15).json()
        self.authCode = resp['code']

        data = {
            'clientVersion': 1,
            'gameSku': self.gameSku,
            'identification': {
                'authCode': self.authCode,
                'redirectUrl': 'nucleus:rest'
            },
            'authCode': self.authCode,
            'redirectUrl': 'nucleus:rest',
            'isReadOnly': 'false',
            'locale': 'en-US',
            'method': 'authcode',
            'nucleusPersonaId': self.personaId,
            'priorityLevel': 4,
            'sku': self.sku
        }
        resp = self.r.post('https://utas.external.s2.fut.ea.com/ut/auth', data=json.dumps(data), timeout=15).json()
        self.r.headers['X-UT-SID'] = self.sid = resp['sid']
        self.r.headers['Easw-Session-Data-Nucleus-Id'] = self.pidId

        self.pin = Pin(pidId=self.pidId, personaId=self.personaId, dob=self.dob[:-3], sid=self.sid, pinUrl=self.pinUrl)
        events = [self.pin.event('login', status='success')]
        self.pin.send(events)

        events = [self.pin.event('page_view', 'Hub - Home')]
        self.pin.send(events)

    def logout(self):
        """ Logout
        """

        events = [self.pin.event('page_view', 'Settings')]
        self.pin.send(events)
        self.r.delete('https://utas.external.s2.fut.ea.com/ut/auth', timeout=15)


    """
    GENERIC METHODS

    """
    def request(self, method, url, data=None, params=None):
        """ Request
        """

        time.sleep(random.uniform(3,5))

        data = data or {}
        params = params or {}
        url = 'https://%s/%s/%s' % (self.futHost, self.gameUrl, url)

        if method == 'GET':
            resp = self.r.get(url, data=data, params=params, timeout=15)
        elif method == 'POST':
            resp = self.r.post(url, data=data, params=params, timeout=15)
        elif method == 'PUT':
            resp = self.r.put(url, data=data, params=params, timeout=15)
        elif method == 'DELETE':
            resp = self.r.delete(url, data=data, params=params, timeout=15)

        if not resp.ok:
            print(method)
            print(url)
            print(resp.status_code)
            print(resp.url)
            print(resp.content)
            print(params)
            print(data)

        self.count += 1
        if self.count == 90:
            time.sleep(random.uniform(360, 420))
            self.count = 0

        if resp.text != '':
            return resp.json()
        else:
            return {}

    def sendToPile(self, pile, itemId):
        """ Send Item to Pile
        """

        method = 'PUT'
        url = 'item'
        data = {'itemData': [{'id': itemId, 'pile': pile}]}

        resp = self.request(method, url, data=json.dumps(data))

        if resp['itemData'][0]['success']:
            return True
        elif resp['itemData'][0]['reason'] == 'Duplicate Item Type':
            return False
        
        self.tradepile()
        self.clearSold()
        sent = self.sendToPile('trade', itemId)

        return sent

    def club(self, league=None, club=None, start=0, count=91):
        """ Get Club Items
        """

        method = 'GET'
        url = 'club'

        events = [self.pin.event('page_view', 'Hub - Club')]
        self.pin.send(events)

        params = {
            'sort': 'desc',
            'sortBy': 'value',
            'type': 'player',
            'start': start,
            'count': count
        }
        if league:
            params['league'] = league
        if club:
            params['team'] = club

        resp = self.request(method, url, params=params)
        events = [self.pin.event('page_view', 'Club - Players - List View')]
        self.pin.send(events)

        return resp

    def unassigned(self):
        """ Get Unassigned Items
        """

        method = 'GET'
        url = 'purchased/items'

        resp = self.request(method, url)
        events = [self.pin.event('page_view', 'Unassigned Items - List View')]
        self.pin.send(events)

        return resp      

    def openPack(self, packId, preorder=False):
        """ Open Pack
        """

        method = 'POST'
        url = 'purchased/items'
        if preorder:
            data = {'currency': 0, 'packId': packId, 'usePreOrder': True}
        else:
            data = {'currency': 'COINS', 'packId': packId}

        events = [self.pin.event('page_view', 'Hub - Store')]
        self.pin.send(events)
        resp = self.request(method, url, data=json.dumps(data))
        events = [self.pin.event('page_view', 'Unassigned Items - List View'), self.pin.event('page_view', 'Item - Detail View')]
        self.pin.send(events)
        
        return resp

    def redeem(self, itemId):
        """ Redeems Item
        """

        method = 'POST'
        url = 'item/%s' % itemId
        data = {'apply': []}
        self.request(method, url, data=json.dumps(data))

        method = 'GET'
        url = 'user/credits'
        self.request(method, url)

    def quickSell(self, itemIds):
        """ Quicksell Items
        """

        method = 'DELETE'
        url = 'item'

        if not isinstance(itemIds, (list, tuple)):
            itemIds = (itemIds,)
        itemIds = (str(i) for i in itemIds)
        params = {'itemIds': ','.join(itemIds)}

        self.request(method, url, params=params)

        return True

    def toString(self, string):
        """ Format Message
        """

        print('[' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] ' + string)

    """

    AUCTION HOUSE METHODS

    """
    def tradepile(self):
        """ Get Tradepile Items
        """

        method = 'GET'
        url = 'tradepile'

        events = [self.pin.event('page_view', 'Hub - Transfers'), self.pin.event('page_view', 'Transfer List - List View')]
        self.pin.send(events)
        resp = self.request(method, url)
        if 'auctionInfo' in resp:
            events = [self.pin.event('page_view', 'Item - Detail View')]
        self.pin.send(events)

        return resp

    def auction(self, assetId=None, maxBuy=None, maxBid=None, position=None, quality=None, nation=None, league=None, club=None, playStyle=None):
        """ Get Auction Items
        """
        
        method = 'GET'
        url = 'transfermarket'
        params = {
            'start': 0,
            'num': 21,
            'type': 'player'
        }
        if assetId:
            params['maskedDefId'] = assetId
        if maxBuy:
            params['maxb'] = maxBuy
        if maxBid:
            params['macr'] = maxBid
        if position:
            params['pos'] = position
        if quality:
            params['lev'] = quality
        if nation:
            params['nat'] = nation
        if league:
            params['leag'] = league
        if club:
            params['team'] = club
        if playStyle:
            params['playStyle'] = playStyle

        events = [self.pin.event('page_view', 'Hub - Transfers'), self.pin.event('page_view', 'Transfer Market Search')]
        self.pin.send(events)
        resp = self.request(method, url, params=params)
        events = [self.pin.event('page_view', 'Transfer Market Results - List View')]
        self.pin.send(events)

        return resp

    def buy(self, tradeId, buy):
        """ Buy Item on Auction House
        """

        method = 'PUT'
        url = 'trade/%s/bid' % tradeId
        data = {'bid': buy}

        events = [self.pin.event('page_view', 'Hub - Transfers'), self.pin.event('page_view', 'Transfer List - List View')]
        self.pin.send(events)
        resp = self.request(method, url, data=json.dumps(data))

        if 'itemData' in resp:
            return True
        else:
            return False

    def sell(self, itemId, buy, realBid=None, duration=3600):
        """ Sell Item on Auction House
        """

        method = 'POST'
        url = 'auctionhouse'
        
        if buy < 1000:
            buy = buy - (buy % 50)
            bid = buy - 50
        elif buy < 10000:
            buy = buy - (buy % 100)
            bid = buy - 100
            if buy == 1000:
                bid = 950
        elif buy < 50000:
            buy = buy - (buy % 250)
            bid = buy - 250
            if buy == 10000:
                bid = 9900
        elif buy > 50000:
            buy = buy - (buy % 1000)
            bid = buy - 1000
            if buy == 50000:
                bid = 49500

        if realBid:
            bid = realBid

        data = {'buyNowPrice': buy, 'duration': duration, 'itemData': {'id': itemId}, 'startingBid': bid}
        self.request(method, url, data=json.dumps(data))

        return True

    def price(self, assetId):
        """ Get Item Price
        """

        oldBuy = 0
        buy = 0
        while(True):
            if buy == 0:
                resp = self.auction(assetId=assetId)
            else:
                resp = self.auction(assetId=assetId, maxBuy=buy)
            
            count = 0
            if 'auctionInfo' in resp:
                for auction in resp['auctionInfo']:
                    if auction['buyNowPrice'] < buy:
                        buy = auction['buyNowPrice']
                    count += 1

            if count < 3:
                return buy
            elif buy == 200:
                return 199
            
            if oldBuy == buy:
                return buy
            oldBuy = buy          

    def clearSold(self):
        """ Clear Trade Pile
        """

        method = 'DELETE'
        url = 'trade/sold'

        resp = self.request(method, url)

    """

    SBC METHODS

    """
    def getSets(self):
        """ Get Sets
        """

        method = 'GET'
        url = 'sbs/sets'

        events = [self.pin.event('page_view', 'Hub - SBC')]
        self.pin.send(events)
        resp = self.request(method, url)

        return resp    

    def getChallenges(self, setId):
        """ Get Set Challenges
        """

        method = 'GET'
        url = 'sbs/setId/%s/challenges' % setId
        resp = self.request(method, url)

        if len(resp['challenges']) > 1:
            events = [self.pin.event('page_view', 'SBC - Challenges')]
            self.pin.send(events)

        return resp

    def getSquad(self, challengeId, started=True):
        """ Get Challenge Squad
        """

        if started:
            method = 'GET'
            url = 'sbs/challenge/%s/squad' % challengeId
        else:
            method = 'POST'
            url = 'sbs/challenge/%s' % challengeId
        resp = self.request(method, url)

        events = [self.pin.event('page_view', 'SBC Squad Details'), self.pin.event('page_view', 'SBC - Squad')]
        self.pin.send(events)

        return resp

    def addPlayer(self, itemId, setId, challengeId=None, leagueId=None, clubId=None):
        """ Add Player to Challenge Squad
        """

        self.getSets()
        squad = None

        if leagueId and clubId:
            squad, challengeId = self.findChallenge(setId, clubId)
        elif challengeId:
            challenges = self.getChallenges(setId)
            for challenge in challenges['challenges']:
                if challenge['challengeId'] == challengeId:
                    if challenge['status'] == 'IN_PROGRESS':
                        squad = self.getSquad(challengeId)
                    elif challenge['status'] == 'NOT_STARTED':
                        squad = self.getSquad(challengeId, started=False)

        if squad == None:
            return False

        players = []
        moved = False
        count = 0
        for i, player in enumerate(squad['squad']['players']):
            if player['itemData']['id'] == 0 and not moved:
                players.append({'index': i, 'itemData': {'id': itemId, 'dream': 'false'}})
                moved = True
                count += 1
            else:
                players.append({'index': i, 'itemData': {'id': player['itemData']['id'], 'dream': 'false'}})

            if player['itemData']['id'] != 0:
                count += 1
        
        if not moved:
            return False

        method = 'PUT'
        url = 'sbs/challenge/%s/squad' % challengeId
        data = {'players': players}

        if count > 10:
            url = 'sbs/challenge/%s' % challengeId
            params = {'skipUserSquadValidation': False}
            resp = self.request(method, url, params=params)              

        self.request(method, url, data=json.dumps(data))

        return True

    def removePlayer(self, setId, challengeId, itemId):
        """ Remove Player from Challenge Squad
        """

        self.getSets()
        challenges = self.getChallenges(setId)

        for challenge in challenges['challenges']:
            if challenge['challengeId'] == challengeId:
                if challenge['status'] == 'IN_PROGRESS':
                    squad = self.getSquad(challengeId)
                elif challenge['status'] == 'NOT_STARTED':
                    squad = self.getSquad(challengeId, started=False)
                else:
                    return False

        players = []
        for i, player in enumerate(squad['squad']['players']):
            if player['itemData']['id'] == itemId:
                players.append({'index': i, 'itemData': {'id': 0, 'dream': 'false'}})
            else:
                players.append({'index': i, 'itemData': {'id': player['itemData']['id'], 'dream': 'false'}})

        method = 'PUT'
        url = 'sbs/challenge/%s/squad' % challengeId
        data = {'players': players}

        self.request(method, url, data=json.dumps(data))

    def sumbitSquad(self, challengeId):
        """ Submit Challenge Squad
        """

    def findSet(self, leagueId):
        """ Find Player SetId
        """

        leagues = [(13, 262), (16, 116), (31, 156), (53, 367), (19, 95), (39, 149)]
        for league in leagues:
            if league[0] == leagueId:
                return league[1]

        return 0

    def findChallenge(self, setId, clubId):
        """ Find Player ChallengeId
        """

        challenges = self.getChallenges(setId)
        for challenge in challenges['challenges']:
            for item in challenge['elgReq']:
                if item['type'] == 'CLUB_ID':
                    if item['eligibilityValue'] == clubId:
                        challengeId = challenge['challengeId']
                        if challenge['status'] == 'IN_PROGRESS':
                            return self.getSquad(challengeId), challengeId
                        elif challenge['status'] == 'NOT_STARTED':
                            return self.getSquad(challengeId, started=False), challengeId


        return [], challengeId

    def addUpgrade(self, itemId, position, setId=6, challengeId=15):
        """ Add Player to Bronze Upgrade SBC
        """

        positions = [(0, 'GK'), (1, 'LB'), (2, 'CB'), (3, 'CB'), (4, 'RB'), (5, 'CDM'), (6, 'RM'), (7, 'LM'), (8, 'CAM'), (9, 'ST'), (10, 'ST')]
        self.getSets()

        challenges = self.getChallenges(setId)
        for challenge in challenges['challenges']:
            if challenge['status'] == 'IN_PROGRESS':
                squad = self.getSquad(challengeId)
            elif challenge['status'] == 'NOT_STARTED':
                squad = self.getSquad(challengeId, started=False)

        players = []
        moved = False
        count = 0
        for i, player in enumerate(squad['squad']['players']):
            if i < 11:
                if positions[i][1] == position and not moved:
                    if player['itemData']['id'] == 0:
                        players.append({'index': i, 'itemData': {'id': itemId, 'dream': 'false'}})
                        moved = True
                        count += 1
                    else:
                        players.append({'index': i, 'itemData': {'id': player['itemData']['id'], 'dream': 'false'}})
                else:
                        players.append({'index': i, 'itemData': {'id': player['itemData']['id'], 'dream': 'false'}})
            else:
                players.append({'index': i, 'itemData': {'id': 0, 'dream': 'false'}})

            if player['itemData']['id'] != 0:
                count += 1

        if not moved:
            return False
        
        method = 'PUT'
        url = 'sbs/challenge/%s/squad' % challengeId
        data = {'players': players}
        self.request(method, url, data=json.dumps(data))

        if count > 10:
            url = 'sbs/challenge/15'
            params = {'skipUserSquadValidation': False}
            resp = self.request(method, url, params=params)
            if 'grantedSetAwards' in resp:
                self.pack = resp['grantedSetAwards'][0]['value']

        return True

    """
    BRONZE PACK METHODS

    """

    def bronzeMethod(self):
        """ Bronze Pack Method
        """

        discard = []
        unassigned = self.unassigned()

        for item in unassigned['itemData']:
            if item['itemType'] == 'player':
                self.toString('bronzeMethod: Dealing with an Player')
                setId = self.findSet(item['leagueId'])
                self.toString('bronzeMethod: SetId is %s' % setId)
                if setId != 0:
                    sent = self.sendToPile('club', item['id'])
                    self.toString('bronzeMethod: Sent Player to Club : %s' % sent)
                    if not sent:
                        sent = self.sendToPile('trade', item['id'])
                        self.toString('bronzeMethod: Sent Duplicate Player to Tradepile : %s' % sent)
                        if not sent:
                            discard.append(item['id'])
                            self.toString('bronzeMethod: Sent Untradeable Player to Discard : %s' % sent)
                        else:
                            buy = self.price(item['assetId'])
                            if buy > 199 and item['untradeable'] == False:
                                sent = self.sendToPile('trade', item['id'])
                                self.toString('bronzeMethod: Sending Duplicate Player to Tradepile : %s' % sent)
                                if not sent:
                                    discard.append(item['id'])
                                    self.toString('bronzeMethod: Added Duplicate Player to Discard')
                                else:
                                    sold = self.sell(item['id'], buy)
                                    self.toString('bronzeMethod: Selling Duplicate Player for %s : %s' % (buy, sold))
                            elif buy == 0 and item['untradeable'] == False:
                                sent = self.sendToPile('trade', item['id'])
                                self.toString('bronzeMethod: Sending Player to Tradepile : %s' % sent)
                                if not sent:
                                    discard.append(item['id'])
                                    self.toString('bronzeMethod: Sending Untradeable Player to Discard')
                            else:
                                discard.append(item['id'])
                                self.toString('bronzeMethod: Sending Duplicate Player to Discard')
                    else:
                        added = self.addPlayer(item['id'], setId=setId, leagueId=item['leagueId'], clubId=item['teamid'])
                        self.toString('bronzeMethod: Added Player to League %s and Club %s : %s' % (item['leagueId'], item['teamid'], added))
                        if not added:
                            buy = self.price(item['assetId'])
                            if buy > 199 and item['untradeable'] == False:
                                sent = self.sendToPile('trade', item['id'])
                                self.toString('bronzeMethod: Sending Duplicate Player to Tradepile : %s' % sent)
                                if not sent:
                                    discard.append(item['id'])
                                    self.toString('bronzeMethod: Added Duplicate Player to Discard')
                                else:
                                    sold = self.sell(item['id'], buy)
                                    self.toString('bronzeMethod: Selling Duplicate Player for %s : %s' % (buy, sold))
                            elif buy == 0 and item['untradeable'] == False:
                                sent = self.sendToPile('trade', item['id'])
                                self.toString('bronzeMethod: Sending Player to Tradepile : %s' % sent)
                                if not sent:
                                    discard.append(item['id'])
                                    self.toString('bronzeMethod: Sending Untradeable Player to Discard')
                            else:
                                if item['rating'] < 65:
                                    added = self.addUpgrade(item['id'], item['preferredPosition'])
                                    self.toString('bronzeMethod: Adding Player to Bronze Upgrade SBC : %s' % added)
                                elif item['rating'] < 75:
                                    added = self.addUpgrade(item['id'], item['preferredPosition'], 7, 16)
                                    self.toString('bronzeMethod: Adding Player to Silver Upgrade SBC : %s' % added)
                                else:
                                    added = self.addUpgrade(item['id'], item['preferredPosition'], 8, 17)
                                    self.toString('bronzeMethod: Adding Player to Gold Upgrade SBC : %s' % added)

                                if not added:
                                    discard.append(item['id'])
                                    self.toString('bronzeMethod: Sending Untradeable Player to Discard')
                else:
                    self.toString('bronzeMethod: Player Price is')
                    buy = self.price(item['assetId'])
                    self.toString('bronzeMethod: Player Price is %s' % buy)
                    if buy > 199 and item['untradeable'] == False:
                        sent = self.sendToPile('trade', item['id'])
                        self.toString('bronzeMethod: Sending Player to Tradepile : %s' % sent)
                        if not sent:
                            discard.append(item['id'])
                            self.toString('bronzeMethod: Added Player to Discard')
                        else:
                            sold = self.sell(item['id'], buy)
                            self.toString('bronzeMethod: Selling Player for %s : %s' % (buy, sold))
                    elif buy == 0  and item['untradeable'] == False:
                        sent = self.sendToPile('trade', item['id'])
                        self.toString('bronzeMethod: Sending Player to Tradepile : %s' % sent)
                        if not sent:
                            discard.append(item['id'])
                            self.toString('bronzeMethod: Sending Untradeable Player to Discard')
                    else:
                        sent = self.sendToPile('club', item['id'])
                        self.toString('bronzeMethod: Sending Player to Club : %s' % sent)
                        if item['rating'] < 65 and sent:
                            added = self.addUpgrade(item['id'], item['preferredPosition'])
                            self.toString('bronzeMethod: Adding Player to Bronze Upgrade SBC : %s' % added)
                        elif item['rating'] < 75 and sent:
                            added = self.addUpgrade(item['id'], item['preferredPosition'], 7, 16)
                            self.toString('bronzeMethod: Adding Player to Silver Upgrade SBC : %s' % added)
                        elif sent:
                            added = self.addUpgrade(item['id'], item['preferredPosition'], 8, 17)
                            self.toString('bronzeMethod: Adding Player to Gold Upgrade SBC : %s' % added)
                        
                        if not added or not sent:
                            discard.append(item['id'])
                            self.toString('bronzeMethod: Sending Player to Discard')
            elif item['resourceId'] == 5002004:
                sent = self.sendToPile('trade', item['id'])
                self.toString('bronzeMethod: Sending Squad Fitness to Tradepile : %s' % sent)
                if sent:
                    sold = self.sell(item['id'], 1000, realBid=850)
                    self.toString('bronzeMethod: Selling Squad Fitness for 850, 1000 : %s' % sold)
                else:
                    sent = self.sendToPile('club', item['id'])
                    self.toString('bronzeMethod: Selling Squad Fitness for 850, 1000 : %s' % sent)
            elif 'name' in item:
                if item['name'] == 'FreeCredits' or item['name'] == 'FreeBronzePack':
                    self.redeem(item['id'])
                    self.toString('bronzeMethod: Redeemed Free Coins')
                else:
                    discard.append(item['id'])
                    self.toString('bronzeMethod: Discarding %s' % item['name'])
            else:
                discard.append(item['id'])
                self.toString('bronzeMethod: Discarding Item')

        if len(discard) > 0:
            sold = self.quickSell(discard)
            self.toString('bronzeMethod: Quick Selling Discard : %s' % sold)

        if self.pack:
            self.openPack(self.pack, preorder=True)
            self.toString('bronzeMethod: Opened Silver Pack')
            self.pack = None
        else:
            self.openPack(100)
            self.toString('bronzeMethod: Opened New Pack')


