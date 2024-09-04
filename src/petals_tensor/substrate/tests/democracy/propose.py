from petals_tensor.substrate.chain_functions import propose
from test_utils import MODEL_MEMORY_MB, MODEL_PATH, get_subnet_nodes, get_substrate_config



pre_subnet_data = {
	"path": list(MODEL_PATH.encode('ascii')),
	"memory_mb": MODEL_MEMORY_MB
}

vote_subnet_data = {
	"data": pre_subnet_data,
	"active": True
}

def propose_activate(n: int):
  substrate_config = get_substrate_config(n)
  subnet_nodes = get_subnet_nodes(5)
  print('subnet nodes: ', subnet_nodes)

  print('vote_subnet_data: ', vote_subnet_data)

  receipt = propose(
    substrate_config.interface,
    substrate_config.keypair,
    pre_subnet_data,
    subnet_nodes,
    "Activate"
  )
  print('propose receipt: ', receipt)
  return receipt