""""""
import argparse
from petals_tensor.substrate import config as substrate_config
from petals_tensor.substrate.chain_functions import get_model_path_id

def main():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
    "--id",
    nargs="?",
    required=True,
    help="The path of the existing model. "
    "Example: petals-team/StableBeluga2 if the full path is https://huggingface.co/petals-team/StableBeluga2",
  )
  parser.add_argument(
    "--amount",
    type=int, 
    required=True,
    nargs="?",
    help="The amont to vote towards a model vote out. "
    "Example: 10000000000000",
  )

  args = parser.parse_args()

  model_path_id = get_model_path_id(
    substrate_config.SubstrateConfig.interface,
    args.path,
  )

  assert model_path_id > 0, "Model path is already stored"

if __name__ == "__main__":
  main()
