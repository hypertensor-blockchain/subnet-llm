import dataclasses
import os
from substrateinterface import SubstrateInterface, Keypair
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(os.path.join(Path.cwd(), '.env'))
LOCAL_URL = os.getenv('LOCAL_RPC')
DEV_URL = os.getenv('DEV_RPC')


MODEL_PATH = "bigscience/bloom-560m"
MODEL_MEMORY_MB = 50000

PEER_IDS = [
  "QmedTaZXmULqwspJXz44SsPZyTNKxhnnFvYRajfH7MGhCY",
  "QmQGTqmM7NKjV6ggU1ZCap8zWiyKR89RViDXiqehSiCpY5",
  "12D3KooWBxMLje7yExEBhZQqbuVL1giKPpN8DieYkL3Wz7sTku7T",
  "12D3KooWEDYmpQVW6ixD7MijciZcZMuPtdrvNbeC4Jr1cxV1hJZe",
  "12D3KooWJAAqbBW3YXJE42TAGgXTRVxZwmWuqY9yBneLfsDFiA8b",
  "12D3KooWGB94YYemuff4AucWo8RfV5mzHWLZc5HvhWqBXrk2W8YN"
] 

@dataclasses.dataclass
class SubstrateConfig:
  interface: SubstrateInterface
  keypair: Keypair
  account_id: str

def get_substrate_config(n: int):
  return SubstrateConfig(
    SubstrateInterface(url=LOCAL_URL),
    Keypair.create_from_uri(f"//{str(n)}"),
    Keypair.create_from_uri(f"//{str(n)}").ss58_address
  )

@dataclasses.dataclass
class SubnetNode:
  account_id: str
  peer_id: str

def get_subnet_nodes(count: int):
  subnet_nodes = []
  for i in range(0, count):
    node = {
      'account_id': Keypair.create_from_uri(f"//{i}").ss58_address,
      'peer_id': PEER_IDS[i]
    }
    subnet_nodes.append(node)
  return subnet_nodes