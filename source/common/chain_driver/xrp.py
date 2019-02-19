# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-7-26 下午2:25

import json
import requests


class RippleClient(object):
    TEST_RIPPLE_SERVER = 'https://s.altnet.rippletest.net:51234'
    PROD_RIPPLE_SERVER = 'https://s1.ripple.com:51234'

    def __init__(self, server=PROD_RIPPLE_SERVER, timeout=300):
        self.server = server
        self.timeout = timeout

    def _request(self, method, params, strict=True, ledger_index=None):
        params['strict'] = strict
        params['ledger_index'] = ledger_index or "validated"

        req = {
            "method": method,
            "params": [
                params
            ]
        }
        response = requests.post(self.server, json=req, timeout=self.timeout)
        if response.status_code != 200:
            raise Exception('Error: {}'.format(response.status_code))
        rv = json.loads(response.text)
        return rv

    ##########################
    # Public Ripple Commands #
    ##########################

    def wallet_propose(self, passphrase=None):
        params = {}
        if passphrase:
            params["passphrase"] = passphrase
        return self._request('wallet_propose', params)

    def account_info(self, account, **kwargs):
        params = {
            "account": account
        }
        params.update(kwargs)
        return self._request('account_info', params)

    def account_currencies(self, account, account_index):
        params = {
            "account": account,
            "account_index": account_index,
        }
        return self._request('account_currencies', params)

    def account_tx(self,
                   account,
                   binary=False,
                   forward=False,
                   ledger_index_max=-1,
                   ledger_index_min=-1,
                   limit=20,
                   **kwargs
                   ):
        """
        The account_tx method retrieves a list of transactions that involved
        the specified account.

        "params": [
        {
            "account": "r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59",
            "binary": false,
            "forward": false,
            "ledger_index_max": -1,
            "ledger_index_min": -1,
            "limit": 2
        }
        https://ripple.com/build/rippled-apis/#account-tx

        """
        params = {
            "account": account,
            "binary": binary,
            "forward": forward,
            "ledger_index_max": ledger_index_max,
            "ledger_index_min": ledger_index_min,
            "limit": limit,
        }
        params.update(kwargs)
        return self._request('account_tx', params)

    def set_regular_key(self, account, regular_key, secret_key):
        """
        {
           "method": "sign",
           "params": [
              {
                 "tx_json": {
                    "TransactionType": "SetRegularKey",
                    "Account": "rUAi7pipxGpYfPNg3LtPcf2ApiS8aw9A93",
                    "RegularKey": "rsprUqu6BHAffAeG4HpSdjBNvnA6gdnZV7"
                 },
                 "secret": "ssCATR7CBvn4GLd1UuU2bqqQffHki"
              }
           ]
        }
        """
        params = {
            "tx_json": {
                'TransactionType': 'SetRegularKey',
                'Account': account,
                'RegularKey':  regular_key
            },
            "secret": secret_key
        }
        return self._request('sign', params)

    def sign(self, secret_key, transaction):
        if transaction.currency == 'XRP':
            amount = str(transaction.amount)
        else:
            amount = {
                "currency": transaction.currency,
                "issuer": transaction.issuer or transaction.source_address,
                "value": str(transaction.amount),
            }
        params = {
            "offline": False,
            "secret": secret_key,
            "tx_json": {
                "Account": transaction.source_address,
                "Amount": amount,
                "Destination": transaction.destination_address,
                "TransactionType": transaction.transaction_type,
                'LastLedgerSequence': transaction.last_ledger_sequence,
                'DestinationTag': transaction.destination_tag,
                'SourceTag': transaction.source_tag
            },
            "fee_mult_max": transaction.fee_mult_max,
        }
        return self._request('sign', params)

    def cancel_tx(self, secret_key, tx_id):
        """
        取消订单，Typically, this means sending another transaction with the
         same Sequence value from the same account.
        :param tx_id: 订单id
        :return:
        """
        rv = self.tx(tx_id)
        if rv['result']['validated']:
            # 订单已经被合并，无法取消
            return

        sequence = rv['result']['Sequence']
        account = rv['result']['Account']

        params = {
            "secret": secret_key,
            'offline': False,
            'tx_json': {
                'Account': account,
                "TransactionType": "AccountSet",
                'Sequence': sequence
            }
        }
        res = self._request('sign', params)
        tx_blob = res['result']['tx_blob']
        return self.submit(tx_blob)

    def submit(self, tx_blob):
        """
        Given the BLOB that is returned after signing a transaction with secret
        key, submit it to the server
        """
        params = {
            'tx_blob': tx_blob
        }
        return self._request('submit', params)

    def tx(self, transaction, binary=False):
        """The tx method retrieves information on a single transaction."""
        params = {
            'transaction': transaction,
            'binary': binary
        }
        return self._request('tx', params)

    ######################
    # Ledger 相关接口 #
    ######################

    def ledger_current(self):
        """当前账本"""
        params = {}
        return self._request('ledger_current', params)

    def ledger_closed(self):
        """最近的已关闭的账本
        响应示例
        {
            "result": {
                "ledger_hash": "CBAFB81722D06E1335256CB49FC9500C55F29E15098AC8A95059476E3111CD25",
                "ledger_index": 28,
                "status": "success"
            }
        }
        """
        params = {}
        return self._request('ledger_closed', params)

    def ledger(self, ledger_index='validated', accounts=False, full=False,
               transactions=False, expand=False, owner_funds=False, **kwargs):
        """Retrieve information about the public ledger."""
        params = {
            "ledger_index": ledger_index,
            "accounts": accounts,
            "full": full,
            "transactions": transactions,
            "expand": expand,
            "owner_funds": owner_funds
        }
        params.update(kwargs)
        return self._request('ledger', params)

    #########################
    # Admin Ripple Commands #
    #########################


class RippleTransaction(object):
    def __init__(self,
                 source_address,
                 destination_address,
                 amount,
                 last_ledger_sequence,
                 currency="XRP",
                 issuer=None,
                 transaction_type="Payment",
                 fee_mult_max=1000,
                 destination_tag=0,
                 source_tag=0,
                 ):
        self.source_address = source_address
        self.destination_address = destination_address
        self.amount = amount
        self.currency = currency
        self.issuer = issuer
        self.transaction_type = transaction_type
        self.fee_mult_max = fee_mult_max
        self.last_ledger_sequence = last_ledger_sequence
        self.destination_tag = destination_tag
        self.source_tag = source_tag


class XrpOpt(object):
    def __init__(self, uri, address='', secret='', timeout=300):
        self.client = RippleClient(uri, timeout)
        self.address = address
        self.secret_key = secret

    @property
    def ledger_closed_index(self):
        rv = self.client.ledger_closed()
        return rv['result']['ledger_index']

    @property
    def ledger_current(self):
        rv = self.client.ledger_current()
        return rv['result']['ledger_current_index']

    def account_info(self, account=None, **kwargs):
        if account is None:
            account = self.address
        return self.client.account_info(account, **kwargs)

    def account_tx(self, account=None, marker=True):
        if account is None:
            account = self.address
        return self.client.account_tx(account, marker=marker)

    def get_balance(self, account=None):
        if account is None:
            account = self.address
        account_info = self.client.account_info(account,
                                                strict=True,
                                                ledger_index='validated')
        if account_info['result']['status'] == 'success' and \
            account_info['result']['validated']:
            return float(account_info['result']['account_data']['Balance'])
        else:
            return 0

    def send2address(self, destination, amount, destination_tag=None,
                     fee_mult_max=None, source_tag=0):
        ledger_current_index = self.ledger_current
        transaction = RippleTransaction(
            source_address=self.address,
            destination_address=destination,
            amount=amount,
            last_ledger_sequence=ledger_current_index + 4,
            source_tag=source_tag
        )
        if destination_tag:
            transaction.destination_tag = destination_tag
        if fee_mult_max:
            transaction.fee_mult_max = fee_mult_max
        rv = self.client.sign(self.secret_key, transaction)
        tx_blob = rv['result']['tx_blob']
        return self.client.submit(tx_blob)

    @classmethod
    def is_validated(cls, tx):
        try:
            return tx['result']['validated'] and \
                   tx['result']['meta']['TransactionResult'] == "tesSUCCESS"
        except:
            return False
