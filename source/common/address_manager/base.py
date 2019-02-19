#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
地址管理抽象接口类
@author:ljc
@file: base.py
@time: 2018/09/05
"""
from abc import ABC, abstractmethod, ABCMeta
from copy import deepcopy
import os
import time

from pymongo.errors import OperationFailure
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.orm import scoped_session

from source import config
from source.common.utils import log
from source.model.database import Account
from source.common.encrypt_component import MCipher
from source.exception import NotFoundCollection

logger = log.get_logger(__name__, config.log_level)


class BaseAddressManager(ABC):
    """
    货币地址的抽象工厂
    """
    def __init__(self):
        self.coin_category = None
        self.chain_api = None
        self.db_connect = None
        self.encrypt_tool = MCipher()
        self._address_template = dict(account="",
                                      pub_address="",
                                      private_hash="",
                                      destination_tag="",
                                      coin_type="",
                                      is_used=False)

    @abstractmethod
    def generate_address(self, *args, **kwargs):
        """
        单个地址创建不涉及地址固化存储
        :param args:
        :param kwargs:
        :return:
        """
        return dict()

    @abstractmethod
    def get_address(self, *args, **kwargs):
        pass

    @abstractmethod
    def store_address(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def del_address(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def bulk_create_address(self, *args, **kwargs):
        pass


class MongoAddressManager(BaseAddressManager, metaclass=ABCMeta):
    """mongodb地址管理抽象类"""
    def _get_collection(self, collection_name: str):
        """
        获取mongodb中的集合对象
        :param collection_name: 集合名称
        :return:
        """
        address_collection = self.db_connect[collection_name]
        if not address_collection:
            raise NotFoundCollection(collection_name)
        return address_collection

    def get_address(self)-> dict:
        """
        从db中获取一条未绑定的地址
        获取时判定该地址即将绑定
        :return:
        """
        address_collection = self._get_collection(config.coin_address)
        address = address_collection. \
            find_one_and_update({"coin_type": self.coin_category,
                                 "is_used": False},
                                {"is_used": True})
        if not address:
            logger.warning("预留地址不足请尽快批量创建地址")
            address = self.generate_address(1)
            try:
                self.store_address(**address)
            except (OperationFailure, NotFoundCollection) as e:
                time.sleep(5)
                self.store_address(**address)
                logger.warn("地址不足,单独创建地址失败{}".format(e.msg))
            else:
                return address
        else:
            return address

    def store_address(self, **kwargs):
        """
        将创建的地址存储到db中(插入数据的异常留做上级处理)
        :param kwargs: like self._address_template
        """
        account = Account(**kwargs)
        account.insert()

    def del_address(self, account: str, is_used: bool=False):
        """
        删除地址(慎用,用于处理垃圾数据时临时使用)
        :param account:
        :param is_used:
        """
        address_collection = self._get_collection(config.coin_address)
        address = address_collection.find_one({"account": account,
                                               "coin_type": self.coin_category,
                                               "is_used": is_used})
        if address:
            filename = '{}/{}'.format(config.priv_fn_path, account)
            if os.path.exists(filename):
                address_collection.find_one_and_delete({"account": account,
                                                        "coin_type":
                                                            self.coin_category,
                                                        "is_used": is_used})
                os.remove(filename)

    def bulk_create_address(self, start: int, stop: int):
        """
        批量创建地址
        :param start:
        :param stop:
        """
        for i in range(start, stop):
            address = self.generate_address(i)
            try:
                self.store_address(**address)
            except (OperationFailure, NotFoundCollection) as e:
                time.sleep(5)
                self.store_address(**address)
                logger.warn("创建地址失败{},失败的位置为{}".format(e.msg, i))


class MysqlAddressManager(BaseAddressManager, metaclass=ABCMeta):
    """mysql地址管理抽象类"""
    def __init__(self, parent_session):
        super().__init__()
        self._local_session = scoped_session(parent_session)
        self.db_connect = self._local_session()

    def get_address(self) -> dict:
        """
        从db中获取一条未绑定的地址
        获取时判定该地址即将绑定
        :return:
        """
        try:
            address = self.db_connect.query(
                Account).filter_by(
                coin_type=self.coin_category, is_used=False).first()
        except DisconnectionError:
            logger.exception("数据库链接丢失")
            return dict()
        if not address:
            logger.warning("预留地址不足请尽快批量创建地址")
            address = self.generate_address(1)
            try:
                self.store_address(**address)
            except Exception as e:
                time.sleep(5)
                logger.exception("地址不足,单独创建地址失败{}".format(e))
                self._local_session.remove()
                return dict()
            else:
                return address
        else:
            try:
                address.is_used = True
                copy_address = deepcopy(address)
                self.db_connect.commit()
            except Exception as e:
                logger.exception("修改地址为可用状态失败,失败原因{}".format(e))
                self._local_session.remove()
                return dict()
            else:
                self._local_session.remove()
                return vars(copy_address)

    def store_address(self, **kwargs):
        """
        将创建的地址存储到db中(插入数据的异常留做上级处理)
        :param kwargs: like self._address_template
        """
        try:
            account = Account(**kwargs)
            self.db_connect.add(account)
            self.db_connect.commit()
        except Exception as e:
            logger.exception("数据库保存地址失败,失败原因{}".format(e))
            self.db_connect.rollback()

    def del_address(self, account: str, is_used: bool = False):
        """
        删除地址(慎用,用于处理垃圾数据时临时使用)
        :param account:
        :param is_used:
        """
        try:
            address = self.db_connect.query(
                Account).filter_by(
                account=account, coin_type=self.coin_category, is_used=is_used
            ).first()
        except DisconnectionError:
            logger.exception("丢失数据库连接")
        else:
            if address:
                filename = '{}/{}'.format(config.priv_fn_path, account)
                if os.path.exists(filename):
                    self.db_connect.delete(address)
                    os.remove(filename)

    def bulk_create_address(self, start: int, stop: int):
        """
        批量创建地址
        :param start:
        :param stop:
        """
        for i in range(start, stop):
            address = self.generate_address(i)
            try:
                self.store_address(**address)
            except Exception as e:
                time.sleep(5)
                self.store_address(**address)
                logger.warn("创建地址失败{},失败的位置为{}".format(e, i))
        self._local_session.remove()
