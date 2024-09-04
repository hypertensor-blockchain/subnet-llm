"""
python -m petals_tensor.cli.run_consensus --path bigscience/bloom-560m
"""
import logging
import argparse
from petals_tensor.substrate import config as substrate_config
from petals_tensor.substrate import utils as substrate_utils
from petals_tensor.substrate.consensus import Consensus

logger = logging.getLogger(__name__)

def main():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--path', required=True, nargs='?', type=str, help="path or name of a pretrained model, converted with cli/convert_model.py")

  args = parser.parse_args()

  path = args.path

  logger.info('path %s' % path)

  consensus = Consensus(path)

  try:
    consensus.run()
  except KeyboardInterrupt:
    logger.info("Caught KeyboardInterrupt, shutting down")

if __name__ == "__main__":
    main()