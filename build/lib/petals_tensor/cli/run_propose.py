"""
If a model is successfully voted in use this cli
python -m petals_tensor.cli.run_add_model --path petals-team/Beluga2

"""
import logging

import argparse
from petals_tensor.constants import PUBLIC_INITIAL_PEERS
from petals_tensor.substrate import config as substrate_config
from petals_tensor.health.state_updater import get_peer_ids_list
from petals_tensor.substrate.chain_functions import add_model, get_model_path_id, remove_subnet

logger = logging.getLogger(__name__)

def main():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      "--path",
      nargs="?",
      required=True,
      help="The path of the existing model. "
      "Example: petals-team/StableBeluga2 if the full path is https://huggingface.co/petals-team/StableBeluga2",
  )
  parser.add_argument('--initial_peers', type=str, nargs='+', required=False, default=PUBLIC_INITIAL_PEERS,
                      help='Multiaddrs of one or more DHT peers from the target swarm. Default: connects to the public swarm')

  args = parser.parse_args()

  logger.error("Checking blockchain model paths...")

  model_path_id = get_model_path_id(
    substrate_config.SubstrateConfig.interface,
    args.path,
  )

  assert model_path_id == None, "Model path is already stored with model_id %s" % model_path_id

  logger.error("Checking model has minimum required peers...")

  peer_ids_list = get_peer_ids_list()

  min_model_peers = substrate_config.NetworkConfig.min_model_peers

  assert len(peer_ids_list) >= min_model_peers, "Model doesn't meet minimum required model validators hosting the model"

  block_number = substrate_config.SubstrateConfig.interface.get_block_number()
  
  remove_remove_subnet_receipt = remove_subnet(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.keypair,
    args.peer_id,
    args.ip,
    args.port,
    args.stake_to_be_added,
  )

  if remove_remove_subnet_receipt.is_success:
    logger.info("✅ Successfully initialized model at or near block %s" % block_number)
    logger.info("""
      ✅ Successfully initialized model
    """)
    for event in remove_remove_subnet_receipt.triggered_events:
      event_id = event['event_id']
      if event_id == 'ModelAdded':
        model_id = event['attributes']['model_id']
        block = event['attributes']['block']
        substrate_config.SubnetDataConfig.id = model_id
        substrate_config.SubnetDataConfig.initialized = block
  else:
    logger.error('⚠️ Extrinsic Failed, add_subnet unsuccessful with the following error message: %s' % remove_remove_subnet_receipt.error_message)


if __name__ == "__main__":
  main()
