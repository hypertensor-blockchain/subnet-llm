"""
This should be ran after your node has successfully began hosting the machine learning models

Make sure to update `.env` variables

run python -m petals_tensor.cli.run_update_network_config before run_server

python3 -m petals_tensor.cli.run_update_model_peer
"""
import logging
import argparse
from petals_tensor.health.state_updater import get_peer_ids_list
from petals_tensor.substrate import config as substrate_config
import re
from petals_tensor.substrate.chain_functions import get_model_peer_account, update_model_peer
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
  # parser.add_argument(
  #   "--subscribe",
  #   type=bool, 
  #   required=False,
  #   default=True,
  #   help="Begin subscribing to blocks. This is used to submit consensus data. This can be done manually"
  # )

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

  """Load model data saved in `run_server` CLI"""
  model_config = substrate_config.load_model_config()
  model_id = model_config.id

  """Load network data saved in `run_update_network_config` CLI"""
  network_config = substrate_config.load_network_config()

  block_header = substrate_config.SubstrateConfig.interface.get_block_header()
  block_number = block_header['header']['number']

  _can_remove_or_update_model_peer = substrate_utils.can_remove_or_update_model_peer(
    block_number,
    network_config.consensus_blocks_interval, 
  )

  assert _can_remove_or_update_model_peer == True, "Cannot update model peer while blockchain is accepting consensus data."

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

  assert initialized == 0, "Peer already initialized into storage."

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

  assert model_peer_account == "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM", "PeerId already stored on blockchain"

  update_model_peer_receipt = update_model_peer(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.keypair,
    model_id,
    peer_id,
  )

  if update_model_peer_receipt.is_success:
    for event in update_model_peer_receipt.triggered_events:
      event_id = event.value['event_id']
      if event_id == 'ModelPeerAdded':
        block = event.value['attributes']['block']
        logger.info("✅ Successfully initialized model peer at block %s" % block)
        """Start subscribing to blocks"""
  else:
    logger.error('⚠️ Extrinsic Failed with the following error message: %s' % update_model_peer_receipt.error_message)

if __name__ == "__main__":
    main()