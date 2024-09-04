




import time
from petals_tensor.substrate.chain_functions import cast_vote, execute_proposal, get_subnet_proposal, get_subnet_proposals_count
from propose import propose_activate
from test_utils import PEER_IDS, get_substrate_config
from petals_tensor.substrate.config import BLOCK_SECS

# python src/petals_tensor/substrate/tests/democracy/execute.py
def test_execute_activate():
  print("hi")
  receipt = propose_activate(0)
  proposal_index = 0
  print("propose_activate done")

  count = len(PEER_IDS)
  print("PEER_IDS count", count)

  for i in range(0, 12):
    substrate_config = get_substrate_config(i)
    cast_vote(
      substrate_config.interface,
      substrate_config.keypair,
      proposal_index,
      1000e18,
      "Yay"
    )
    print("vote", i)

  print("voting done")
  substrate_config = get_substrate_config(1)
  next_props_index = get_subnet_proposals_count(substrate_config.interface)
  print("next_props_index", next_props_index)
  props_index = int(str(next_props_index)) - 1
  proposal = get_subnet_proposal(substrate_config.interface, props_index)
  print("proposal", proposal)
  max_block = proposal['max_block']
  print("max_block", max_block)

  while True:
    print("waiting for execution block")
    time.sleep(BLOCK_SECS)
    block_hash = substrate_config.interface.get_block_hash()
    block_number = substrate_config.interface.get_block_number(block_hash)
    print("block_number", block_number)
    if block_number > max_block:
      execute_proposal(
        substrate_config.interface,
        substrate_config.keypair,
        props_index,
      )
      break


if __name__ == "__main__":
  test_execute_activate()