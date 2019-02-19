import os
from source.config.wallet_config import WalletConfig

config = WalletConfig(os.environ["coin_type"], os.environ.get("coin_category", None))
