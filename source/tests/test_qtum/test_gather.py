# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 18-11-4


import random
import pytest
import json

from common.chain_driver.bitcoin_operator.qtum import QtumOP
import config


address_from = "qQ9Xd2zdouyJ8GbYMz3o6Dj5Ww68NZPuy8"
hex_address_from = "4845f6d06443815b63a831bb0443135e9c30698b"
account_from = "QTUM_20181107_1_1541595154.134524"
priv_address_from = "cPsryuY1oQoBzcKX6pCJtShWKiYkGuXywsmsAPkakuUv8Y9eThTq"


address_to = "qbjWFymbYQf6HZEx81w85miYZShyxLQXvY"
hex_address_to = "c75c5a46b7a15f5c8a4bc47cffb6e5feaa6e7286"
account_to = "QTUM_20181107_1_1541597505.627648"
priv_address_to = "cPELCsWsrJKMb66aRxB5hePL44SWqqUYmFEGXHsETVcopycpPtBR"


chain_api = QtumOP(config)


class TestGather:
	
	# def test_get_account_by_address(self):
	# 	account = chain_api.get_account(address_from)
	# 	print("address_from:%s ==> account:%s" % (address_from, account))
	# 	assert account == account_from
	#
	# 	account = chain_api.get_account(address_to)
	# 	print("address_to:%s ==> account:%s" % (address_to, account))
	# 	assert account == account_to
	#
	# def test_list_accounts(self):
	# 	accounts = chain_api.list_accounts()
	# 	print(accounts)

	def test_get_balance(self):
		balance = chain_api.get_balance(account_from)
		print("%s : %u qtum" % (account_from, balance))
		balance = chain_api.get_balance(account_to)
		print("%s : %u qtum" % (account_to, balance))

	def test_get_walletinfo(self):
		print(chain_api.get_wallet_info())

	def test_recharge_qtum(self):
		chain_api.send2address("qQzA2Gxm7tPwyEqrxMBQNcrvwsbxVRrYZw", amount=6)

	def test_get_walletinfo_after(self):
		print(chain_api.get_wallet_info())
	
	def test_get_balance_after(self):
		balance = chain_api.get_balance(account_from)
		print("%s : %u qtum" % (account_from, balance))
		balance = chain_api.get_balance(account_to)
		print("%s : %u qtum" % (account_to, balance))
		
	# def test_get_transaction(self):
	# 	tnxs = chain_api.list_transactions()
	# 	for tnx in tnxs:
	# 		print("transaction ===>", tnx)
	#
	# def test_get_confirm_num(self):
	# 	tnxs = chain_api.list_transactions()
	# 	for tnx in tnxs:
	# 		confirmations = tnx['confirmations']
	# 		print("%s ==> %u confirms" % (tnx['address'], confirmations))