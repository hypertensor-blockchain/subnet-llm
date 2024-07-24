"""
Return peer data stored in the substrate config

Note: In dev mode the blockchain must be running

python -m petals_tensor.cli.run_get_model
"""
import logging
from petals_tensor.substrate import config as substrate_config

logger = logging.getLogger(__name__)

def main():
  model_config = substrate_config.load_model_config()
  print("model_config -> ", model_config)
  print("model_config.id -> ", model_config.id)
  print("model_config.path -> ", model_config.path)
  print("model_config.initialized -> ", model_config.initialized)

  # logger.info("Model ID1:          %s" % substrate_config.ModelDataConfig().get_test())
  # logger.info("Model ID2:          %s" % substrate_config.ModelDataConfig().test)

  # logger.info("Model ID:          %s" % substrate_config.ModelDataConfig().id)
  # logger.info("Model Path:        %s" % substrate_config.ModelDataConfig().path)
  # logger.info("Model Initialized: %s" % substrate_config.ModelDataConfig().initialized)

if __name__ == "__main__":
    main()