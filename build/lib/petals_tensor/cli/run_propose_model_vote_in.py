""""""
import argparse
from petals_tensor.constants import PUBLIC_INITIAL_PEERS
from petals_tensor.health.state_updater import get_peer_ids_list
from petals_tensor.substrate import config as substrate_config
from petals_tensor.substrate.chain_functions import get_model_path_id

def main():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
    "--path",
    nargs="?",
    required=True,
    help="The path of the existing model. "
    "Example: petals-team/StableBeluga2 if the full path is https://huggingface.co/petals-team/StableBeluga2",
  )
  parser.add_argument('--initial_peers', type=str, nargs='+', required=True, default=PUBLIC_INITIAL_PEERS,
                      help='Multiaddrs of one or more DHT peers from the target swarm. Default: connects to the public swarm')
  parser.add_argument(
    "--amount",
    type=int, 
    required=True,
    nargs="?",
    help="The amont to vote towards a model vote in or out. "
    "Example: 10000000000000",
  )

  args = parser.parse_args()

  model_path_id = get_model_path_id(
    substrate_config.SubstrateConfig.interface,
    args.path,
  )

  assert model_path_id == 0, "Model path is already stored"

  peer_ids_list = get_peer_ids_list()

  network_config = substrate_config.load_network_config()

  min_model_peers = network_config.min_model_peers

  assert len(peer_ids_list) >= min_model_peers, "Model doesn't meet minimum required model validators hosting the model"

if __name__ == "__main__":
  main()
