"""
Return peer data stored in the substrate config

Note: In dev mode the blockchain must be running

python -m petals_tensor.cli.run_test_inference
"""
import argparse
import logging
import pprint

from torch import tensor
import torch
from petals_tensor.client import InferenceSession
from petals_tensor.utils.auto_config import AutoDistributedModelForCausalLMValidator
from transformers import AutoTokenizer
from petals_tensor import AutoDistributedModelForCausalLM
# from petals_tensor.consensus import InferenceSessionValidator


logger = logging.getLogger(__name__)

def main():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      "--peer",
      nargs="*",
      help="Multiaddrs of the peers that will welcome you into the existing DHT. "
      "Example: /ip4/203.0.113.1/tcp/31337/p2p/XXXX /ip4/203.0.113.2/tcp/7777/p2p/YYYY",
  )
  args = parser.parse_args()

  # Choose any model available at dashboard.hypertensor.org
  model_name = "petals-team/StableBeluga2"  # This one is fine-tuned Llama 2 (70B)
  
  print(model_name)
  # Connect to a distributed network hosting model layers
  tokenizer = AutoTokenizer.from_pretrained(model_name)
  print("tokenizer", tokenizer)

  # model = AutoDistributedModelForCausalLM.from_pretrained(model_name)
  # print("model", model)

  model = AutoDistributedModelForCausalLMValidator.from_pretrained(model_name)
  print("model", model)

  # Run the model as if it were on your computer
  inputs = tokenizer("A cat sat", return_tensors="pt")["input_ids"]
  print("inputs", inputs)

  # outputs = model.generate_with_specific_peer(inputs, max_new_tokens=5)
  # outputs = model.generate_with_specific_peer("12D3KooWKkY4mz7riahcMo7NUnfhtFrAcexfLGZigFRS3MtaKXKo", inputs, max_new_tokens=5)
  # outputs = model.generate(inputs, peer_id="12D3KooWMGqMt6GEeqwgBhkrHPH5sT7zrBmMjHMMoyGz1b5ahE3f", max_new_tokens=5)
  # print("outputs", outputs)

  peer_spans = [
     {
        'peer_id':"12D3KooWG35HByAh4BFLYEqzfKnrqjKYDSNFWwZSiDJjbmEWTFJu",
        'start':0,
        'end':1,
     },
      {
        'peer_id':"12D3KooWG35HByAh4BFLYEqzfKnrqjKYDSNFWwZSiDJjbmEWTFJu",
        'start':1,
        'end':2,
     },
     {
        'peer_id':"12D3KooWG35HByAh4BFLYEqzfKnrqjKYDSNFWwZSiDJjbmEWTFJu",
        'start':2,
        'end':3,
     },
     {
        'peer_id':"12D3KooWG35HByAh4BFLYEqzfKnrqjKYDSNFWwZSiDJjbmEWTFJu",
        'start':3,
        'end':4,
     },
     {
        'peer_id':"12D3KooWRq6irihC9wiXWQXNQvbF2yGHCycr7J9ttvVZJorhyJL6",
        'start':4,
        'end':5,
     },
  ]

  # tensors = {
  #   'server_idx': 3, 
  #   'inputs': tensor([[[-0.0149,  0.0022,  0.0225,  ..., -0.0713,  0.0425,  0.0072]]], dtype=torch.bfloat16), 
  #   'outputs': tensor([[[-0.0149,  0.0022,  0.0225,  ..., -0.0713,  0.0425,  0.0072]]]), 
  #   'span_start': 3, 
  #   'span_end': 4, 
  #   'attempt_no': 0, 
  #   'peer_id': "12D3KooWG35HByAh4BFLYEqzfKnrqjKYDSNFWwZSiDJjbmEWTFJu", 
  #   'server_session': {
  #       "peer_id": "12D3KooWG35HByAh4BFLYEqzfKnrqjKYDSNFWwZSiDJjbmEWTFJu", 
  #       "start": 3, 
  #       "end": 4,
  #       "server_info": {
  #           "start_block": 0, 
  #           "end_block": 80
  #       }
  #   }
  # }
  # torch.set_printoptions(threshold=10_000)

  inference_session_data, outputs = model.generate_with_tensors(
      inputs, 
      peers=peer_spans,
      max_new_tokens=5,
      # tensors=tensors
  )
  # torch.set_printoptions(profile="full")

  # outputs = model.generate(inputs, peer_ids=["12D3KooWCWrjfLzYL4zJevm35MzexAwjngE1WNPYeiHrsLTGEkoy"], max_new_tokens=5)
  print("outputs\n")
  pprint.pprint(outputs)
  print("inference_session_data\n")
  pprint.pprint(inference_session_data)

  pprint.pprint(tokenizer.decode(outputs[0]))  # A cat sat on a mat...

  tensors = []

  for data in inference_session_data:
    if data["server_idx"] == 4:
      print("found server_idx 4")
      tensors.append(data)

  print("tensors\n")
  pprint.pprint(tensors)

  inference_session_data, outputs = model.generate_with_tensors(
      inputs, 
      peers=peer_spans,
      max_new_tokens=5,
      tensors=tensors
  )

  print("tensors\n")
  print("last output\n")
  pprint.pprint(tokenizer.decode(outputs[0]))  # A cat sat on a mat...


if __name__ == "__main__":
    main()