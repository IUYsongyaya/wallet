#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:ljc
@file: log.py
@time: 2018/09/07
"""
import logging


def get_logger(logger_name='service_engine',
               log_level=logging.WARNING,
               filename=""):
    """
    创建logger
    :param logger_name: logger名字一般为文件名
    :param log_level: 日志级别,从config中获取
    :param filename: 输出到文件(为空时输出控制台)
    :return:
    """
    logger = logging.getLogger(logger_name)
    log_formatter = u"[%(asctime)s] %(levelname)-8s %(pathname)s " \
                    u"%(funcName)s %(lineno)d %(process)d " \
                    u"%(thread)d %(threadName)s: %(message)s"
    formatter = logging.Formatter(log_formatter)
    logger.setLevel(log_level)

    if filename:
        fh = logging.FileHandler(filename)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    else:
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)
    return logger
