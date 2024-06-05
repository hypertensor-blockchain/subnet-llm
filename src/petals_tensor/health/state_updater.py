import datetime
import threading
import time
from dataclasses import asdict, is_dataclass
from enum import Enum

import hivemind
import simplejson
# from flask import Flask, render_template

# import config
from .config import *
# from .health_v1 import fetch_health_state
from .health_v2 import fetch_health_state2, get_online_peers
from .metrics import get_prometheus_metrics

logger = hivemind.get_logger(__name__)

# python src/petals/health/state_updater.py

class StateUpdaterThread(threading.Thread):
    def __init__(self, dht: hivemind.DHT, **kwargs):
        super().__init__(**kwargs)
        self.dht = dht
        # self.app = app

        self.state_json = self.state_html = None
        self.ready = threading.Event()

    def run(self):
        start_time = time.perf_counter()
        # try:
        #     # state_dict = fetch_health_state(self.dht)
        #     # print("state_dict", state_dict)
        #     state_dict = fetch_health_state2(self.dht)

        #     self.state_json = simplejson.dumps(state_dict, indent=2, ignore_nan=True, default=json_default)

        #     # self.ready.set()
        #     logger.info(f"Fetched new state in {time.perf_counter() - start_time:.1f} sec")
        # except Exception:
        #     logger.error("Failed to update state:", exc_info=True)
        # self.exit()

    # def run(self):
    #     while True:
    #         start_time = time.perf_counter()
    #         try:
    #             # state_dict = fetch_health_state(self.dht)
    #             # print("state_dict", state_dict)
    #             state_dict = fetch_health_state2(self.dht)

    #             self.state_json = simplejson.dumps(state_dict, indent=2, ignore_nan=True, default=json_default)

    #             self.ready.set()
    #             logger.info(f"Fetched new state in {time.perf_counter() - start_time:.1f} sec")
    #         except Exception:
    #             logger.error("Failed to update state:", exc_info=True)

    #         delay = UPDATE_PERIOD - (time.perf_counter() - start_time)
    #         if delay < 0:
    #             logger.warning("Update took more than update_period, consider increasing it")
    #         time.sleep(max(delay, 0))

class StateUpdaterThreadV2():
    def __init__(self, dht: hivemind.DHT, **kwargs):
        super().__init__(**kwargs)
        self.dht = dht

    def run(self):
        try:
            state_dict = fetch_health_state2(self.dht)
            return state_dict
        except:
            return None

def json_default(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Enum):
        return value.name.lower()
    if isinstance(value, hivemind.PeerID):
        return value.to_base58()
    if isinstance(value, datetime.datetime):
        return value.timestamp()
    raise TypeError(f"Can't serialize {repr(value)}")

# def get_peers_data():
#     dht = hivemind.DHT(initial_peers=INITIAL_PEERS, client_mode=True, num_workers=32, start=True)
#     # updater = StateUpdaterThread(dht, daemon=True)
#     # updater.start()
#     # updater.ready.wait()
#     state_dict = fetch_health_state2(dht)
#     return state_dict

def get_peers_data():
    try:
        dht = hivemind.DHT(initial_peers=INITIAL_PEERS, client_mode=True, num_workers=32, start=True)
        # updater = StateUpdaterThread(dht, daemon=True)
        # updater.start()
        # updater.ready.wait()
        state_dict = fetch_health_state2(dht)
        return state_dict
    except Exception as error:
        logger.error("Failed to get peers data:", error)
        return None

def get_peer_ids_list():
    try:
        dht = hivemind.DHT(initial_peers=INITIAL_PEERS, client_mode=True, num_workers=32, start=True)
        # updater = StateUpdaterThread(dht, daemon=True)
        # updater.start()
        # updater.ready.wait()
        state_dict = get_online_peers(dht)
        return state_dict
    except Exception as error:
        logger.error("Failed to get peers list:", error)
        return None