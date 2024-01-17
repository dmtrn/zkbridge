import random
import time
from loguru import logger
from eth_account import Account
from web3 import Web3, exceptions
from web3.middleware import geth_poa_middleware
from config import SOURCE_CHAIN, DST_CHAIN, AMOUNT
from utilitites.constants import DST_CHAINS, RPCS, CONTRACT_ADDRESSES, ABI, SCAN_LINKS, NATIVE_TOKEN_POOL_IDS


class Bridge:
    def __init__(self, index, private_key) -> None:
        self.index = index
        self.private_key = private_key
        self.wallet = Account.from_key(private_key)
        self.address = self.wallet.address
        self.w3 = Web3(Web3.HTTPProvider(RPCS[SOURCE_CHAIN]))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.contract = self.w3.eth.contract(address=CONTRACT_ADDRESSES[SOURCE_CHAIN], abi=ABI)

    def getFee(self, amount):
        try:
            estimated_fee = self.contract.functions.estimateFee(
                NATIVE_TOKEN_POOL_IDS[SOURCE_CHAIN], 
                DST_CHAINS[DST_CHAIN], 
                amount
            ).call()
            return estimated_fee
        except exceptions.Web3Exception as e:
            logger.error(f"{self.index} | {self.address} | Error in getFee: {e}")
            return None

    def bridge(self, retry_limit=3, retry_delay=5):
        amount = Web3.to_wei(random.uniform(AMOUNT[0], AMOUNT[1]), "ether")
        fee = self.getFee(amount)
        if fee is None:
            time.sleep(retry_delay)
            self.getFee(amount)

        totalAmount = amount + fee
        retry_count = 0
        balance = self.w3.eth.get_balance(self.address)
        while retry_count < retry_limit:
            try:
                transaction = self.contract.functions.transferETH(DST_CHAINS[DST_CHAIN], amount, self.address)
                overrides = {
                    'from': Web3.to_checksum_address(self.address),
                    'nonce': self.w3.eth.get_transaction_count(Web3.to_checksum_address(self.address)),
                    'gas': int(transaction.estimate_gas({'from': self.address, 'value': totalAmount}) * 1.3),
                    'value': totalAmount
                }
                if SOURCE_CHAIN == "bsc":
                    overrides["gasPrice"] = Web3.to_wei(round(random.uniform(1.01, 1.1), 2), "gwei")
                built_transaction = transaction.build_transaction(overrides)
                signed_tx = self.w3.eth.account.sign_transaction(built_transaction, self.private_key)
                receipt = self.w3.eth.wait_for_transaction_receipt(self.w3.eth.send_raw_transaction(signed_tx.rawTransaction))
                if receipt.status != 1:
                    logger.error(f"{self.index} | {self.address} | Bridge Failed: {SCAN_LINKS[SOURCE_CHAIN]}{receipt.transactionHash.hex()}")
                else:
                    logger.success(f"{self.index} | {self.address} | Successfully bridged: {SCAN_LINKS[SOURCE_CHAIN]}{receipt.transactionHash.hex()}")
                    return True
            except exceptions.Web3Exception as e:
                logger.error(f"{self.index} | {self.address} | Error in bridging attempt {retry_count + 1}: {e}")
                retry_count += 1
                time.sleep(retry_delay)

        logger.error(f"{self.index} | {self.address} | Failed to bridge after {retry_limit} attempts.")
        return False
    
