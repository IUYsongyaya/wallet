# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 18-11-3

import random
import pytest
import json

from common.chain_driver.bitcoin_operator.qtum import QtumOP
import config


address_from = "qQ9Xd2zdouyJ8GbYMz3o6Dj5Ww68NZPuy8"
hex_address_from = "4845f6d06443815b63a831bb0443135e9c30698b"
account_from = "QTUM_20181107_1_1541595154.134524"
priv_address_from = "cPsryuY1oQoBzcKX6pCJtShWKiYkGuXywsmsAPkakuUv8Y9eThTq"

# address_from = "qQzA2Gxm7tPwyEqrxMBQNcrvwsbxVRrYZw"
# hex_address_from = "4845f6d06443815b63a831bb0443135e9c30698b"
# account_from = "QTUM_20181108_1_1541644061.317054"
# priv_address_from = "cTWcpHWFyEMtpqVTZoLCEFGintTwdRPqQR6UicXqqs54uLpespkH"


address_to = "qbjWFymbYQf6HZEx81w85miYZShyxLQXvY"
hex_address_to = "c75c5a46b7a15f5c8a4bc47cffb6e5feaa6e7286"
account_to = "QTUM_20181107_1_1541597505.627648"
priv_address_to = "cPELCsWsrJKMb66aRxB5hePL44SWqqUYmFEGXHsETVcopycpPtBR"


chain_api = QtumOP(config)


def pytest_namespace():
	return dict(tx_id="")


LARGE_AMOUNT_CONFIRMATION_NUM = 20
SMALL_AMOUNT_CONFIRMATION_NUM = 10


class TestRecharge:
	
	def test_qtum_check_tx_success(self):
		for tnx in chain_api.list_transactions():
			chain_api.is_success(tnx)
			assert chain_api.is_success(tnx)

	def test_qtum_check_balance_confirmation_enough(self):
		# target_balance = 70
		print("Balance:%u" % chain_api.get_balance(account_from))
		balance = 0.0
		
		for tnx in chain_api.list_transactions():
			chain_api.is_success(tnx)
			assert chain_api.is_success(tnx)
			print("%s %s %u qtums, confirmation:%u" % (
				tnx["account"], tnx["category"], tnx["amount"], tnx["confirmations"]))
			
			if tnx["category"] == "receive" and tnx["confirmations"] > SMALL_AMOUNT_CONFIRMATION_NUM:
				balance += int(tnx["amount"])
			
			if tnx["category"] == "send":
				balance -= int(tnx["amount"])
		
		# assert balance == target_balance