"""
If a model is successfully voted in use this cli
python -m petals_tensor.cli.run_add_model --path petals-team/Beluga2

"""
import logging

import argparse
from petals_tensor.constants import PUBLIC_INITIAL_PEERS
from petals_tensor.substrate import config as substrate_config
from petals_tensor.health.state_updater import get_peer_ids_list
from petals_tensor.substrate.chain_functions import add_model, get_model_path_id

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

  network_config = substrate_config.load_network_config()
  min_model_peers = network_config.min_model_peers
  assert len(peer_ids_list) >= min_model_peers, "Model doesn't meet minimum required model validators hosting the model"

  block_number = substrate_config.SubstrateConfig.interface.get_block_number()
  
  add_model_receipt = add_model(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.keypair,
    args.path
  )

  if add_model_receipt.is_success:
    logger.info("✅ Successfully initialized model at or near block %s" % block_number)
    logger.info("""
      ✅ Successfully initialized model
    """)
    for event in add_model_receipt.triggered_events:
      event_id = event.value['event_id']
      if event_id == 'ModelAdded':
        model_id = event.value['attributes']['model_id']
        block = event.value['attributes']['block']
        model_config = substrate_config.load_model_config()
        model_config.id = model_id
        model_config.initialized = block
  else:
    logger.error('⚠️ Extrinsic Failed, add_model_peer unsuccessful with the following error message: %s' % add_model_receipt.error_message)


if __name__ == "__main__":
  main()
