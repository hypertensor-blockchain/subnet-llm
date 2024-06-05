"""
Vote in a live model

Model must be live to be successfully voted in

(Not yet implemented as of testnet v1.0)
"""
import argparse

def main():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
    "--path",
    nargs="?",
    required=True,
    help="The path of the existing model. "
    "Example: petals-team/StableBeluga2 if the full path is https://huggingface.co/petals-team/StableBeluga2",
  )
  parser.add_argument(
    "--vote",
    type=bool, 
    required=True,
    nargs="*",
    help="The vote towards a model. "
    "Example: True or False",
  )
  parser.add_argument(
    "--amount",
    type=int, 
    required=True,
    nargs="?",
    help="The amont to vote towards a model vote in or out. "
    "Example: 10000000000000",
  )

  args = parser.parse_args()

if __name__ == "__main__":
  main()
