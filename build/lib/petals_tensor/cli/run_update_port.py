"""
This should be ran after your node has successfully began hosting the machine learning models

Before running add_model_peer() make sure your peer_id is shown when running `health.py`

It's important other peers are submitting your peer_id during peer consensus so the node 
doesn't increment your peer_id out of consensus. Read documentation for more information

python -m petals_tensor.cli.run_add_model_peer --id 1 --peer_id 12D3KooWGFuUunX1AzAzjs3CgyqTXtPWX3AqRhJFbesGPGYHJQTP --ip 127.0.0.1 --port 8888 --stake_to_be_added 1000

"""
import logging
import argparse
from petals_tensor.health.state_updater import get_peer_ids_list
from petals_tensor.substrate import config as substrate_config
import re
from petals_tensor.substrate.chain_functions import add_model_peer, get_balance, update_port
from petals_tensor.substrate import utils as substrate_utils

logger = logging.getLogger(__name__)

def main():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
    "--port",
    type=int, 
    required=True,
    nargs="?",
    help="The port designated to be open to be called by the blockchain to query model data. "
    "Example: 8888",
  )

  model_config = substrate_config.load_model_config()
  model_id = model_config.id

  args = parser.parse_args()

  """
  Checking if model_id exists on blockchain is done during add_model_peer
  Here we check if its a possible model_id
  """
  assert args.id >= 1, "Model invalid - Must be greater than 0"

  block_header = substrate_config.SubstrateConfig.interface.get_block_header()

  block_number = block_header['header']['number']
  update_port_receipt = update_port(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.keypair,
    model_id,
    args.port,
  )

  if update_port_receipt.is_success:
    logger.info("✅ Successfully updated port at or near block %s" % block_number)
    model_validator_config = substrate_config.load_model_validator_config()
    model_validator_config.port = args.port
    substrate_config.save_model_validator_config(model_validator_config)
  else:
    logger.error('⚠️ Extrinsic Failed with the following error message: %s' % update_port_receipt.error_message)

if __name__ == "__main__":
    main()