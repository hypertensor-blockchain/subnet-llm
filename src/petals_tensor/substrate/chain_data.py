from enum import Enum
import scalecodec
from dataclasses import dataclass
from scalecodec.base import RuntimeConfiguration, ScaleBytes
from typing import List, Tuple, Dict, Optional, Any, TypedDict, Union
from scalecodec.type_registry import load_type_registry_preset
from scalecodec.utils.ss58 import ss58_encode

U16_MAX = 65535
U64_MAX = 18446744073709551615

def U16_NORMALIZED_FLOAT(x: int) -> float:
  return float(x) / float(U16_MAX)

def U64_NORMALIZED_FLOAT(x: int) -> float:
  return float(x) / float(U64_MAX)

custom_rpc_type_registry = {
  "types": {
    "ModelPeerData": {
      "type": "struct",
      "type_mapping": [
          ["account_id", "AccountId"],
          ["peer_id", "Vec<u8>"],
          ["ip", "Vec<u8>"],
          ["port", "u16"],
          ["initialized", "u64"],
      ],
    },
  }
}

class ParamWithTypes(TypedDict):
  name: str  # Name of the parameter.
  type: str  # ScaleType string of the parameter.

def _encode_params(
  self,
  call_definition: List[ParamWithTypes],
  params: Union[List[Any], Dict[str, Any]],
) -> str:
  """
  Returns a hex encoded string of the params using their types.
  """
  param_data = ScaleBytes(b"")

  for i, param in enumerate(call_definition["params"]):  # type: ignore
    scale_obj = self.substrate.create_scale_object(param["type"])
    if type(params) is list:
      param_data += scale_obj.encode(params[i])
    else:
      if param["name"] not in params:
          raise ValueError(f"Missing param {param['name']} in params dict.")

      param_data += scale_obj.encode(params[param["name"]])

  return param_data.to_hex()

class ChainDataType(Enum):
  ModelPeerData = 1

def from_scale_encoding(
    input: Union[List[int], bytes, ScaleBytes],
    type_name: ChainDataType,
    is_vec: bool = False,
    is_option: bool = False,
) -> Optional[Dict]:
    type_string = type_name.name
    # if type_name == ChainDataType.DelegatedInfo:
      # DelegatedInfo is a tuple of (DelegateInfo, Compact<u64>)
      # type_string = f"({ChainDataType.DelegateInfo.name}, Compact<u64>)"
    if is_option:
      type_string = f"Option<{type_string}>"
    if is_vec:
      type_string = f"Vec<{type_string}>"

    return from_scale_encoding_using_type_string(input, type_string)

def from_scale_encoding_using_type_string(
  input: Union[List[int], bytes, ScaleBytes], type_string: str
) -> Optional[Dict]:
  if isinstance(input, ScaleBytes):
    as_scale_bytes = input
  else:
    if isinstance(input, list) and all([isinstance(i, int) for i in input]):
      vec_u8 = input
      as_bytes = bytes(vec_u8)
    elif isinstance(input, bytes):
      as_bytes = input
    else:
      raise TypeError("input must be a List[int], bytes, or ScaleBytes")

    as_scale_bytes = scalecodec.ScaleBytes(as_bytes)

  rpc_runtime_config = RuntimeConfiguration()
  rpc_runtime_config.update_type_registry(load_type_registry_preset("legacy"))
  rpc_runtime_config.update_type_registry(custom_rpc_type_registry)

  obj = rpc_runtime_config.create_scale_object(type_string, data=as_scale_bytes)

  return obj.decode()

# Dataclasses for chain data.
@dataclass
class ModelPeerData:
  """
  Dataclass for neuron metadata.
  """

  account_id: str
  peer_id: str
  ip: str
  port: int
  initialized: int

  @classmethod
  def fix_decoded_values(cls, model_peer_data_decoded: Any) -> "ModelPeerData":
    """Fixes the values of the ModelPeerData object."""
    model_peer_data_decoded["account_id"] = ss58_encode(
      model_peer_data_decoded["account_id"], 42
    )
    model_peer_data_decoded["peer_id"] = model_peer_data_decoded["peer_id"]
    model_peer_data_decoded["ip"] = model_peer_data_decoded["ip"]
    model_peer_data_decoded["port"] = model_peer_data_decoded["port"]
    model_peer_data_decoded["initialized"] = model_peer_data_decoded["initialized"]

    return cls(**model_peer_data_decoded)

  @classmethod
  def from_vec_u8(cls, vec_u8: List[int]) -> "ModelPeerData":
    """Returns a ModelPeerData object from a ``vec_u8``."""

    if len(vec_u8) == 0:
      return ModelPeerData._null_model_peer_data()

    decoded = from_scale_encoding(vec_u8, ChainDataType.ModelPeerData)

    if decoded is None:
      return ModelPeerData._null_model_peer_data()

    decoded = ModelPeerData.fix_decoded_values(decoded)

    return decoded

  @classmethod
  def list_from_vec_u8(cls, vec_u8: List[int]) -> List["ModelPeerData"]:
    """Returns a list of ModelPeerData objects from a ``vec_u8``."""

    decoded_list = from_scale_encoding(
      vec_u8, ChainDataType.ModelPeerData, is_vec=True
    )
    if decoded_list is None:
      return []

    decoded_list = [
      ModelPeerData.fix_decoded_values(decoded) for decoded in decoded_list
    ]
    return decoded_list

  @staticmethod
  def _null_model_peer_data() -> "ModelPeerData":
    model_peer_data = ModelPeerData(
      account_id="000000000000000000000000000000000000000000000000",
      peer_id=0,
      ip=0,
      port=0,
      initialized=0,
    )
    return model_peer_data

  @staticmethod
  def _model_peer_data_to_namespace(model_peer_data) -> "ModelPeerData":
    # TODO: Legacy: remove?
    if model_peer_data["account_id"] == "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM":
      return ModelPeerData._null_model_peer_data()
    else:
      neuron = ModelPeerData(**model_peer_data)

      return neuron

