

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
    resp = self.request(url, method, params=params)
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
    self.request(url, method, data=json.dumps(data))

    return resp

def sell(self, itemId, buyNowPrice, startingBid, duration=3600):
    """ Search Item """

    method = 'POST'
    url = 'auctionhouse'
    data = {'buyNowPrice': buyNowPrice, 'duration': duration, 'itemData': {'id': itemId}, 'startingBid': startingBid}
    resp = self.request(url, method, data=json.dumps(data))

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

        lastBuy = buy
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



        

    