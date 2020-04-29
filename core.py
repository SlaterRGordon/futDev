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

        # self.positions = [[[],[],[],[],[],[],[],[],[],[],[]], [[],[],[],[],[],[],[],[],[],[],[]], [[],[],[],[],[],[],[],[],[],[],[]]]
        self.positions = {
            'bronze': {'GK': [], 'RB': [], 'CB': [], 'LB': [], 'CDM': [], 'CM': [], 'RM': [], 'LM': [], 'CAM': [], 'ST': []},
            'silver': {'GK': [], 'RB': [], 'CB': [], 'LB': [], 'CDM': [], 'CM': [], 'RM': [], 'LM': [], 'CAM': [], 'ST': []},
            'gold': {'GK': [], 'RB': [], 'CB': [], 'LB': [], 'CDM': [], 'CM': [], 'RM': [], 'LM': [], 'CAM': [], 'ST': []}
        }

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

        exit()


    """
    GENERIC METHODS

    """
    def request(self, method, url, data=None, params=None):
        """ Request
        """

        time.sleep(random.uniform(2,4))

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
            if resp.status_code == 458:
                self.toString('request: Captcha, logging out...')
                self.logout()
            print(method)
            print(url)
            print(resp.status_code)
            print(resp.url)
            print(resp.content)
            print(params)
            print(data)

        self.count += 1
        if self.count == 90:
            self.toString('request: 90 requests, taking break...')
            time.sleep(random.uniform(300, 360))
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

        if 'itemData' in resp:
            if resp['itemData'][0]['success']:
                return True
            elif resp['itemData'][0]['reason'] == 'Duplicate Item Type':
                return False
            elif resp['itemData'][0]['reason'] == 'Destination Full':
                tradepile = self.tradepile()
                self.clearSold()
                self.toString('sendToPile: Tradepile Full, Clearing...')
                self.clearTradepile(tradepile)
                sent = self.sendToPile('trade', itemId)
                return sent
        else:
            return False

    def club(self, league=None, club=None, position=None, quality=None, start=0, count=91):
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
        if position:
            params['position'] = position
        if quality:
            params['level'] = quality

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
        
        if resp == {}:
            return False

        return True

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
        """ Get Tradepile and Return it """

        method = 'GET'
        url = 'tradepile'

        events = [self.pin.event('page_view', 'Hub - Transfers'), self.pin.event('page_view', 'Transfer List - List View')]
        self.pin.send(events)
        resp = self.request(method, url)
        if 'auctionInfo' in resp:
            events = [self.pin.event('page_view', 'Item - Detail View')]
        self.pin.send(events)

        return resp

    def clearSold(self):
        """ Clear Sold Items on Tradepile """

        method = 'DELETE'
        url = 'trade/sold'
        self.request(method, url)

    def tradeStatus(self, tradeId):
        """ Get the Trade's Status """

        method = 'GET'
        url = 'trade/status'
        params = {'tradeIds': tradeId}
        resp = self.request(method, url, params=params)
        return resp

    def search(self, start=0, num=21, type='player', maskedDefId=None, zone=None, pos=None, lev=None, nat=None, leag=None, team=None, playStyle=None, micr=None, macr=None, minb=None, maxb=None):
        """ Search Auctions """

        method = 'GET'
        url = 'transfermarket'

        params = {'start': start, 'num': num, 'type': type}

        args = locals()
        for arg in args:
            if arg!='self':
                params[arg] = args[arg]
        
        events = [self.pin.event('page_view', 'Hub - Transfers'), self.pin.event('page_view', 'Transfer Market Search')]
        self.pin.send(events)

        resp = self.request(method, url, params=params)

        events = [self.pin.event('page_view', 'Transfer Market Results - List View')]
        self.pin.send(events)

        return resp

    def buy(self, tradeId, bid):
        """ Tries to Buy Item """

        method = 'PUT'
        url = 'trade/%s/bid' % tradeId
        data = {'bid': bid}
        self.request(method, url, data=json.dumps(data))

        return resp

    def sell(self, itemId, buyNowPrice, duration=3600):
        """ Search Item """
        buyNowPrice, startingBid = self.getBid(buyNowPrice)
        method = 'POST'
        url = 'auctionhouse'
        data = {'buyNowPrice': buyNowPrice, 'duration': duration, 'itemData': {'id': itemId}, 'startingBid': startingBid}
        resp = self.request(method, url, data=json.dumps(data))

        return resp

    def price(self, assetId):
        """ Get Item Price """

        buy = 0
        lastBuy = 0
        start = 0
        while(True):
            if buy == 0:
                resp = self.search(maskedDefId=assetId, start=start)
            else:
                resp = self.search(maskedDefId=assetId, maxb=buy, start=start)

            
            if 'auctionInfo' in resp:        
                for auction in resp['auctionInfo']:
                    if auction['buyNowPrice'] < buy or buy == 0:
                        buy = auction['buyNowPrice']

                if len(resp['auctionInfo']) < 2:
                    return buy
                elif len(resp['auctionInfo']) == 21 and buy == lastBuy:
                    start += 20
                elif buy == lastBuy:
                    if buy == 200: return 199
                    return buy 
            else: 
                return buy

            lastBuy = buy

    def getBid(self, buy):
        """ Get the next closest bid value after buy's value """

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

        return buy, bid

    def clearTradepile(self):
        """ Clear Tradepile """                

        tradepile = self.tradepile()
        self.clearSold()

        discard = []
        for auction in tradepile['auctionInfo']:
            if auction['tradeState'] != 'active' and auction['itemData']['itemType'] == 'player':
                if auction['buyNowPrice'] == 200:
                    discard.append(auction['itemData']['id'])
                else:
                    buy = self.price(auction['itemData']['assetId'])
                    if buy < 200 and buy != 0:
                        discard.append(auction['itemData']['id'])
                    elif buy > 200:
                        buy, bid = getBid(buy)
                        self.sell(auction['itemData']['id'], buy, bid)

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
                        print('in progress')
                        squad = self.getSquad(challengeId)
                    elif challenge['status'] == 'NOT_STARTED':
                        print('not started')
                        squad = self.getSquad(challengeId, started=False)
                    else:
                        print('completed')
                        return False

        if squad == None:
            return False

        players = []
        moved = False
        count = 0

        for i, player in enumerate(squad['squad']['players']):
            if player['itemData']['id'] == 0 and not moved:
                players.append({'index': i, 'itemData': {'id': int(itemId), 'dream': 'false'}})
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

        leagues = [(13, 262), (16, 116), (31, 156), (53, 367), (19, 95), (39, 149), (14, 280), (350, 162), (2012, 107), (308, 155)]
        for league in leagues:
            if league[0] == leagueId:
                return league[1]

        return 0

    def findChallenge(self, setId, clubId, challengeId=None):
        """ Find Player ChallengeId
        """

        challenges = self.getChallenges(setId)
        for challenge in challenges['challenges']:
            if not challengeId:
                for item in challenge['elgReq']:
                    if item['type'] == 'CLUB_ID':
                        if item['eligibilityValue'] == clubId:
                            challengeId = challenge['challengeId']
                            if challenge['status'] == 'IN_PROGRESS':
                                return self.getSquad(challengeId), challengeId
                            elif challenge['status'] == 'NOT_STARTED':
                                return self.getSquad(challengeId, started=False), challengeId
            elif challengeId == challenge['challengeId']:
                if challenge['status'] == 'IN_PROGRESS':
                    return self.getSquad(challengeId)
                elif challenge['status'] == 'NOT_STARTED':
                    return self.getSquad(challengeId, started=False)

        return None, 0

    def clearSquad(self, squad, challengeId):
        players = []
        for i, player in enumerate(squad['squad']['players']):
            players.append({'index': i, 'itemData': {'id': player['itemData']['id'], 'dream': 'false'}})

        for player in players:
            if player['itemData']['id'] == 0:
                continue
            player['itemData']['id'] = 0
            method = 'PUT'
            url = 'sbs/challenge/%s/squad' % challengeId
            data = {'players': players}
            resp = self.request(method, url, data=json.dumps(data))


    """
    BRONZE PACK METHODS

    """
    # TODO Go through each method used in here and make better
    def bronzeMethod(self, packId=100):
        """ Bronze Pack Method
        """

        discard = []
        positions = [['GK'], ['RB'], ['CB'], ['CB'], ['LB'], ['CDM', 'CM'], ['RM', 'RW'], ['LM', 'LW'], ['CAM', 'CM'], ['ST'], ['ST']]

        if packId == 100:
            opened = self.openPack(packId)
            self.toString('bronzeMethod: Opened New Pack')
        else:
            opened = self.openPack(packId, preorder=True)
            self.toString('bronzeMethod: Opened New Pack')

        unassigned = self.unassigned()

        for item in unassigned['itemData']:
            if item['itemType'] == 'player':
                
                added = True
                setId = self.findSet(item['leagueId'])
                self.toString('bronzeMethod: SetId: %s' % setId)

                if setId != 0:
                    sent = self.sendToPile('club', item['id'])
                    self.toString('bronzeMethod: Sent League Player to Club : %s' % sent)
                    if sent:
                        added = self.addPlayer(item['id'], setId=setId, leagueId=item['leagueId'], clubId=item['teamid'])
                        self.toString('bronzeMethod: Added League Player to SBC : %s' % added)
                        if added:
                            continue
                
                buy = self.price(item['assetId'])
                self.toString('bronzeMethod: Price: %s' % buy)
                if buy > 199:
                    sent = self.sendToPile('trade', item['id'])
                    self.toString('bronzeMethod: Sent Player to Trade : %s' % sent)
                    if sent:
                        sold = self.sell(item['id'], buy)
                        self.toString('bronzeMethod: Listed Player for %s : %s' % (buy, sold))
                        continue

                sent = self.sendToPile('club', item['id'])
                self.toString('bronzeMethod: Sent Player to Club : %s' % sent)
                if sent or not added:
                    for i, positionList in enumerate(positions):
                        for position in positionList:
                            if position == item['preferredPosition']:
                                print(position)
                                if position == 'RW':
                                    position = 'RM'
                                if position == 'LW':
                                    position = 'LM'
                                if item['rating'] < 65:
                                    self.positions['bronze'][position].append(item['id'])
                                elif item['rating'] < 75:
                                    self.positions['silver'][position].append(item['id'])
                                else:
                                    self.positions['gold'][position].append(item['id'])
                    continue

            elif item['resourceId'] == 5002004:
                sent = self.sendToPile('trade', item['id'])
                self.toString('bronzeMethod: Sent Squad Fitness to Trade : %s' % sent)
                if sent:
                    sold = self.sell(item['id'], 1000)
                    self.toString('bronzeMethod: Listed Squad Fitness for %s : %s' % (1000, sold))
                    continue

            elif 'name' in item:
                if item['name'] == 'FreeCredits' or item['name'] == 'FreeBronzePack':
                    self.redeem(item['id'])
                    self.toString('bronzeMethod: Redeemed %s' % item['name'])
                    continue
            
            discard.append(item['id'])
            self.toString('bronzeMethod: Adding to Discard')

        if len(discard) > 0:
            sold = self.quickSell(discard)
            self.toString('bronzeMethod: Quick Selling Discard : %s' % sold)


    def upgradeSbc(self):
        """ Bronze Pack Method
        """

        positions = [['GK'], ['RB'], ['CB'], ['CB'], ['LB'], ['CDM', 'CM'], ['RM', 'RW'], ['LM', 'LW'], ['CAM', 'CM'], ['ST'], ['ST']]
        qualities = ['bronze', 'silver', 'gold']

        self.getSets()
        for index in range(3):
            squad = None
            setId = 6+index
            challengeId = 15+index
            print('setId: %s, challengeId: %s' % (setId, challengeId))
            challenges = self.getChallenges(setId)
            for challenge in challenges['challenges']:
                if challenge['status'] == 'IN_PROGRESS':
                    squad = self.getSquad(challengeId)
                elif challenge['status'] == 'NOT_STARTED':
                    squad = self.getSquad(challengeId, started=False)

            players = []
            itemIds = []
            for i, player in enumerate(squad['squad']['players']):
                players.append({'index': i, 'itemData': {'id': player['itemData']['id'], 'dream': 'false'}})


            print(players)
            count = 0
            
            for i, player in enumerate(players):
                if i < 11 and player['itemData']['id'] == 0:
                    print('checking for player')
                    for position in positions[i]:
                        if position == 'RW':
                            position = 'RM'
                        if position == 'LW':
                            position = 'LM'
                        if self.positions[qualities[index]][position]:
                            itemId = self.positions[qualities[index]][position].pop()
                            player['itemData']['id'] = itemId
                            method = 'PUT'
                            url = 'sbs/challenge/%s/squad' % challengeId
                            data = {'players': players}
                            resp = self.request(method, url, data=json.dumps(data))
                            print('added to sbc, %s - %s' % (qualities[index], count))
                            count += 1
                            break
                        else:
                            print('No more %s players in position %s' % (qualities[index], position))
                
                elif i < 11 and player['itemData']['id'] != 0:
                    count += 1

            if count > 10:
                method = 'PUT'
                url = 'sbs/challenge/%s' % challengeId
                params = {'skipUserSquadValidation': False}
                resp = self.request(method, url, params=params)
                if 'grantedSetAwards' in resp:
                    print('completed sbc, %s' % qualities[index])
                    self.bronzeMethod(resp['grantedSetAwards'][0]['value'])
    
    # def checkUpgrades(self):
    #     """ Format Message
    #     """

    def fillUpgrades(self):
        """ Format Message
        """

        positionList = [['GK'], ['RB'], ['CB'], ['CB'], ['LB'], ['CDM', 'CM'], ['RM', 'RW'], ['LM', 'LW'], ['CAM'], ['CM'], ['ST'], ['ST']]
        qualities = ['bronze', 'silver']

        self.clearSquad(self.findChallenge(6, 0, challengeId=15), 15)
        self.clearSquad(self.findChallenge(7, 0, challengeId=16), 16)
        self.clearSquad(self.findChallenge(8, 0, challengeId=17), 17)

        for i, quality in enumerate(qualities):
            for j, positions in enumerate(positionList):
                for position in positions:
                    start = 0
                    same = False
                    while(True):
                        count = 0
                        items = self.club(quality=quality, position=position, start=start)
                        if 'itemData' in items:
                            if len(items['itemData']) > 0:
                                for item in items['itemData']:
                                    if self.findSet(item['leagueId']) == 0 and item['rating'] < 81:
                                        if position == 'RW':
                                            position = 'RM'
                                        if position == 'LW':
                                            position = 'LM'

                                        if item['rating'] < 65:
                                            self.positions['bronze'][position].append(item['id'])
                                        elif item['rating'] < 75:
                                            self.positions['silver'][position].append(item['id'])
                                        else:
                                            self.positions['gold'][position].append(item['id'])
                                        count += 1
                            else:
                                break
                        else:
                            break


                        start += 91
        
    def fillLeagueSbc(self):
        leagues = [(13, 262), (16, 116), (31, 156), (53, 367), (19, 95), (39, 149)]
        print('filling league sbcs')
        for league in leagues:
            challenges = self.getChallenges(league[1])
            for challenge in challenges['challenges']:
                if challenge['status'] == 'IN_PROGRESS':
                    squad = self.getSquad(challenge['challengeId'])
                elif challenge['status'] == 'NOT_STARTED':
                    squad = self.getSquad(challenge['challengeId'], started=False)
                else:
                    print('completed sbc')
                    continue
                for item in challenge['elgReq']:
                    if item['type'] == 'CLUB_ID':
                        club = self.club(club=item['eligibilityValue'])
                        if 'itemData' in club:
                            for player in club['itemData']:
                                count = 0
                                if player['rating'] < 82:
                                    sbcPlayers = []
                                    for i, sbcPlayer in enumerate(squad['squad']['players']):
                                        if sbcPlayer['itemData']['id'] != 0:
                                            count += 1
                                        if sbcPlayer['itemData']['id'] == player['id']:
                                            moved = False
                                        sbcPlayers.append({'index': i, 'itemData': {'id': player['id'], 'dream': 'false'}})

                                    if not moved:
                                        continue

                                    for i, sbcPlayer in enumerate(sbcPlayers):
                                        if sbcPlayer['itemData']['id'] == 0:
                                            sbcPlayer['itemData']['id'] = player['id']
                                            method = 'PUT'
                                            url = 'sbs/challenge/%s/squad' % challenge['challengeId']
                                            data = {'players': sbcPlayers}
                                            resp = self.request(method, url, data=json.dumps(data))
                                            count += 1
                                            break

                                        
                            self.toString(challenge['name'] + ': ' + str(count))

                    


 