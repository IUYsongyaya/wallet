# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 18-11-2


import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from model.address_manager import QtumManager


class DictObject:
	def __init__(self, **kwargs):
		for key, val in kwargs.items():
			setattr(self, key, val)


class TestAccountCreate:
	
	def test_create_address(self):
		manager = QtumManager(Mock())
		address = manager.generate_address(1)
		assert address
		assert isinstance(address, dict)
		keys_ = {"account", "pub_address", "private_hash", "destination_tag", "created_at", "updated_at", "coin_type",
				"is_used"}
		for i in keys_:
			assert i in address
	
	# def test_get_address_in_stock(self):
	# 	db = MagicMock()
	# 	query_result = MagicMock()
	# 	first_result = MagicMock()
	# 	db.query.return_value = query_result
	# 	query_result.first_by.return_value = first_result
	# 	addr = dict(account="",
	# 				pub_address="",
	# 				private_hash="",
	# 				destination_tag="",
	# 				created_at="",
	# 				updated_at="",
	# 				coin_type="",
	# 				is_used=False)
	# 	first_result.first.return_value = DictObject(**addr)
	# 	manager = QtumManager(db)
	# 	address = manager.get_address()
	# 	assert address
	# 	assert isinstance(address, dict)
	# 	print(address)
	# 	keys_ = {"account", "pub_address", "private_hash", "destination_tag", "created_at", "updated_at", "coin_type",
	# 			"is_used"}
	# 	for i in keys_:
	# 		assert i in address
	#
	# def test_get_address_short_in_stock(self):
	# 	db = MagicMock()
	# 	query_result = MagicMock()
	# 	first_result = MagicMock()
	# 	db.query.return_value = query_result
	# 	query_result.first_by.return_value = first_result
	# 	first_result.first.return_value = None
	# 	manager = QtumManager(db)
	# 	address = manager.get_address()
	# 	assert address
	# 	assert isinstance(address, dict)
	# 	print(address)
	# 	keys_ = {"account", "pub_address", "private_hash", "destination_tag", "created_at", "updated_at", "coin_type",
	# 			"is_used"}
	# 	for i in keys_:
	# 		assert i in address