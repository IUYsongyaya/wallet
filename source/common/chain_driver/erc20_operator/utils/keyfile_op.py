# encoding=utf-8
"""keyfile_op: 密钥操作模块

@date: 2018.04.27
@last_modified: 2018.04.30
"""

import os
import json
import datetime as dt

from eth_account import Account
from ethereum.tools import keys


def load_keyfile(keyfile, password):
    """加载钱包keyfile

    :param keyfile:
    :param password: 密码
    :param filename: keyfile路径
    """
    with open(keyfile, 'r') as f:
        keystore = json.loads(f.read())
        if not keys.check_keystore_json(keystore):
            raise ValueError('invalid keyfile format')
        return keys.decode_keystore_json(keystore, password)


def create_keyfile(password, filename=None):
    """创建钱包keyfile
    """
    account = Account.create("")
    private_key = account.privateKey
    address = account.address
    keyfile_json = keys.make_keystore_json(private_key, password, kdf='scrypt')
    keyfile_json['id'] = str(keyfile_json['id'], encoding='utf-8')
    keyfile_json['address'] = address
    if not filename:
        isotime = dt.datetime.now().isoformat()
        filename = f'UTC--{isotime}--{address}'
    try:
        oldumask = os.umask(0)
        fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(keyfile_json, f)
    except IOError as e:
        print(e)
    else:
        return address, private_key
    finally:
        os.umask(oldumask)
