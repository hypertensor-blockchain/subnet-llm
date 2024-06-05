"""
This should be ran after your node has successfully began hosting the machine learning models

Before running add_model_peer() make sure your peer_id is shown when running `health.py`

It's important other peers are submitting your peer_id during peer consensus so the node 
doesn't increment your peer_id out of consensus. Read documentation for more information

python -m petals_tensor.cli.run_add_model_peer --id 1 --peer_id 12D3KooWGFuUunX1AzAzjs3CgyqTXtPWX3AqRhJFbesGPGYHJQTP --ip 127.0.0.1 --port 8888 --stake_to_be_added 1000
python -m petals_tensor.cli.run_add_model_peer --stake_to_be_added 1000

"""
import logging
from petals_tensor.health.state_updater import get_peer_ids_list
from petals_tensor.substrate import config as substrate_config
from petals_tensor.substrate.chain_functions import get_model_peer_account, remove_model_peer
from petals_tensor.substrate import utils as substrate_utils

logger = logging.getLogger(__name__)

def main():
  model_config = substrate_config.load_model_config()
  model_id = model_config.id

  block_header = substrate_config.SubstrateConfig.interface.get_block_header()
  block_number = block_header['header']['number']

  network_config = substrate_config.load_network_config()

  can_remove_or_update_model_peer = substrate_utils.can_remove_or_update_model_peer(
    block_number,
    network_config.consensus_blocks_interval, 
  )

  assert can_remove_or_update_model_peer == True, "Cannot remove model peer while blockchain is running consensus block spans."

  """
  Peer data is previously saved before storing on the blockchain
  After successfully running `add_model_peer` in Hypertensor we store the new `initialized` at the end
  """
  model_validator_config = substrate_config.load_model_validator_config()

  peer_id = model_validator_config.peer_id 
  initialized = model_validator_config.initialized 

  assert initialized != 0, "Peer not initialized into storage."

  """
  Ensure there is no account using peer_id
  `5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM` is default account
  """
  model_peer_account = get_model_peer_account(
    substrate_config.SubstrateConfig.interface,
    peer_id
  )

  assert model_peer_account != "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM", "PeerId not stored on blockchain"

  logger.info('Getting account balance...')

  remove_model_peer_receipt = remove_model_peer(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.keypair,
    model_id,
  )

  if remove_model_peer_receipt.is_success:
    for event in remove_model_peer_receipt.triggered_events:
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
    logger.error('⚠️ Extrinsic Failed with the following error message: %s' % remove_model_peer_receipt.error_message)

if __name__ == "__main__":
    main()