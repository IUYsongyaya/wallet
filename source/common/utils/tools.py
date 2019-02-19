# encoding=utf-8
'''tools: 工具模块

@date: 2018.04.25
'''

import decimal
from functools import wraps
from decimal import localcontext


from eth_utils.crypto import keccak


def to_unit(number, unit):
    """币种精度转换"""

    s_number = str(number)
    d_number = decimal.Decimal(s_number)
    unit_value = decimal.Decimal(unit)

    if d_number == 0:
        return 0

    if d_number < 1 and '.' in s_number:
        with localcontext() as ctx:
            multiplier = len(s_number) - s_number.index('.') - 1
            ctx.prec = multiplier
            d_number = decimal.Decimal(
                value=number, context=ctx) * 10**multiplier
        unit_value /= 10**multiplier

    with localcontext() as ctx:
        ctx.prec = 999
        result_value = decimal.Decimal(
            value=d_number, context=ctx) * unit_value

    return int(result_value)


def from_unit(number, unit):
    """币种精度转换"""

    if number == 0:
        return 0

    with localcontext() as ctx:
        ctx.prec = 999
        d_number = decimal.Decimal(value=number, context=ctx)
        result_value = d_number / decimal.Decimal(unit)

    return result_value


def singleton(cls):
    """
    单例装饰

    :params cls: 需要装饰的类
    """
    instances = {}

    @wraps(cls)
    def getinstance(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return getinstance


def func_sign_to_4bytes(event_signature):
    """ASCII Keccak hash 4bytes"""
    return keccak(text=event_signature.replace(' ', ''))[:4]


def notify(msg):
    """发送通知"""
