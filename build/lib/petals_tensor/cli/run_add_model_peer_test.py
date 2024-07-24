"""
This should be ran after your node has successfully began hosting the machine learning models

Before running add_model_peer() make sure your peer_id is shown when running `health.py`

It's important other peers are submitting your peer_id during peer consensus so the node 
doesn't increment your peer_id out of consensus. Read documentation for more information

python -m petals_tensor.cli.run_add_model_peer_test --id 1 --peer_id 12D3KooWGFuUunX1AzAzjs3CgyqTXtPWX3AqRhJFbesGPGYHJQTP --ip 127.0.0.1 --port 8888 --stake_to_be_added 1000
python -m petals_tensor.cli.run_add_model_peer_test --stake_to_be_added 1000

"""
import logging
import argparse
from petals_tensor.health.state_updater import get_peer_ids_list
from petals_tensor.substrate import config as substrate_config
import re
from petals_tensor.substrate.chain_functions import add_model_peer, get_balance, get_model_peer_account
from petals_tensor.substrate import utils as substrate_utils

logger = logging.getLogger(__name__)

def main():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
    "--stake_to_be_added",
    type=int, 
    required=True,
    nargs="?",
    help="The integer balance of TENSOR to be staked towards the model. Must be greater than or equal to minumum required stake balance. "
    "Example: 1000",
  )

  args = parser.parse_args()

  model_config = substrate_config.load_model_config()
  model_id = model_config.id

  network_config = substrate_config.load_network_config()

  """Ensure stake_to_be_added is greater than or equal to minimum required stake balance"""
  min_stake_balance = network_config.min_stake_balance
  
  assert args.stake_to_be_added >= min_stake_balance, "Invalid stake_to_be_added - Must be greater than %s" % min_stake_balance

  block_header = substrate_config.SubstrateConfig.interface.get_block_header()
  block_number = block_header['header']['number']

  in_consensus_steps = substrate_utils.is_in_consensus_steps(
    block_number,
    network_config.consensus_blocks_interval, 
  )

  assert in_consensus_steps == False, "Cannot add model peer while blockchain is running consensus steps. Wait 2 blocks"

  """
  Peer data is previously saved before storing on the blockchain
  After successfully running `add_model_peer` in Hypertensor we store the new `initialized` at the end
  """
  model_validator_config = substrate_config.load_model_validator_config()

  model_validator_config = substrate_config.ModelValidatorConfig()

  """Initialize mock peer data"""
  model_validator_config.initialize(
    "QmYyQSo1c1Ym7orWxLYvCrM2EmxFTANf8wXmmE7DWjhx5N51",
    "172.20.54.234",
    8888,
    0
  )

  peer_id = model_validator_config.peer_id 
  ip = model_validator_config.ip 
  port = model_validator_config.port 
  initialized = model_validator_config.initialized 

  print("peer_id      ", peer_id)
  print("ip           ", ip)
  print("port         ", port)
  print("initialized  ", initialized)

  assert initialized == 0, "Peer already initialized into storage."

  """
  Ensure there is no account using peer_id
  `5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM` is default account
  """
  model_peer_account = get_model_peer_account(
    substrate_config.SubstrateConfig.interface,
    peer_id
  )

  assert model_peer_account == "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM", "PeerId already stored on blockchain"

  logger.info('Getting account balance to ensure account can stake `stake_to_be_added`...')

  balance = get_balance(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.account_id
  )

  assert args.stake_to_be_added <= balance, "Invalid stake_to_be_added - Balance must be greater than %s" % min_stake_balance

  add_model_peer_receipt = add_model_peer(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.keypair,
    model_id,
    peer_id,
    ip,
    port,
    args.stake_to_be_added,
  )

  """
  Get helpful messages
  """
  eligible_consensus_inclusion_block = substrate_utils.get_eligible_consensus_block(
    network_config.min_required_peer_consensus_inclusion_epochs, 
    block_number, 
    network_config.consensus_blocks_interval
  )

  eligible_consensus_submit_block = substrate_utils.get_eligible_consensus_block(
    network_config.min_required_peer_consensus_submit_epochs, 
    block_number, 
    network_config.consensus_blocks_interval
  )

  if add_model_peer_receipt.is_success:
    for event in add_model_peer_receipt.triggered_events:
      event_id = event.value['event_id']
      if event_id == 'ModelPeerAdded':
        block = event.value['attributes']['block']
        logger.info("✅ Successfully initialized model peer at block %s" % block)
        logger.info("✅ You must be hosting models by block %s for other validators to include your in their consensus data" % eligible_consensus_inclusion_block)
        logger.info("✅ You must be hosting and submitting consensus data by block %d to receive rewards" % eligible_consensus_submit_block)
        """
        Pickle
        Update `initialized`
        """
        model_validator_config.initialized = block
        substrate_config.save_model_validator_config(model_validator_config)
  else:
    logger.error('⚠️ Extrinsic Failed with the following error message: %s' % add_model_peer_receipt.error_message)

if __name__ == "__main__":
    main()