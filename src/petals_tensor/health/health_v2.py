import datetime
import time
from collections import Counter
from contextlib import suppress
from dataclasses import asdict
from functools import partial
from typing import List

import hivemind
import numpy as np
from multiaddr import Multiaddr
from petals_tensor.data_structures import UID_DELIMITER, ServerState
from petals_tensor.utils.dht import compute_spans, get_remote_module_infos

# import config
from .config import *
from .data_structures import ModelInfo
from .p2p_utils import check_reachability_parallel, get_peers_ips, extract_peer_ip_info

logger = hivemind.get_logger(__name__)


def fetch_health_state2(dht: hivemind.DHT) -> dict:
    start_time = time.perf_counter()
    bootstrap_peer_ids = []
    for addr in INITIAL_PEERS:
        peer_id = hivemind.PeerID.from_base58(Multiaddr(addr)["p2p"])
        if peer_id not in bootstrap_peer_ids:
            bootstrap_peer_ids.append(peer_id)

    reach_infos = dht.run_coroutine(partial(check_reachability_parallel, bootstrap_peer_ids))
    bootstrap_states = ["online" if reach_infos[peer_id]["ok"] else "unreachable" for peer_id in bootstrap_peer_ids]

    model = MODEL

    logger.info(f"Fetching info for models {model}")

    block_uids = [f"{model.dht_prefix}{UID_DELIMITER}{i}" for i in range(model.num_blocks)]
    module_infos = get_remote_module_infos(dht, block_uids, latest=True)

    all_servers = {}
    offset = 0
    model_servers = compute_spans(
        module_infos[offset : offset + model.num_blocks], min_state=ServerState.OFFLINE
    )
    all_servers.update(model_servers)

    offset += model.num_blocks

    online_servers = [peer_id for peer_id, span in all_servers.items() if span.state == ServerState.ONLINE]

    reach_infos.update(dht.run_coroutine(partial(check_reachability_parallel, online_servers, fetch_info=True)))
    peers_info = {str(peer.peer_id): {"location": extract_peer_ip_info(str(peer.addrs[0])), "multiaddrs": [str(multiaddr) for multiaddr in peer.addrs]} for peer in dht.run_coroutine(get_peers_ips)}

    model_reports = []
    block_healthy = np.zeros(model.num_blocks, dtype=bool)
    server_rows = []
    for peer_id, span in sorted(model_servers.items()):
        reachable = reach_infos[peer_id]["ok"] if peer_id in reach_infos else True
        state = span.state.name.lower() if reachable else "unreachable"

        # only append online model validators
        if state == "online":
            block_healthy[span.start : span.end] = True
            peer_num_blocks = span.length
            throughput = span.throughput

            """
                Using relay shows whether a server is reachable directly or we need to 
                use libp2p relays to traverse NAT/firewalls and reach it. Servers 
                available through relays are usually slower, so we don't store DHT keys on them.

                @to-do: If `using_relay` lessen score by `x%`
            """
            using_relay = span.server_info.using_relay
            """
                score is peer_num_blocks / model_num_blocks

                example:
                if a peer #1 is hosting 80 out of 80 blocks they have a score of 100.0
                if a peer #2 is hosting 20 out of 80 blocks they have a score of 20.0

                once on the blockchain, this is summed to:
                scores_sum: 100.0
                peer #1 score is 80.0
                peer #2 score is 20.0

                we don't sum here to avoid unneccessary computations
                the blockchains scoring mechanism is arbitrary and isn't reliant on being  `100.00`
            """
            score = int(peer_num_blocks / model.num_blocks * 1e4)

            """
                Relay servers are slower than direct servers so we lessen the score

                This ultimately incentivizes servers to be direct to result in a more efficient DHT
            """
            if using_relay:
                score = int(score - score * 0.33)

            logger.info(f"Peer ID -> {peer_id}")
            logger.info(f"Score   -> {score}")

            row = {
                "peer_id": peer_id,
                "peer_ip_info": peers_info.get(str(peer_id), "unknown"),
                "state": state,
                "span": span,
                "score": score,
                "using_relay": using_relay,
                "adapters": [dict(name=name, short_name=name.split("/")[-1]) for name in span.server_info.adapters],
                "pings_to_me": {
                    str(origin_id): origin.server_info.next_pings[str(peer_id)]
                    # for origin_id, origin in model_servers[model.dht_prefix].items()
                    for origin_id, origin in model_servers.items()
                    if origin.server_info.next_pings is not None and str(peer_id) in origin.server_info.next_pings
                },
            }
            if span.server_info.cache_tokens_left is not None:
                # We use num_blocks * 2 to account for both keys and values
                row["cache_tokens_left_per_block"] = span.server_info.cache_tokens_left // (span.length * 2)
            server_rows.append(row)

    model_reports.append(
        dict(
            name=model.name,
            short_name=model.short_name,
            state="healthy" if block_healthy.all() else "broken",
            server_rows=server_rows,
            model_num_blocks=model.num_blocks,
            **asdict(model),
        )
    )

    reachability_issues = [
        dict(peer_id=peer_id, err=info["error"]) for peer_id, info in sorted(reach_infos.items()) if not info["ok"]
    ]

    return dict(
        bootstrap_states=bootstrap_states,
        model_reports=model_reports,
        reachability_issues=reachability_issues,
        last_updated=datetime.datetime.now(datetime.timezone.utc),
        update_period=UPDATE_PERIOD,
        update_duration=time.perf_counter() - start_time
    )

def get_online_peers(dht: hivemind.DHT) -> List:
    bootstrap_peer_ids = []
    for addr in INITIAL_PEERS:
        peer_id = hivemind.PeerID.from_base58(Multiaddr(addr)["p2p"])
        if peer_id not in bootstrap_peer_ids:
            bootstrap_peer_ids.append(peer_id)

    model = MODEL

    logger.info(f"Fetching online peers for model {model}")

    block_uids = [f"{model.dht_prefix}{UID_DELIMITER}{i}" for i in range(model.num_blocks)]
    module_infos = get_remote_module_infos(dht, block_uids, latest=True)

    all_servers = {}
    offset = 0
    model_servers = compute_spans(
        module_infos[offset : offset + model.num_blocks], min_state=ServerState.OFFLINE
    )
    all_servers.update(model_servers)

    offset += model.num_blocks

    online_servers = [peer_id for peer_id, span in all_servers.items() if span.state == ServerState.ONLINE]

    return online_servers