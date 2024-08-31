"""
python -m petals_tensor.cli.run_remove_subnet_node
python -m petals_tensor.cli.run_remove_subnet_node --path bigscience/bloom-560m

"""
import argparse
import logging
from petals_tensor.health.state_updater import get_peer_ids_list
from petals_tensor.substrate import config as substrate_config
from petals_tensor.substrate.chain_functions import get_model_peer_account, remove_subnet_node
from petals_tensor.substrate import utils as substrate_utils

logger = logging.getLogger(__name__)

def main():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--path', required=True, nargs='?', type=str, help="path or name of a pretrained model, converted with cli/convert_model.py")
  args = parser.parse_args()

  model_config = substrate_config.load_subnet_config()
  model_id = model_config.id

  block_header = substrate_config.SubstrateConfig.interface.get_block_header()
  block_number = block_header['header']['number']

  network_config = substrate_config.load_network_config()

  """
  Peer data is previously saved before storing on the blockchain
  """
  model_validator_config = substrate_config.load_model_validator_config()

  peer_id = model_validator_config.peer_id 
  initialized = model_validator_config.initialized 

  """
  Ensure there is no account using peer_id
  `5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM` is default account
  """
  model_peer_account = get_model_peer_account(
    substrate_config.SubstrateConfig.interface,
    model_id,
    peer_id
  )

  assert model_peer_account != "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM", "PeerId not stored on blockchain"

  logger.info('Getting account balance...')

  remove_remove_subnet_node_receipt = remove_subnet_node(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.keypair,
    model_id,
  )

  if remove_remove_subnet_node_receipt.is_success:
    for event in remove_remove_subnet_node_receipt.triggered_events:
      event_id = event.value['event_id']
      if event_id == 'ModelPeerRemoved':
        block = event.value['attributes']['block']
        logger.info("✅ Successfully removed model peer at block %s" % block)
        """
        Pickle
        Update `initialized`
        Update `removed`
        """
        model_validator_config.initialized = 0
        model_validator_config.removed = block
        substrate_config.save_model_validator_config(model_validator_config)
  else:
    logger.error('⚠️ Extrinsic Failed with the following error message: %s' % remove_remove_subnet_node_receipt.error_message)

if __name__ == "__main__":
    main()