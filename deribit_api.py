# -*- coding: utf-8 -*-

import base64
import hashlib
import requests
import time
from collections import OrderedDict


class RestClient(object):
    """ client to make requests to Deribit's REST API """

    def __init__(self, key=None, secret=None, url=None):
        """ configure API credentials. one can find these at:
            --> https://www.deribit.com/main#/account?scrollTo=api

        :param key: (str) access key
        :param secret: (str) access secret
        :param url: (str) root url, defaults to the main site
            use this parameter to make API calls to Deribit's test net
        """
        self.key = key
        self.secret = secret
        self.session = requests.Session()

        if url:
            self.url = url
        else:
            self.url = "https://www.deribit.com"

    def request(self, action, data):
        """ perform generic request to the API

        :param action: (str) the suffix of the API endpoint
            e.g. '/api/v1/public/getcurrencies'
        :param data: (dict) additional data to pass to this request
        :return: (str or dict) json response
        """
        response = None

        if action.startswith("/api/v1/private/"):
            if self.key is None or self.secret is None:
                raise Exception("Key or secret empty")

            signature = self.generate_signature(action, data)
            response = self.session.post(self.url + action, data=data, headers={'x-deribit-sig': signature},
                                         verify=True)
        else:
            response = self.session.get(self.url + action, params=data, verify=True)

        if response.status_code != 200:
            raise Exception("Wrong response code: {0}".format(response.status_code))

        json = response.json()

        if json["success"] == False:
            raise Exception("Failed: " + json["message"])

        if "result" in json:
            return json["result"]
        elif "message" in json:
            return json["message"]
        else:
            return "Ok"

    def generate_signature(self, action, data):
        """ create signature, as a function of:
            - API credentials
            - API action
            - timestamp

        :param action: (str) the suffix of the API endpoint
        :param data: (dict) additional data to pass to this request
        :return: (str) unicode string
        """
        tstamp = int(time.time() * 1000)
        signature_data = {
            '_': tstamp,
            '_ackey': self.key,
            '_acsec': self.secret,
            '_action': action
        }
        signature_data.update(data)
        sorted_signature_data = OrderedDict(sorted(signature_data.items(), key=lambda t: t[0]))

        def converter(data):
            key = data[0]
            value = data[1]
            if isinstance(value, list):
                return '='.join([str(key), ''.join(value)])
            else:
                return '='.join([str(key), str(value)])

        items = map(converter, sorted_signature_data.items())

        signature_string = '&'.join(items)

        sha256 = hashlib.sha256()
        sha256.update(signature_string.encode("utf-8"))
        sig = self.key + "." + str(tstamp) + "."
        sig += base64.b64encode(sha256.digest()).decode("utf-8")
        return sig

    def getorderbook(self, instrument):
        """ Retrieve the orderbook for a given instrument

        :param instrument: (str) Required, instrument name
        :return: (dict) example:
            {
                'state': 'open',
                'settlementPrice': 2.705176305e-06,
                'instrument': 'BTC-5JAN18-11000-P',
                'bids': [],
                'asks': [{'quantity': 1.2, 'price': 0.0033, 'cm': 1.2}],
                'tstamp': 1515114174701,
                'last': 0.0001,
                'low': 0.0001,
                'high': 0.0001,
                'mark': 9.483847626285752e-15,
                'uPx': 15048.52,
                'uIx': 'index_price',
                'iR': 0,
                'markIv': 160.0,
                'askIv': 500.0,
                'bidIv': 0.0
            }
        """
        return self.request("/api/v1/public/getorderbook", {'instrument': instrument})

    def getinstruments(self):
        """ Retrieve all tradeable instruments
            (both futures and options)

        :return: ([dict]) list of dictionaries. example:
            {
                'kind': 'option',
                'baseCurrency': 'BTC',
                'currency': 'USD',
                'minTradeSize': 0.1,
                'instrumentName': 'BTC-5JAN18-11000-P',
                'isActive': True,
                'settlement': 'week',
                'created': '2017-12-30 16:37:00 GMT',
                'expiration': '2018-01-05 08:00:00 GMT',
                'strike': 11000.0,
                'optionType': 'put',
                'pricePrecision': 4
            }
        """
        return self.request("/api/v1/public/getinstruments", {})

    def getcurrencies(self):
        """ Get all supported currencies

        :return: ([dict]) list of dictionaries. example:
            {
                'currency': 'BTC',
                'currencyLong': 'Bitcoin',
                'minConfirmation': 2,
                'txFee': 0.0006,
                'isActive': True,
                'coinType': 'BITCOIN',
                'baseAddress': None
            }
        """
        return self.request("/api/v1/public/getcurrencies", {})

    def getlasttrades(self, instrument, count=None, since=None):
        """ Retrieve the latest trades that have occurred
            for a specific instrument

        :param instrument: (str) Required, instrument name
        :param count: (int) Optional, count of trades returned
                            (limitation: max. count is 100)
        :param since: (int) Optional, “since” trade id,
            the server returns trades newer than that “since”
        :return: ([dict]) list of dictionaries. example:
            {
                'tradeId': 3615901,
                'instrument': 'BTC-5JAN18-11000-P',
                'tradeSeq': 6,
                'timeStamp': 1515113157777,
                'quantity': 1.0,
                'price': 0.0001,
                'direction': 'sell',
                'tickDirection': 2,
                'indexPrice': 15060.03,
                'iv': 402.81
            }
        """
        options = {
            'instrument': instrument
        }

        if since:
            options['since'] = since

        if count:
            options['count'] = count

        return self.request("/api/v1/public/getlasttrades", options)

    def getsummary(self, instrument):
        """ Retrieve the summary info such as
            Open Interest, 24H Volume etc for a specific instrument

        :param instrument: (str) Required, instrument name
        :return: (dict)
            {
                'instrumentName': 'BTC-5JAN18-11000-P',
                'openInterest': 4.5,
                'high': 0.0001,
                'low': 0.0001,
                'volume': 1.0,
                'volumeBtc': 1.0,
                'last': 0.0001,
                'bidPrice': '',
                'askPrice': 0.0033,
                'midPrice': '',
                'markPrice': 0.0,
                'created': '2018-01-05 01:00:08 GMT'
            }
        """
        return self.request("/api/v1/public/getsummary", {"instrument": instrument})

    def index(self):
        """ Get price index, BTC-USD rates

        :return: (dict)
            {
                'btc': float,
                'edp': float,
            }
        """
        return self.request("/api/v1/public/index", {})

    def stats(self):
        """

        :return: (dict)
            {
                'btc_usd': {
                    'futuresVolume': float,
                    'putsVolume':    float,
                    'callsVolume':   float
                },
                'created': 'YYYY-MM-DD HH:MM:SS GMT'
            }
        """
        return self.request("/api/v1/public/stats", {})

    def account(self):
        """ Get user account summary

        :return: (dict) schema:
            {
                'equity':            float,
                'maintenanceMargin': float,
                'initialMargin':     float,
                'availableFunds':    float,
                'balance':           float,
                'depositAddress':    str,
                'SUPL':              float,
                'SRPL':              float,
                'PNL':               float,
                'optionsPNL':        float,
                'optionsSUPL':       float,
                'optionsSRPL':       float,
                'optionsD':          float,
                'optionsG':          float,
                'optionsV':          float,
                'optionsTh':         float,
                'futuresPNL':        float,
                'futuresSUPL':       float,
                'futuresSRPL':       float,
                'deltaTotal':        float
            }
        """
        return self.request("/api/v1/private/account", {})

    def buy(self, instrument, quantity, price, postOnly=None, label=None):
        """ Place a buy order in an instrument

        :param instrument: (str) Required, instrument name
        :param quantity: (int) Required, quantity, in contracts
                               $10 per contract for futures
                               ฿1 for options
        :param price: (float) Required, USD for futures, BTC for options
        :param postOnly: (bool) Optional, if true then
                                the order will be POST ONLY
        :param label: (str) Optional, user defined maximum
                            4-char label for the order
        :return:
        """
        options = {
            "instrument": instrument,
            "quantity": quantity,
            "price": price
        }

        if label:
            options["label"] = label

        if postOnly:
            options["postOnly"] = postOnly

        return self.request("/api/v1/private/buy", options)

    def sell(self, instrument, quantity, price, postOnly=None, label=None):
        """ Place a sell order in an instrument

        :param instrument: (str) Required, instrument name
        :param quantity: (int) Required, quantity, in contracts
                               $10 per contract for futures
                               ฿1 for options
        :param price: (float) Required, USD for futures, BTC for options
        :param postOnly: (bool) Optional, if true then
                                the order will be POST ONLY
        :param label: (str) Optional, user defined maximum
                            4-char label for the order
        :return:
        """
        options = {
            "instrument": instrument,
            "quantity": quantity,
            "price": price
        }

        if label:
            options["label"] = label
        if postOnly:
            options["postOnly"] = postOnly

        return self.request("/api/v1/private/sell", options)

    def cancel(self, orderId):
        """ Cancel own order by id

        :param orderId: (int) Required, ID of the order returned
                              by "sell" or "buy" request
        :return: None
        """
        options = {
            "orderId": orderId
        }

        return self.request("/api/v1/private/cancel", options)

    def cancelall(self, typeDef="all"):
        """ Cancel all own futures, or all options, or all.

        :param typeDef: (str) Optional, type of instruments to cancel,
                              allowed: "all", "futures", "options",
                              default: "all"
        :return: (str) 'cancel all'
        """
        return self.request("/api/v1/private/cancelall", {"type": typeDef})

    def edit(self, orderId, quantity, price):
        """ Edit price and/or quantity of the own order.
            (Authorization is required).

        :param orderId: (int) Required, ID of the order returned
                              by "sell" or "buy" request
        :param quantity: (int) Required, quantity, in contracts
            ($10 per contract for futures, ฿1 for options)
        :param price: (float) Required, USD for futures, BTC for options
        :return:
        """
        options = {
            "orderId": orderId,
            "quantity": quantity,
            "price": price
        }

        return self.request("/api/v1/private/edit", options)

    def getopenorders(self, instrument=None, orderId=None):
        """ Retrieve open orders.

        :param instrument: (str) Optional, instrument name,
            use if want orders for specific instrument
        :param orderId: (int) Optional, order id
        :return: ([dict])
        """
        options = {}

        if instrument:
            options["instrument"] = instrument
        if orderId:
            options["orderId"] = orderId

        return self.request("/api/v1/private/getopenorders", options)

    def positions(self):
        """ Retrieve positions.

        :return: ([dict])
        """
        return self.request("/api/v1/private/positions", {})

    def orderhistory(self, count=None):
        """ Get history of own orders

        :param count: (int) Optional, number of requested records
        :return: ([dict])
        """
        options = {}
        if count:
            options["count"] = count

        return self.request("/api/v1/private/orderhistory", options)

    def tradehistory(self, countNum=None, instrument="all", startTradeId=None):
        """ Get private trade history of the account. (Authorization is required).
            The result is ordered by trade identifiers (trade id-s).

        :param countNum: (int) Optional, number of results to fetch. Default: 20
        :param instrument: (str) Optional, name of instrument,
            also aliases “all”, “futures”, “options” are allowed. Default: "all"
        :param startTradeId: (int) Optional, number of requested records
        :return: ([dict])
        """
        options = {
            "instrument": instrument
        }

        if countNum:
            options["count"] = countNum
        if startTradeId:
            options["startTradeId"] = startTradeId

        return self.request("/api/v1/private/tradehistory", options)
