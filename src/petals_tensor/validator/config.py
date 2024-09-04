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

"""ACCOUNTANT CONFIG"""
@dataclasses.dataclass
class CustomInferenceSequence:
    peer_id: PeerID
    start: int
    end: int

@dataclasses.dataclass
class AccountantConfig:
    start_block: int                        # The start block to validate against
    end_block: int                          # The end block to validate against
    sequence: List[CustomInferenceSequence] # The custom sequence of nodes to validate

"""BLOCKCHAIN CONFIG"""
@dataclasses.dataclass
class PeerInferenceSequenceData:
    """Class for storing node inferece and sequence data."""
    position: int                # Position of sequence
    accountant_tensor_sum: float # Tensor sum of the accountant performing inference validation
    tensor_sum: float            # Tensor sum of the node accountant is checking inference of
    valid: bool                  # Accountant data validation result of position

@dataclasses.dataclass
class PeerInferenceResults:
    span_start: int              # Start span of node
    span_end: int                # End span of node
    data: List[PeerInferenceSequenceData]

# @dataclasses.dataclass
# class PeerInferenceSequenceData:
#     """Class for storing node inferece and sequence data."""
#     peer_id: PeerID              # Peer ID of node accountant is checking inference of
#     position: int                # Position of sequence
#     span_start: int              # Start span of node accountant is checking inference of
#     span_end: int                # End span of node accountant is checking inference of
#     accountant_tensor_sum: float # Tensor sum of the accountant performing inference validation
#     tensor_sum: float            # Tensor sum of the node accountant is checking inference of
#     valid: bool                  # If accountant deems node checking inference of is valid

@dataclasses.dataclass
class PeerValidationData:
    """
    input_tensor: Input tensor validating off of
    a_tol: Absolute tolerance used in allclose
    r_tol: Relative tolerance used in allclose
    data: Inference sequence data of each position the peer was assigned
    """
    input_tensor: Union[torch.Tensor, None] # Input tensor validating of
    a_tol: float
    r_tol: float
    data: List[PeerInferenceResults]        # Array of each sequence position

@dataclasses.dataclass
class AccountantDataPeerParams:
    """
    Copy of struct from Hypertensor blockchain required format for accountants to submit data as

    peer_id: PeerID of peer inference validation results
    valid: Accountant overall data validation results
    data: Inference sequence data of each position the peer was assigned
    """
    peer_id: PeerID
    valid: bool
    data: List[PeerValidationData]

"""Accountant data comprising of each peers inference data"""
class AccountantData:
    def __init__(self):
        self.data = []
        self.epoch = 0

    def add_data(self, data: AccountantDataPeerParams):
        self.data.append(data)

    def reset(self):
        self.data = []

@dataclasses.dataclass
class AccountantDataCompare:
    """Interface for submitting proposal for dishonest accountant data comparison"""
    accountant_data_id: int                         # ID of the blockchains accountant data submission
    accountant_data: List[AccountantDataPeerParams] # Parts of accountant data to propose as dishonest
    proposer_data: List[AccountantDataPeerParams]   # Parts of data to compare to accountant_data that should have been submitted