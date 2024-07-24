"""
Vote a model peer as dishonest manually

Note: In dev mode the blockchain must be running

python -m petals_tensor.cli.run_vote_peer_dishonest
"""
import argparse
import logging
from petals_tensor.substrate import config as substrate_config
from petals_tensor.substrate.chain_functions import get_model_path_id, vote_model_peer_dishonest

logger = logging.getLogger(__name__)

def main():
  logger.info("Coming in Testnet V2")
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
    "--peer_id",
    type=str, 
    nargs=1,
    required=True,
    help="The Peer ID of the dishonest peer. "
    "Example: petals-team/StableBeluga2 if the full path is https://huggingface.co/petals-team/StableBeluga2",
  )

  args = parser.parse_args()

  """Load model data saved in `run_server` CLI"""
  model_config = substrate_config.load_model_config()
  model_id = model_config.id
  model_path = model_config.path

  model_path_id = get_model_path_id(
    substrate_config.SubstrateConfig.interface,
    model_path,
  )

  assert model_path_id != None, "Model path is already stored with model_id %s" % model_path_id

  vote_model_peer_dishonest_receipt = vote_model_peer_dishonest(
    substrate_config.SubstrateConfig.interface,
    substrate_config.SubstrateConfig.keypair,
    model_id,
    args.peer_id,
  )

  if vote_model_peer_dishonest_receipt.is_success:
    logger.info("""✅ Successfully vote model peer dishonest""")
  else:
    logger.error('⚠️ Extrinsic Failed, vote_model_peer_dishonest unsuccessful with the following error message: %s' % vote_model_peer_dishonest_receipt.error_message)


if __name__ == "__main__":
    main()