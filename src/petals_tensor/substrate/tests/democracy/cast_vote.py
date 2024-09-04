




from petals_tensor.substrate.chain_functions import cast_vote
from propose import propose_activate
from test_utils import PEER_IDS, get_substrate_config


def test_cast_votes(n: int):
  receipt = propose_activate(0)
  proposal_index = 0

  count = len(PEER_IDS)

  for i in range(0, count):
    substrate_config = get_substrate_config(i)
    cast_vote(
      substrate_config.interface,
      substrate_config.keypair,
      proposal_index,
      1000e18,
      "1"
    )

if __name__ == "__main__":
  test_cast_votes(12)