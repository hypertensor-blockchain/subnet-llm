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

# source .venv/bin/activate
# python src/petals/substrate/test.py

print("starting")

# import logging
# logging.basicConfig(level=logging.DEBUG)

# substrate = SubstrateInterface(url=SubstrateConfig.url)
# keypair_alice = Keypair.create_from_uri('//Alice', ss58_format=substrate.ss58_format)
# print(keypair_alice.ss58_address)

# keypair = Keypair.create_from_uri('//Alice')

# print("keypair => ", keypair)
# print("keypair ss58_address => ", keypair.ss58_address)

# keypair_1 = Keypair.create_from_uri('//1')
# print("keypair_1 => ", keypair_1)
# print("keypair_1 ss58_address => ", keypair_1.ss58_address)

# "5D34dL5prEUaGNQtPPZ3yN5Y6BnkfXunKXXz6fo7ZJbLwRRH"

# account_info = substrate.query(
#   module='Network',
#   storage_function='TotalModels',
# )

# path = "petals-team/StableBeluga2"
# path_as_vec = list(path.encode('ascii'))

# path_as_bytes = str.encode(path)
# print(type(path_as_bytes)) # ensure it is byte representation
# print(path_as_bytes) # ensure it is byte representation

# my_decoded_str = path_as_bytes.decode()
# print(type(my_decoded_str)) # ensure it is string representation

# model_peers_data = substrate.rpc_request(
#   method='network_getModelPeers',
#   params=[
#     1
#   ]
# ).get('result')
# model_id = 1

# model_peers_data = substrate.rpc_request(
#   method='network_getModelPeers',
#   params=[
#     model_id
#   ]
# )

# def filterbyvalue(seq, value):
#   for el in seq:
#     if el.attribute==value: yield el
# async def async_consensus_data(self):
#     try:
#         consensus_data = await get_consensus_data(SubstrateConfig.interface, 1)
#         return consensus_data
#     except:
#         raise Exception(some_identifier_here + ' ' + traceback.format_exc())

try:
  # model_peers_data = SubstrateConfig.interface.rpc_request(
  #   method='network_getModelPeers',
  #   params=[
  #     1
  #   ]
  # )
  # print("model_peers_data", model_peers_data)

  # consensus_data_test = get_consensus_data_test(SubstrateConfig.interface, 1)
  # print("consensus_data_test", consensus_data_test)

  consensus_data = get_consensus_data(SubstrateConfig.interface, 1)
  print("consensus_data", consensus_data)

  print(consensus_data["model_state"])
  print(consensus_data["peers"])

  # dht = hivemind.DHT(initial_peers=PUBLIC_INITIAL_PEERS, client_mode=True, start=True)

  # peers = fetch_peers(dht)
  # result = substrate.query('System', 'Account', [keypair.ss58_address])
  # print(result.value['data']['free'])
  # print(substrate.rpc_request("system_properties", []).get('result') )

  # storage_function = substrate.get_metadata_storage_function("Network", "ModelPeersData")
  # print(storage_function)
  # print(len(storage_function.get_params_type_string()))
  # param_type = substrate.create_scale_object(storage_function.get_params_type_string()[0])
  # print("param_type", storage_function.get_params_type_string()[0])

  # result_map = substrate.query_map(module='Network', storage_function='ModelPeersData')
  # print(list(result_map))

  # storage_function = substrate.get_metadata_storage_function('Network', 'ModelPeersData')
  # param_info = storage_function.get_param_info()
  # print(param_info)

  #
  #


  # check if we need to submit consensus data


  # get model validators - peers
  # result = model_peers_data["result"]
  # result_from_vec_u8 = ModelPeerData.list_from_vec_u8(result)


  # # match blockchain with hosting
  # # score hosters
  # blockchain_peers = []
  # for peer_result in result_from_vec_u8:
  #   peer_id = peer_result.peer_id 
  #   for model_peer in peers:
  #     if model_peer["peer_id"] == peer_id:
  #       print(peer_result.account_id)
  #       # print(peer_result.peer_id)
  #       dict = {
  #         "account_id": peer_result.account_id,
  #         "peer_id": peer_result.peer_id,
  #         "score": model_peer["score"],
  #       }
  #       blockchain_peers.append(dict)
  #       break

  # print("blockchain_peers", blockchain_peers)

  # Check if submitting is possible
  # can = can_submit_consensus_data(
  #   substrate, 
  #   keypair_1,
  #   0,
  #   NetworkConfig.consensus_blocks_interval,
  #   model_id,
  # )

  # print("can", can)


  # submit consensus data
  # submit_consensus_data(substrate, keypair_1, model_id, blockchain_peers)




except SubstrateRequestException as e:
  print("Failed to send: {}".format(e))