"""
This should be ran after your node has successfully began hosting the machine learning models

Before running add_subnet_net() make sure your peer_id is shown when running `health.py`

It's important other peers are submitting your peer_id during peer consensus so the node 
doesn't increment your peer_id out of consensus. Read documentation for more information

python -m petals_tensor.cli.run_remove_stake --stake_to_be_removed 10000000000000000000000

"""
import logging
import argparse
from petals_tensor.substrate import config as substrate_config
from petals_tensor.substrate.chain_functions import get_model_stake_balance, remove_stake
from petals_tensor.substrate import utils as substrate_utils

logger = logging.getLogger(__name__)

def main():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
    "--stake_to_be_removed",
    type=int, 
    required=True,
    nargs="?",
    help="The amont of stake to be removed. "
    "Example: 10000000000000",
  )

  model_config = substrate_config.load_subnet_config()
  model_id = model_config.id

  args = parser.parse_args()

  assert args.stake_to_be_removed > 0, "Stake To Be Removed invalid - Must be greater than 0"

  """
  Ensure amount being removed won't go below minimum required stake balance towards a model
  """

  logger.info("Your Account ID is %s" % substrate_config.SubstrateConfig.account_id)

  model_stake_balance = get_model_stake_balance(
    substrate_config.SubstrateConfig.interface,
    int(model_id),
    substrate_config.SubstrateConfig.account_id
  )

  logger.info("Your subnet stake balance %s" % model_stake_balance)

  block_header = substrate_config.SubstrateConfig.interface.get_block_header()
  block_number = block_header['header']['number']

  stake_to_be_removed = args.stake_to_be_removed

  if int(str(model_stake_balance)) < args.stake_to_be_removed:
     stake_to_be_removed = int(str(model_stake_balance))

  remove_stake_receipt = remove_stake(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.keypair,
    int(model_id),
    stake_to_be_removed,
  )

  if remove_stake_receipt.is_success:
    logger.info("✅ Successfully removed from stake at or near block %s" % block_number)
  else:
    logger.error('⚠️ Extrinsic Failed with the following error message: %s' % remove_stake_receipt.error_message)

if __name__ == "__main__":
    main()