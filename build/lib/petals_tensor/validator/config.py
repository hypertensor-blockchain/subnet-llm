import dataclasses
import os
from typing import List, Optional, Sequence, Union

from hivemind import PeerID
import torch

from petals_tensor.constants import PUBLIC_INITIAL_PEERS

_max_retries = os.getenv("PETALS_MAX_RETRIES")
# DEFAULT_MAX_RETRIES = int(_max_retries) if isinstance(_max_retries, str) else None
DEFAULT_MAX_RETRIES = int(_max_retries) if isinstance(_max_retries, str) else 10


@dataclasses.dataclass
class ClientConfig:
    initial_peers: Sequence[str] = tuple(PUBLIC_INITIAL_PEERS)  # a list of initial peers for hivemind DHT
    dht_prefix: Optional[str] = None  # a prefix for all dht keys that correspond to this model (default: model name)
    daemon_startup_timeout: int = 60  # timeout for the libp2p daemon connecting to initial peers

    show_route: Union[str, bool] = "inference"  # show chosen route through servers. one of [False, "inference", True]
    allowed_servers: Optional[Sequence[Union[PeerID, str]]] = None  # if defined, send requests only to these servers
    blocked_servers: Optional[Sequence[Union[PeerID, str]]] = None  # if defined, do not use these servers
    use_server_to_server: bool = True  # Use direct server-to-server communication

    connect_timeout: float = 5  # timeout for opening a connection
    request_timeout: float = 3 * 60  # timeout for forward/backward/inference requests
    update_period: float = 60  # refresh DHT information once in this many seconds

    max_retries: Optional[int] = DEFAULT_MAX_RETRIES  # max number of retries before an exception (default: inf)
    min_backoff: float = 1  # after a repeated failure, sleep for this many seconds times 2 ** (num_failures - 1)
    max_backoff: float = 60  # limit maximal sleep time between retries to this value
    ban_timeout: float = 15  # when a remote peer fails to respond, prevent routing to that peer for this many seconds
    active_adapter: Optional[str] = None  # name of active LoRA adapter (usually, Hugging Face repo)

    max_pinged: int = 3  # max servers to ping from each sequence side, per update
    ping_timeout: float = 2  # max time to wait for pings, per update

@dataclasses.dataclass
class PeerInferenceSequenceData:
    """Class for storing node inferece and sequence data."""
    peer_id: PeerID # Peer ID of node accountant is checking inference of
    span_start: int # Start span of node accountant is checking inference of
    span_end: int # End span of node accountant is checking inference of
    accountant_tensor_sum: float # Tensor sum of the accountant performing inference validation
    tensor_sum: float # Tensor sum of the node accountant is checking inference of
    accountant_tensor: str
    peer_tensor: str
    valid: bool # If accountant deems node checking inference of is valid

@dataclasses.dataclass
class AccountantDataPeerParams:
    """Copy of struct from Hypertensor blockchain required format for accountants to submit data as"""
    peer_id: PeerID
    data: PeerInferenceSequenceData

@dataclasses.dataclass
class AccountantDataCompare:
    """Interface for submitting proposal for dishonest accountant data comparison"""
    accountant_data_id: int
    accountant_data: List[AccountantDataPeerParams] # Parts of accountant data to propose as dishonest
    proposer_data: List[AccountantDataPeerParams] # Parts of data to compare to accountant_data that should have been submitted

"""Accountant data comprising of each peers inference data"""
class AccountantData:
    def __init__(self):
        self.data = []
        self.epoch = 0

    def add_data(self, data: AccountantDataPeerParams):
        self.data.append(data)

    def reset(self):
        self.data = []
