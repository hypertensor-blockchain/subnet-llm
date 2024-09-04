# Python Substrate Interface Library
#
# Copyright 2018-2023 Stichting Polkascan (Polkascan Foundation).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import pytest
import hivemind
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException
from scalecodec.base import ScaleBytes, RuntimeConfiguration
from scalecodec.type_registry import load_type_registry_preset
from scalecodec.types import GenericCall
from config import NetworkConfig, SubstrateConfig

from typing import List, Dict, Union, Optional, Tuple, TypedDict, Any, TypeVar

from chain_data import ModelPeerData
from petals_tensor.constants import PUBLIC_INITIAL_PEERS
from utils import get_consensus_data, get_consensus_data_test


