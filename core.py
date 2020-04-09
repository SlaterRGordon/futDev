import requests, pickle
import json
import re
import time
from app.urls import headers, authUrl, pinUrl, clientId, releaseType, funCaptchaPublicKey
from app.pin import Pin

count = 0

class Core(object):

    def __init__(self, email, password):
        """ Initialization """

    def __login__(self, email, password):
        """ Logs in and stores the access token """

    def __launch__(self, email, password):
        """ Accesses fut web application """

    def __request__(self, method, url, data=None, params=None):
        """ Sends request and returns response in json format """

    def bronzePackMethod(self):
        """ opens bronze packs and sells items """

        rc = self.unassigned()

        if rc != {}:
            self.clear(rc)
        
        rc = self.buyPack(100)

        if rc != {}:
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

        # TODO: Loop through and decide what to do with each

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

    

    

        

        