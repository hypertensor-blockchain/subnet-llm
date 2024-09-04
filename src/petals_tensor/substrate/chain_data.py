from enum import Enum
import json
import scalecodec
from dataclasses import dataclass
from scalecodec.base import RuntimeConfiguration, ScaleBytes
from typing import List, Tuple, Dict, Optional, Any, TypedDict, Union
from scalecodec.type_registry import load_type_registry_preset
from scalecodec.utils.ss58 import ss58_encode
from hivemind import PeerID

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
  """
  TypedDict for a parameter with its types.
  """
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
  """
  Enum for chain data types.
  """
  ModelPeerData = 1

def from_scale_encoding(
    input: Union[List[int], bytes, ScaleBytes],
    type_name: ChainDataType,
    is_vec: bool = False,
    is_option: bool = False,
) -> Optional[Dict]:
    """
    Returns the decoded data from the SCALE encoded input.

    Args:
      input (Union[List[int], bytes, ScaleBytes]): The SCALE encoded input.
      type_name (ChainDataType): The ChainDataType enum.
      is_vec (bool): Whether the input is a Vec.
      is_option (bool): Whether the input is an Option.

    Returns:
      Optional[Dict]: The decoded data
    """
    
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
  """
  Returns the decoded data from the SCALE encoded input using the type string.

  Args:
    input (Union[List[int], bytes, ScaleBytes]): The SCALE encoded input.
    type_string (str): The type string.

  Returns:
    Optional[Dict]: The decoded data
  """
  
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
  Dataclass for model peer metadata.
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
    """
    Returns a ModelPeerData object with null values.
    """

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
    """
    Converts a ModelPeerData object to a namespace.

    Args:
      model_peer_data (ModelPeerData): The ModelPeerData object.

    Returns:
      ModelPeerData: The ModelPeerData object.
    """

    # TODO: Legacy: remove?
    if model_peer_data["account_id"] == "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM":
      return ModelPeerData._null_model_peer_data()
    else:
      neuron = ModelPeerData(**model_peer_data)

      return neuron

###

# Dataclasses for chain data.
@dataclass
class AccountantDataParams:
  """
  Dataclass for accountant data
  """

  peer_id: PeerID
  span_start: int
  span_end: int
  accountant_tensor_sum: float
  tensor_sum: float
  valid: bool

  @classmethod
  def fix_decoded_values(cls, accountant_data_decoded: Any) -> "AccountantDataParams":
    """Fixes the values of the AccountantDataParams object."""

    accountant_data_decoded["peer_id"] = accountant_data_decoded["peer_id"]
    accountant_data_decoded["span_start"] = accountant_data_decoded["span_start"]
    accountant_data_decoded["span_end"] = accountant_data_decoded["span_end"]
    accountant_data_decoded["accountant_tensor_sum"] = accountant_data_decoded["accountant_tensor_sum"]
    accountant_data_decoded["tensor_sum"] = accountant_data_decoded["tensor_sum"]
    accountant_data_decoded["valid"] = accountant_data_decoded["valid"]

    return cls(**accountant_data_decoded)

  @classmethod
  def list_from_vec_u8(cls, vec_u8: List[int]) -> List["AccountantDataParams"]:
    """Returns a list of AccountantDataParams objects from a ``vec_u8``."""
    """The data is arbitrary so we don't count on a struct"""

    decoded_list: List[AccountantDataParams] = []

    # Convert arbitrary data to str
    list_of_ord_values = ''.join(chr(i) for i in vec_u8)

    # Replace ' to " for json
    list_of_ord_values = list_of_ord_values.replace("\'", "\"")

    json_obj = json.loads(list_of_ord_values)

    for x in json_obj:
      accountant_data_params = AccountantDataParams(*x)
      decoded_list.append(accountant_data_params)

    return decoded_list

@dataclass
class AccountIdList:
  """
  Dataclass for AccountId lists
  """
  @classmethod
  def list_from_vec_u8(cls, vec_u8: List[int]) -> List["AccountIdList"]:
    """Returns a list of AccountIdList objects from a ``vec_u8``."""
    """The data is arbitrary so we don't count on a struct"""

    decoded_list: List[AccountIdList] = []

    # Convert arbitrary data to str
    list_of_ord_values = ''.join(chr(i) for i in vec_u8)

    # Replace ' to " for json
    list_of_ord_values = list_of_ord_values.replace("\'", "\"")

    json_obj = json.loads(list_of_ord_values)

    for x in json_obj:
      accountant_data_params = AccountIdList(*x)
      decoded_list.append(accountant_data_params)

    return decoded_list