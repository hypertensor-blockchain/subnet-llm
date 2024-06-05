"""
Return peer data stored in the substrate config

Note: In dev mode the blockchain must be running

python -m petals_tensor.cli.run_test
"""
import logging
from petals_tensor.substrate import config as substrate_config

logger = logging.getLogger(__name__)

def main():
  model_config = substrate_config.load_model_config()
  model_config.initialize(
    1,
    "this is it",
    400
  )
  substrate_config.save_model_config(model_config)

  logger.info("Model ID Saved ->            %s" % substrate_config.ModelDataConfig().id)
  logger.info("Model Path Saved ->          %s" % substrate_config.ModelDataConfig().path)
  logger.info("Model Initialized Saved ->   %s" % substrate_config.ModelDataConfig().initialized)

  network_config = substrate_config.NetworkConfig()
  network_config.initialize(
    11,
    44,
    516,
    15,
    61,
    51,
    88,
    26,
    72,
    2,
    2
  )

  """
  Save Pickle
  """
  substrate_config.save_network_config(network_config)
  print("saved")
  logger.info("consensus_blocks_interval -> %s" % substrate_config.NetworkConfig().consensus_blocks_interval)

if __name__ == "__main__":
    main()