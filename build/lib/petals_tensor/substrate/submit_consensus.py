from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException
from typing import List, Tuple, Dict, Optional, Any, TypedDict, Union
from tenacity import retry, stop_after_attempt, wait_exponential

from utils import is_in_consensus_steps, get_eligible_consensus_block


def submit_consensus_data(
  substrate: SubstrateInterface,
  keypair: Keypair,
  model_id: int,
  consensus_data
):
  """
  Submit consensus data on each epoch with no conditionals

  It is up to prior functions to decide whether to call this function

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  :param model_id: the id of the model associated with the model path
  :param consensus_data: an array of data containing all AccountIds, PeerIds, and scores per model hoster

  Note: It's important before calling this to ensure the entrinsic will be successful.
        If the function reverts, the extrinsic is Pays::Yes
  """

  # compose call
  call = substrate.compose_call(
    call_module='Network',
    call_function='submit_consensus_data',
    call_params={
      'model_id': model_id,
      'consensus_data': consensus_data
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

  # submit extrinsic (this is gasless unless it reverts)
  # This will retry up to 4 times when except is returned
  # 
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def submit_extrinsic():
    try:
      receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
      if receipt.is_success:
        print('✅ Success, triggered events:')
        for event in receipt.triggered_events:
          print(f'* {event.value}')
      else:
        print('⚠️ Extrinsic Failed: ', receipt.error_message)
      return receipt
    except SubstrateRequestException as e:
      print("Failed to send: {}".format(e))

  return submit_extrinsic()

  # try:
  #   receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
  #   if receipt.is_success:
  #     print('✅ Success, triggered events:')
  #     for event in receipt.triggered_events:
  #       print(f'* {event.value}')
  #   else:
  #     print('⚠️ Extrinsic Failed: ', receipt.error_message)
  # except SubstrateRequestException as e:
  #   print("Failed to send: {}".format(e))

def eligible_to_submit_consensus_data(
  substrate: SubstrateInterface,
  keypair: Keypair,
  block: int,
  model_id: int,
  model_initialized: int,
  peer_initialized: int,
  required_model_epochs: int,
  epochs_interval: int,
  required_peer_epochs: int,
) -> Dict:
  """
  Submit consensus data on each epoch

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  :param block: current block
  :param epoch_interval: epoch blocks interval
  :param model_id: the id of the model associated with the model path
  """
  print("Checking if eligible to submit consensus data...")

  model_eligible_block = get_eligible_consensus_block(
    epochs_interval, 
    model_initialized, 
    required_model_epochs
  )
  print("model_eligible_block: ", model_eligible_block)

  # ensure model can have consensus data submitted
  if (block <= model_eligible_block):
    # return False
    return {
      "eligible": False,
      "reason": "Model not eligible for consensus data"
    }

  peer_eligible_block = get_eligible_consensus_block(
    epochs_interval, 
    peer_initialized, 
    required_peer_epochs
  )
  print("block: ", block)
  print("peer_eligible_block: ", peer_eligible_block)
  # ensure model peer can submit consensus data
  if (block <= peer_eligible_block):
    # return False
    return {
      "eligible": False,
      "reason": "Peer not eligible to submit consensus data"
    }

  # block_hash = substrate.get_block_hash(block)

  # ensure peer hasn't already submitted consensus data
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query(
        "Network", 
        "PeerConsensusEpochSubmitted", 
        [
          model_id,
          keypair
        ], 
        # block_hash=block_hash
      )
      return result
    except SubstrateRequestException as e:
      print("Failed to query: {}".format(e))

  # return if already submitted
  already_submitted = make_query()
  print("already_submitted: ", already_submitted)
  if already_submitted == True:
    # return False
    return {
      "eligible": False,
      "reason": "Peer already submitted consensus data"
    }

  return {
    "eligible": True,
    "reason": ""
  }
 
def eligible_to_unconfirm_consensus_data(
  substrate: SubstrateInterface,
  keypair: Keypair,
  block: int,
  model_id: int,
  model_initialized: int,
  peer_initialized: int,
  required_model_epochs: int,
  epochs_interval: int,
  required_peer_epochs: int,
) -> Dict:
  """
  Submit consensus data on each epoch

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  :param block: current block
  :param epoch_interval: epoch blocks interval
  :param model_id: the id of the model associated with the model path
  """

  model_eligible_block = get_eligible_consensus_block(
    epochs_interval, 
    model_initialized, 
    required_model_epochs
  )

  # ensure model can have consensus data submitted
  if (block <= model_eligible_block):
    # return False
    return {
      "eligible": False,
      "reason": "Model not eligible for consensus data"
    }

  peer_eligible_block = get_eligible_consensus_block(
    epochs_interval, 
    peer_initialized, 
    required_peer_epochs
  )

  # ensure model peer can submit consensus data
  if (block <= peer_eligible_block):
    # return False
    return {
      "eligible": False,
      "reason": "Peer not eligible to submit consensus data"
    }

  block_hash = substrate.get_block_hash(block)

  # ensure peer hasn't already submitted consensus data
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query(
        "Network", 
        "PeerConsensusEpochUnconfirmed", 
        [
          model_id,
          keypair
        ], 
        block_hash=block_hash
      )
      return result
    except SubstrateRequestException as e:
      print("Failed to query: {}".format(e))

  # return if already submitted
  already_unconfirmed = make_query()
  if already_unconfirmed == True:
    # return False
    return {
      "eligible": False,
      "reason": "Peer already submitted uncofirm consensus data"
    }

  return {
    "eligible": True,
    "reason": ""
  }