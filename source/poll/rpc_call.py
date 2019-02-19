# @Author  : ymy
# @Email   : yaomingyong@wanshare.com
# @Time    : 18-10-25 上午9:26

# 由java提供的接口

import json
import requests
from retry import retry

from source import config


url = config.java_rpc_server


@retry(tries=3, delay=3)
def recharge(address, from_address, amount, txid, coin_type,
             confirmations, status, destination_tag=None):
    headers = {'content-type': 'application/json'}
    payload = {
        "method": "recharge",
        "params": {
            'address': address,
            'from_address': from_address,
            'amount': amount,
            'txid': txid,
            'coin_type': coin_type,
            'destination_tag': destination_tag,
            'confirmations': confirmations,
            'status': status
        },
        "jsonrpc": "2.0",
        "id": 0,
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()


@retry(tries=3, delay=3)
def confirm(txid, confirmations, status):
    headers = {'content-type': 'application/json'}
    payload = {
        "method": 'confirmWithdraw',
        "params": {
            'txid': txid,
            'status': status,
            'confirmations': confirmations
        },
        "jsonrpc": "2.0",
        "id": 0,
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()


