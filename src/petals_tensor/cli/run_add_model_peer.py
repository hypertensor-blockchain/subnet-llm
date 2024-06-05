"""
This should be ran after your node has successfully began hosting the machine learning models

Make sure to update `.env` variables

run python -m petals_tensor.cli.run_update_network_config before run_server

python -m petals_tensor.cli.run_add_model_peer --stake_to_be_added 1000000000000000000000
"""
import logging
import argparse
from petals_tensor.health.state_updater import get_peer_ids_list
from petals_tensor.substrate import config as substrate_config
import re
from petals_tensor.substrate.chain_functions import add_model_peer, get_balance, get_model_peer_account
from petals_tensor.substrate import utils as substrate_utils

logger = logging.getLogger(__name__)

"""
This is one layer of defense and doesn't gauarantee checking if a peer_id is valid
"""
def validate_peer_id(peer_id):
  peer_id_len = len(peer_id)
  if peer_id_len < 32 or peer_id_len > 128:
    return False
  
  first_char = peer_id[0]
  second_char = peer_id[1]
  
  if first_char == "1":
    return True
  elif first_char == "Q" and second_char == "m":
    return True
  elif first_char == "f" or first_char == "b" or first_char == "z" or first_char == "m":
    return True
  else:
    return False

def validate_ip(ip):
  # Make a regular expression
  # for validating an Ip-address
  regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
  if(re.search(regex, ip)): 
    print("Valid ip address")
    return True
  else: 
    print("Invalid ip address")
    return False


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
  parser.add_argument(
    "--subscribe",
    type=bool, 
    required=False,
    default=False,
    help="Begin subscribing to blocks. This is used to submit consensus data. This can be done manually"
  )

  args = parser.parse_args()

  # """
  # Checking if model_id exists on blockchain is done during add_model_peer
  # Here we check if its a possible model_id
  # """
  # assert args.id >= 1, "Model invalid - Must be greater than 0"

  # assert validate_ip(args.ip), "IP invalid - Must be IPv4 or IPv6"

  # assert args.port <= 65535, "Port invalid - Must be less than or equal to 65535"

  # logger.info('Validating peer_id is hosting...')
  # """
  # First check format is about right
  # Then check if they are hosting models as a model validator
  # """
  # assert validate_peer_id(args.peer_id), "PeerId invalid - Must be correct format"

  """Load model data saved from `run_server` CLI"""
  model_config = substrate_config.load_model_config()
  model_id = model_config.id

  """Load network data saved from `run_update_network_config` CLI"""
  network_config = substrate_config.load_network_config()

  min_stake_balance = network_config.min_stake_balance
  
  """Ensure stake_to_be_added is greater than or equal to minimum required stake balance"""
  assert args.stake_to_be_added >= min_stake_balance, "Invalid stake_to_be_added - Must be greater than %s" % min_stake_balance

  subscribe = args.subscribe

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

  peer_id = model_validator_config.peer_id 
  ip = model_validator_config.ip 
  port = model_validator_config.port 
  initialized = model_validator_config.initialized 

  print("peer_id      ", peer_id)
  print("ip           ", ip)
  print("port         ", port)
  print("initialized  ", initialized)

  assert initialized == 0, "Peer already initialized into storage. If this is a mistake remove the `model_validator_config` pickle file."

  peer_ids_list = get_peer_ids_list()
  print(peer_ids_list)
  peer_exists = False
  for peer in peer_ids_list:
    if peer_id == peer:
      peer_exists = True
      break

  assert peer_exists, "PeerId not hosting models."

  """
  Ensure there is no account using peer_id
  `5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM` is default account
  """
  model_peer_account = get_model_peer_account(
    substrate_config.SubstrateConfig.interface,
    model_id,
    peer_id
  )

  assert model_peer_account == "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM", "PeerId already stored on blockchain. If this is a mistake remove the `model_validator_config` pickle file."

  logger.info('Getting account balance to ensure account can stake `stake_to_be_added`...')

  balance = get_balance(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.account_id
  )

  logger.info('Your balance is %s (%s)' % (balance, float(balance / 1e18)))

  assert args.stake_to_be_added <= balance, "Invalid stake_to_be_added. Need %s more. Balance is %s and must be greater than %s" % (
    (min_stake_balance - balance), balance, min_stake_balance
  )

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

        substrate_utils.save_last_unconfirm_consensus_block(0)
        substrate_utils.save_last_submit_consensus_block(0)

        """Start subscribing to blocks"""
        if subscribe:
          """"""
  else:
    logger.error('⚠️ Extrinsic Failed with the following error message: %s' % add_model_peer_receipt.error_message)

if __name__ == "__main__":
    main()