import urllib3
import time
import sys
import random
from loguru import logger
from modules.bridge import Bridge
from utilitites.common import read_files, check_gas
from utilitites.constants import ETH_NETWORKS
from config import PRIVATE_KEYS_RANDOM_MOD, PAUSE, SOURCE_CHAIN
from concurrent.futures import ThreadPoolExecutor


def configuration():
    urllib3.disable_warnings()
    logger.remove()
    logger.add(sys.stdout, colorize=True,
               format="<light-cyan>{time:HH:mm:ss}</light-cyan> | <level> {level: <8}</level> | - <white>{"
                      "message}</white>")


def main():
    configuration()
    private_keys = read_files()

    if PRIVATE_KEYS_RANDOM_MOD == "shuffle":
        random.shuffle(private_keys)

    num_threads = int(input("Enter the number of threads: "))
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for index, private_key in enumerate(private_keys):
            if SOURCE_CHAIN in ETH_NETWORKS:
                check_gas()
            bridge = Bridge(index + 1, private_key)
            executor.submit(bridge.bridge)
            time.sleep(random.randint(PAUSE[0], PAUSE[1]))

if __name__ == "__main__":
    main()
