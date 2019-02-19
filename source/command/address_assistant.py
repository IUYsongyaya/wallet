#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: address_assistant.py
@time: 2018/11/06
"""
import os
import threading
import importlib.util
from source import config
from source.common.utils.log import get_logger
from source.model.database import Session

ADDRESS_MANAGER_PATH = os.path.dirname(__file__) + "/../common/address_manager"
spec = importlib.util.spec_from_file_location("address_manager", "%s/%s.py" % (ADDRESS_MANAGER_PATH, config.coin_type.lower()))
address_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(address_manager)
AddressManager = address_manager.AddressManager

logger = get_logger(__name__, config.log_level)


def create_address(count):
    """用于最初手动批量创建地址"""
    # 通过mongodb客户端创建地址管理器
    # 因为mongo连接池大小为5,创建最多5个线程来创建地址
    remainder = count % 4  # 余数用来判断4个线程是否满足需求
    segment = count // 4 if count >= 4 else 0  # 整数用来判断每个线程中的创建地址数
    thread_pool = list()
    start_point = 0
    while True:
        print(f"=============New thread {start_point} {segment} {remainder}")
        thread = threading.Thread(
            target=AddressManager(Session).bulk_create_address,
            args=(start_point, start_point + segment))
        thread.start()
        thread_pool.append(thread)
        start_point += segment
        
        if sum([start_point, segment, remainder]) >= count:
            break
    if remainder:
        other_thread = threading.Thread(
            target=AddressManager(Session).bulk_create_address,
            args=(count - remainder, count))
        other_thread.start()
        thread_pool.append(other_thread)
    for i in thread_pool:
        i.join()
    logger.info("创建地址完成")


def main():
    AddressManager(Session).bulk_create_address(0, 1)


if __name__ == '__main__':
    main()
