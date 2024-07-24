"""
This should be ran after your node has successfully began hosting the machine learning models

Before running add_model_peer() make sure your peer_id is shown when running `health.py`

It's important other peers are submitting your peer_id during peer consensus so the node 
doesn't increment your peer_id out of consensus. Read documentation for more information

python -m petals_tensor.cli.run_add_model_peer --id 1 --peer_id 12D3KooWGFuUunX1AzAzjs3CgyqTXtPWX3AqRhJFbesGPGYHJQTP --ip 127.0.0.1 --port 8888 --stake_to_be_added 1000

"""
import logging
import argparse
from petals_tensor.substrate import config as substrate_config
from petals_tensor.substrate.chain_functions import add_to_stake, get_balance
from petals_tensor.substrate import utils as substrate_utils

logger = logging.getLogger(__name__)

def main():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
    "--stake_to_be_added",
    type=int, 
    required=True,
    nargs="?",
    help="The amont of stake to be added. "
    "Example: 10000000000000",
  )

  args = parser.parse_args()

  model_config = substrate_config.load_model_config()
  model_id = model_config.id

  balance = get_balance(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.account_id
  )
  assert args.stake_to_be_added <= balance, "Invalid stake_to_be_added - Balance must be greater than %s" % args.stake_to_be_added

  block_header = substrate_config.SubstrateConfig.interface.get_block_header()
  block_number = block_header['header']['number']

  in_consensus_steps = substrate_utils.is_in_consensus_steps(
    block_number,
    substrate_config.NetworkConfig.consensus_blocks_interval, 
  )

  assert in_consensus_steps == False, "Cannot add to stake while blockchain is running consensus steps. Wait 2 blocks"

  add_to_stake_receipt = add_to_stake(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.keypair,
    model_id,
    args.stake_to_be_added,
  )

  if add_to_stake_receipt.is_success:
    logger.info("✅ Successfully added to stake at or near block %s" % block_number)
  else:
    logger.error('⚠️ Extrinsic Failed with the following error message: %s' % add_to_stake_receipt.error_message)

if __name__ == "__main__":
    main()