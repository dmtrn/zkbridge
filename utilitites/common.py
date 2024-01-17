import time
from web3 import Web3
from utilitites.constants import RPCS
from config import MAX_GWEI
from loguru import logger


def read_files():
    with open("./data/private_keys.txt") as file:
        private_keys = [line.strip() for line in file if line.strip()]
    return private_keys

def check_gas():
    w3 = Web3(Web3.HTTPProvider(RPCS["eth"]))
    while True:
        try:
            current_gas_price_wei = w3.eth.gas_price
            current_gas_price_gwei = current_gas_price_wei / 1e9
            logger.info(f"Current gas price: {current_gas_price_gwei} Gwei")

            if current_gas_price_gwei <= MAX_GWEI:
                logger.info("Gas price is within the limit. Proceeding with the transaction.")
                break
            else:
                logger.info(f"Gas price is too high: {current_gas_price_gwei} Gwei. Waiting for 30 seconds to recheck.")
                time.sleep(30)
        except Exception as e:
            logger.error(f"Error checking gas price: {e}")
            time.sleep(30)
            
