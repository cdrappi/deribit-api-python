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
        """

        :param instrument:
        :return:
        """
        return self.request("/api/v1/public/getorderbook", {'instrument': instrument})

    def getinstruments(self):
        """

        :return:
        """
        return self.request("/api/v1/public/getinstruments", {})

    def getcurrencies(self):
        """

        :return:
        """
        return self.request("/api/v1/public/getcurrencies", {})

    def getlasttrades(self, instrument, count=None, since=None):
        """

        :param instrument:
        :param count:
        :param since:
        :return:
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
        """

        :param instrument:
        :return:
        """
        return self.request("/api/v1/public/getsummary", {"instrument": instrument})

    def index(self):
        """

        :return:
        """
        return self.request("/api/v1/public/index", {})

    def stats(self):
        """

        :return:
        """
        return self.request("/api/v1/public/stats", {})

    def account(self):
        """

        :return:
        """
        return self.request("/api/v1/private/account", {})

    def buy(self, instrument, quantity, price, postOnly=None, label=None):
        """

        :param instrument:
        :param quantity:
        :param price:
        :param postOnly:
        :param label:
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
        """

        :param instrument:
        :param quantity:
        :param price:
        :param postOnly:
        :param label:
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
        """

        :param orderId:
        :return:
        """
        options = {
            "orderId": orderId
        }

        return self.request("/api/v1/private/cancel", options)

    def cancelall(self, typeDef="all"):
        """

        :param typeDef:
        :return:
        """
        return self.request("/api/v1/private/cancelall", {"type": typeDef})

    def edit(self, orderId, quantity, price):
        """

        :param orderId:
        :param quantity:
        :param price:
        :return:
        """
        options = {
            "orderId": orderId,
            "quantity": quantity,
            "price": price
        }

        return self.request("/api/v1/private/edit", options)

    def getopenorders(self, instrument=None, orderId=None):
        """

        :param instrument:
        :param orderId:
        :return:
        """
        options = {}

        if instrument:
            options["instrument"] = instrument
        if orderId:
            options["orderId"] = orderId

        return self.request("/api/v1/private/getopenorders", options)

    def positions(self):
        """

        :return:
        """
        return self.request("/api/v1/private/positions", {})

    def orderhistory(self, count=None):
        """

        :param count:
        :return:
        """
        options = {}
        if count:
            options["count"] = count

        return self.request("/api/v1/private/orderhistory", options)

    def tradehistory(self, countNum=None, instrument="all", startTradeId=None):
        """

        :param countNum:
        :param instrument:
        :param startTradeId:
        :return:
        """
        options = {
            "instrument": instrument
        }

        if countNum:
            options["count"] = countNum
        if startTradeId:
            options["startTradeId"] = startTradeId

        return self.request("/api/v1/private/tradehistory", options)
