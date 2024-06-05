"""
Return peer data stored in the substrate config

Note: In dev mode the blockchain must be running

python -m petals_tensor.cli.run_get_peer
"""
import logging
from petals_tensor.substrate import config as substrate_config

logger = logging.getLogger(__name__)

def main():
  model_validator_config = substrate_config.load_model_validator_config()
  logger.info("account_id:  %s" % model_validator_config.account_id)
  logger.info("peer_id:     %s" % model_validator_config.peer_id)
  logger.info("ip:          %s" % model_validator_config.ip)
  logger.info("port:        %s" % model_validator_config.port)
  logger.info("initialized: %s" % model_validator_config.initialized)
  logger.info("removed:     %s" % model_validator_config.removed)

if __name__ == "__main__":
    main()