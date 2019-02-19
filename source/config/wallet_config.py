# @Author  : xy.zhang
# @Email   : zhangxuyi@wanshare.com
# @Time    : 19-1-29

import os
import json
from source.common.utils.log import get_logger
import os


logger = get_logger('wallet-config')


NECESSARY_ENV = ["wallet_user", "wallet_password", "database_uri", "rpc_host", "rpc_port", "coin_type"]


class WalletConfig:
    
    def __init__(self, coin_type, coin_category):
        self.coin_type = coin_type.lower()
        self.coin_category = coin_category.lower() if coin_category else None
        cwd = os.path.dirname(os.path.abspath(__file__))
        self.config_json = None
        with open(f"{cwd}/{self.coin_type}.json") as f:
            json_str = f.read()
            self.config_json = json.loads(json_str)
        
        if self.config_json['production']:
            for env_name in NECESSARY_ENV:
                try:
                    del self.config_json[env_name]
                except KeyError as e:
                    logger.info("Delete %s in config" % env_name)
        else:
            os.environ['wallet_user'] = self.config_json['wallet_user']
            os.environ['wallet_password'] = self.config_json['wallet_password']
        if os.environ['wallet_user']:
            self.config_json["rpc_uri"] = "http://%s:%s@%s:%s" % (
                os.environ['wallet_user'], os.environ['wallet_password'], os.environ['rpc_host'], os.environ['rpc_port'])
        else:
            self.config_json["rpc_uri"] = "http://%s:%s" % (
                os.environ['rpc_host'],
                os.environ['rpc_port'])
        
    def __getattr__(self, item):
        if item not in self.config_json:
            logger.warning(f"item:{item} not in {self.coin_type}.json, try env")
            res = os.environ.get(item, None)
            if res is None:
                raise AttributeError
            else:
                return res
        else:
            return self.config_json[str(item)]



