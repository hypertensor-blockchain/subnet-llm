import time
from config import load_model_config, load_model_validator_config, load_network_config, save_network_config, SubstrateConfig, BLOCK_SECS
from utils import get_recheck_consensus_block, can_submit_consensus, get_consensus_data, get_eligible_consensus_block, get_blochchain_model_peers_submittable, get_next_eligible_submit_consensus_block, load_last_submit_consensus_block, load_last_unconfirm_consensus_block, load_unconfirm_consensus_count, save_last_submit_consensus_block, save_last_unconfirm_consensus_block, save_unconfirm_consensus_count
from submit_consensus import eligible_to_submit_consensus_data, eligible_to_unconfirm_consensus_data
from errors import SubscriptionException
from chain_functions import submit_consensus_data, unconfirm_consensus_data
from hivemind.utils import get_logger
import multiprocessing
import gc
from typing import Dict, Optional

logger = get_logger(__name__)

# source .venv/bin/activate
# python src/petals/substrate/subscriptions.py

# Checks local storage pickles to see if we can submit any consensus data at the current block
# Instead of listening to blocks we infinitely loop using a while True loop
# @to-do: Make more efficient
def block_listener():
  logger.info("block_listener running...")
  while True:
    block_hash = SubstrateConfig.interface.get_block_hash()
    block_number = SubstrateConfig.interface.get_block_number(block_hash)
    logger.info("Block height: %s " % block_number)

    network_config = load_network_config()
    min_required_model_consensus_submit_epochs = network_config.min_required_model_consensus_submit_epochs
    min_required_peer_consensus_submit_epochs = network_config.min_required_peer_consensus_submit_epochs
    min_model_peers = network_config.min_model_peers
    consensus_blocks_interval = network_config.consensus_blocks_interval

    model_config = load_model_config()
    model_id = model_config.id
    model_initialized = model_config.initialized

    model_validator_config = load_model_validator_config()
    peer_initialized = model_validator_config.initialized


    """Avoid remote calling the blockchain by using local storage"""
    last_submit_consensus_block = load_last_submit_consensus_block()
    last_unconfirm_consensus_block = load_last_unconfirm_consensus_block()

    """Get next submission block related to the last submission"""
    next_submit_consensus_block = get_next_eligible_submit_consensus_block(
      consensus_blocks_interval, 
      last_submit_consensus_block
    )

    """Get next unconfirm block related to the last unconfirm or last model health check"""
    next_unconfirm_consensus_block = get_next_eligible_submit_consensus_block(
      consensus_blocks_interval, 
      last_unconfirm_consensus_block
    )

    if next_submit_consensus_block >= block_number and next_unconfirm_consensus_block >= block_number:
      """Already submitted consensus and already checked health or unconfirmed"""
      delta_1 = next_submit_consensus_block - block_number
      delta_2 = next_unconfirm_consensus_block - block_number
      delta = delta_1 if delta_1 < delta_2 else delta_2
      time.sleep(delta * BLOCK_SECS)
      block_hash = SubstrateConfig.interface.get_block_hash()
      block_number = SubstrateConfig.interface.get_block_number(block_hash)
    elif next_submit_consensus_block >= block_number and next_unconfirm_consensus_block < block_number:
      """
      Already submitted consensus -> wait until latter end of epoch to recheck model health
      If we're in this block, we update `next_unconfirm_consensus_block`
      Using `get_next_eligible_submit_consensus_block()` only gets the beginning of an epochs submit block
      """
      next_unconfirm_consensus_block = get_recheck_consensus_block(
        block_number,
        network_config.consensus_blocks_interval
      )
      if next_unconfirm_consensus_block > block_number:
        delta = next_unconfirm_consensus_block - block_number
        time.sleep(delta * BLOCK_SECS)

      block_hash = SubstrateConfig.interface.get_block_hash()
      block_number = SubstrateConfig.interface.get_block_number(block_hash)

    # The block the model can begin submitting consensus
    peer_eligible_block = get_eligible_consensus_block(
      network_config.consensus_blocks_interval, 
      peer_initialized, 
      min_required_peer_consensus_submit_epochs
    )

    # ensure model peer can submit consensus data from its initialization block
    is_peer_consensus_submission_eligible = peer_eligible_block != None and block_number >= peer_eligible_block

    if is_peer_consensus_submission_eligible == False:
      delta = peer_eligible_block - block_number
      logger.info("Model peer begins submitting consensus on block %s, going to sleep for %s blocks " % (peer_eligible_block, delta))
      time.sleep(delta * BLOCK_SECS)
      block_hash = SubstrateConfig.interface.get_block_hash()
      block_number = SubstrateConfig.interface.get_block_number(block_hash)

    # If we have unconfirmed and not submitted data, then 

    # The block the model can begin submitting consensus
    model_eligible_block = get_eligible_consensus_block(
      network_config.consensus_blocks_interval, 
      model_initialized, 
      min_required_model_consensus_submit_epochs
    )

    # ensure model can have consensus data submitted from its initialization block
    is_model_consensus_eligible = model_eligible_block != None and block_number >= model_eligible_block

    if is_model_consensus_eligible == False:
      delta = model_eligible_block - block_number
      logger.info("Model begins accepting consensus on block %s, going to sleep for %s blocks " % (model_eligible_block, delta))
      time.sleep(delta * BLOCK_SECS)
      block_hash = SubstrateConfig.interface.get_block_hash()
      block_number = SubstrateConfig.interface.get_block_number(block_hash)

    # Are we in the blocks available for consensus submission?
    _can_submit_consensus = can_submit_consensus(
      block_number,
      network_config.consensus_blocks_interval, 
    )

    if _can_submit_consensus == True and is_model_consensus_eligible == True:
      p = multiprocessing.Process(
        target=handle_consensus(
          block_number,
          model_id,
          model_initialized,
          peer_initialized,
          consensus_blocks_interval,
          next_submit_consensus_block,
          next_unconfirm_consensus_block,
          min_model_peers,
          min_required_model_consensus_submit_epochs,
          min_required_peer_consensus_submit_epochs
        )
      )
      p.start()
      p.join()
      p.close()

    time.sleep(BLOCK_SECS)

def handle_consensus(
  block_number: int, 
  model_id: int,
  model_initialized: int,
  peer_initialized: int,
  consensus_blocks_interval: int,
  next_submit_consensus_block: int,
  next_unconfirm_consensus_block: int,
  min_model_peers: int,
  min_required_model_consensus_submit_epochs: int,
  min_required_peer_consensus_submit_epochs: int
):
  # @to-do: pass this onto get_consensus_data instead of calling again
  model_peers_submittable = get_blochchain_model_peers_submittable(
    SubstrateConfig.interface,
    model_id,
  )

  if len(model_peers_submittable) >= min_model_peers:
    del model_peers_submittable

    model_validator_config = load_model_validator_config()

    logger.info("Next consensus block is %s " % next_submit_consensus_block)
    
    can_submit = block_number > next_submit_consensus_block

    can_unconfirm = block_number > next_unconfirm_consensus_block

    can_submit_or_unconfirm = can_submit or can_unconfirm

    """
    There are 3 possible calls
    Steps 1 and 2 are not required and are only here as a backup to keep model peers in uniform

    1. Unconfirm consensus (second step possibility) 
      • If already submitted consensus and model is broken
    2. Submit consensus data (second step possibility)
      • If already unconfirmed and model is healthy
    3. (first step) Submit consensus data (if model is healthy) or unconfirm (if model is broken)
      • This should be the first call of all 3
    """
    if can_submit == False and can_unconfirm == True:
      logger.info("Checking if model is healthy")
      """Previously submitted consensus data - check if model is broken to unconfirm"""
      unconfirm_consensus_count = load_unconfirm_consensus_count()

      """
      Update as last unconfirm consensus block whether we do or don't
      to avoid checking multiple times
      """
      save_last_unconfirm_consensus_block(block_number)

      """
      Only check to unconfirm is others have
      We want to avoid getting peers data if unneeded
      """
      if unconfirm_consensus_count > 0:
        handle_unconfirm_consensus(
          block_number,
          model_id,
          model_initialized,
          peer_initialized,
          model_validator_config.account_id,
          min_required_model_consensus_submit_epochs,
          consensus_blocks_interval,
          min_required_peer_consensus_submit_epochs,
        )
      else:
        logger.info("Model is healthy so far")
    elif can_submit == True and can_unconfirm == False:
      handle_submit_consensus(
        block_number,
        model_id,
        model_initialized,
        peer_initialized,
        model_validator_config.account_id,
        min_required_model_consensus_submit_epochs,
        consensus_blocks_interval,
        min_required_peer_consensus_submit_epochs
      )
    elif can_submit_or_unconfirm:
      logger.info("Checking model state and getting peers data")
      """Has not yet submitted consensus data or unconfirmed consensus data"""
      consensus_data = get_consensus_data(SubstrateConfig.interface, model_id)

      logger.info("Model state is %s" % consensus_data["model_state"])
      logger.info("There are %s peers in the DHT" % len(consensus_data["peers"]))
      logger.info("The min model peers is %s peers" % min_model_peers)

      """If model is broken or zero peers, unconfirm data"""
      if consensus_data["model_state"] == "broken" or len(consensus_data["peers"]) < min_model_peers:
        handle_unconfirm_consensus(
          block_number,
          model_id,
          model_initialized,
          peer_initialized,
          model_validator_config.account_id,
          min_required_model_consensus_submit_epochs,
          consensus_blocks_interval,
          min_required_peer_consensus_submit_epochs,
          consensus_data
        )
      elif consensus_data["model_state"] == "healthy" and len(consensus_data["peers"]) >= min_model_peers:
        handle_submit_consensus(
          block_number,
          model_id,
          model_initialized,
          peer_initialized,
          model_validator_config.account_id,
          min_required_model_consensus_submit_epochs,
          consensus_blocks_interval,
          min_required_peer_consensus_submit_epochs,
          consensus_data
        )

  gc.collect()

def handle_submit_consensus(
  block_number: int,
  model_id: int,
  model_initialized: int,
  peer_initalized: int,
  account_id: str,
  min_required_model_consensus_submit_epochs: int,
  consensus_blocks_interval: int,
  min_required_peer_consensus_submit_epochs: int,
  consensus_data: Optional[Dict] = None
):
  """Previously unconfirmed consensus data - check if model is healthy to submit consensus"""
  """
  Update as last submit consensus block whether we do or don't
  to avoid checking multiple times
  """
  save_last_submit_consensus_block(block_number)

  """Double check blockchain data `can submit data`"""
  eligible_to_submit = eligible_to_submit_consensus_data(
    SubstrateConfig.interface, 
    account_id,
    block_number,
    model_id,
    model_initialized,
    peer_initalized,
    min_required_model_consensus_submit_epochs,
    consensus_blocks_interval,
    min_required_peer_consensus_submit_epochs,
  )

  if eligible_to_submit["eligible"] == True:
    """Get hosting data - Check if model is in healthy state"""
    if consensus_data == None:
      consensus_data = get_consensus_data(SubstrateConfig.interface, model_id)

    """If model is healthy, submit consensus data"""
    if consensus_data["model_state"] == "healthy":
      logger.info("Submiting consensus data")
      receipt = submit_consensus_data(
        SubstrateConfig.interface,
        SubstrateConfig.keypair,
        block_number,
        model_id,
        consensus_data["peers"]
      )
      """Save to local storage"""
      if receipt is not None and receipt.is_success:
        logger.info("Successfully submitted consensus data")
        save_last_submit_consensus_block(block_number)
      else:
        logger.error("Error submitting consensus data")
        error = receipt.error_message['name']
        stop_subscribing = should_stop_block_subscribe(error)
        if stop_subscribing:
          logger.error("We stopped subscribing due to %s", error)
          raise SubscriptionException(error)
        else:
          """Allow up to x retries if failure is unknown after y blocks"""
          # MAX_RETRIES = x
          # CONSENSUS_ATTEMPTS = y
      del receipt
    del consensus_data
  
def handle_unconfirm_consensus(
  block_number: int,
  model_id: int,
  model_initialized: int,
  peer_initialized: int,
  account_id: str,
  min_required_model_consensus_submit_epochs: int,
  consensus_blocks_interval: int,
  min_required_peer_consensus_submit_epochs: int,
  consensus_data: Optional[Dict] = None
):
  eligible_to_unconfirm = eligible_to_unconfirm_consensus_data(
    SubstrateConfig.interface, 
    account_id,
    block_number,
    model_id,
    model_initialized,
    peer_initialized,
    min_required_model_consensus_submit_epochs,
    consensus_blocks_interval,
    min_required_peer_consensus_submit_epochs,
  )
  if eligible_to_unconfirm["eligible"] == True:

    if consensus_data == None:
      consensus_data = get_consensus_data(SubstrateConfig.interface, model_id)

    if consensus_data["model_state"] == "broken":
      logger.info("Unconfirming consensus data, model is broken or not enough peers")
      receipt = unconfirm_consensus_data(
        SubstrateConfig.interface,
        SubstrateConfig.keypair,
        block_number,
        model_id
      )
      """Save to local storage"""
      if receipt is not None and receipt.is_success:
        logger.info("Successfully unconfirmed consensus data")
        save_last_unconfirm_consensus_block(block_number)
      else:
        logger.error("Error unconfirming consensus data")
        error = receipt.error_message['name']
        stop_subscribing = should_stop_block_subscribe(error)
        if stop_subscribing:
          logger.error("We stopped subscribing due to %s", error)
          raise SubscriptionException(error)
      del receipt

def model_consensus_epoch_unconfirm_count_subscription_handler(obj, update_nr, subscription_id):
  count = int(str(obj.value))
  save_unconfirm_consensus_count(count)

  # Check if there are current unconfirms and not just storage resets
  if count > 0:
    network_config = load_network_config()

    block_header = SubstrateConfig.interface.get_block_header()
    block_number = block_header['header']['number']

    _can_submit_consensus = can_submit_consensus(
      block_number,
      network_config.consensus_blocks_interval, 
    )

    last_unconfirm_consensus_block = load_last_unconfirm_consensus_block()
    next_unconfirm_consensus_block = get_next_eligible_submit_consensus_block(
      network_config.consensus_blocks_interval, 
      last_unconfirm_consensus_block
    )

    """
    Save unconfirmed consensus block even if we don't unconfirm
    This will keep up from checking too many times and using unneeded computations
    """
    save_last_unconfirm_consensus_block(block_number)

    can_unconfirm = block_number > next_unconfirm_consensus_block
    if _can_submit_consensus and can_unconfirm:
      model_config = load_model_config()
      model_id = model_config.id
      model_initialized = model_config.initialized

      model_validator_config = load_model_validator_config()

      min_required_model_consensus_submit_epochs = network_config.min_required_model_consensus_submit_epochs
      min_required_peer_consensus_submit_epochs = network_config.min_required_peer_consensus_submit_epochs

      # Only confirm an `unconfirm` towards the latter end of an epoch to allow
      # time for the unconfirming model peer to submit consensus data if the model
      # health becomes healthy for them
      next_unconfirm_consensus_block = get_recheck_consensus_block(
        block_number,
        network_config.consensus_blocks_interval
      )
      
      if next_unconfirm_consensus_block > block_number:
        delta = next_unconfirm_consensus_block - block_number
        time.sleep(delta * BLOCK_SECS)

      p = multiprocessing.Process(
        target=handle_unconfirm_consensus(
          block_number,
          model_id,
          model_initialized,
          model_validator_config.initialized,
          model_validator_config.account_id,
          min_required_model_consensus_submit_epochs,
          network_config.consensus_blocks_interval,
          min_required_peer_consensus_submit_epochs,
        )
      )
      p.start()
      p.join()
      p.close()

def max_models_subscription_handler(obj, update_nr, subscription_id):
  network_config = load_network_config()
  network_config.max_models = int(str(obj.value))
  save_network_config(network_config)
  
def min_model_peers_subscription_handler(obj, update_nr, subscription_id):
  network_config = load_network_config()
  network_config.min_model_peers = int(str(obj.value))
  save_network_config(network_config)
  
def max_model_peers_subscription_handler(obj, update_nr, subscription_id):
  network_config = load_network_config()
  network_config.max_model_peers = int(str(obj.value))
  save_network_config(network_config)
  
def min_stake_balance_subscription_handler(obj, update_nr, subscription_id):
  network_config = load_network_config()
  network_config.min_stake_balance = int(str(obj.value))
  save_network_config(network_config)
  
def tx_rate_limit_subscription_handler(obj, update_nr, subscription_id):
  network_config = load_network_config()
  network_config.tx_rate_limit = int(str(obj.value))
  save_network_config(network_config)
  
def max_zero_consensus_epochs_subscription_handler(obj, update_nr, subscription_id):
  network_config = load_network_config()
  network_config.max_zero_consensus_epochs = float(int(str(obj.value)) / 10000)
  save_network_config(network_config)
  
def min_required_model_consensus_submit_subscription_handler(obj, update_nr, subscription_id):
  network_config = load_network_config()
  network_config.min_required_model_consensus_submit = int(str(obj.value))
  save_network_config(network_config)
  
def min_required_peer_consensus_submit_epochs_subscription_handler(obj, update_nr, subscription_id):
  network_config = load_network_config()
  network_config.min_required_peer_consensus_submit_epochs = int(str(obj.value))
  save_network_config(network_config)
  
def min_required_peer_consensus_inclusion_epochs_subscription_handler(obj, update_nr, subscription_id):
  network_config = load_network_config()
  network_config.min_required_peer_consensus_inclusion_epochs = int(str(obj.value))
  save_network_config(network_config)
  
def maximum_outlier_delta_percent_subscription_handler(obj, update_nr, subscription_id):
  network_config = load_network_config()
  network_config.maximum_outlier_delta_percent = float(int(str(obj.value)) / 100)
  save_network_config(network_config)
  
def consensus_blocks_interval_subscription_handler(obj, update_nr, subscription_id):
  network_config = load_network_config()
  network_config.consensus_blocks_interval = int(str(obj.value))
  save_network_config(network_config)

def remove_model_peer_epoch_percentage_subscription_handler(obj, update_nr, subscription_id):
  network_config = load_network_config()
  network_config.remove_model_peer_epoch_percentage = int(str(obj.value))
  save_network_config(network_config)

"""
Returns `True` if we should stop subscribing to blocks if the specific reasons are met
"""
def should_stop_block_subscribe(reason: str) -> bool:
  if reason == "AccountIneligible" or reason == "ModelNotExist" or reason == "ModelPeerNotExist":
    return True
  else:
    return False

if __name__ == "__main__":
  """Begin subscribing to new block headers after running `python src/petals/substrate/subscriptions.py`"""
  block_listener()

  result = SubstrateConfig.interface.query(
    "Network", 
    "MaxModels", 
    subscription_handler=max_models_subscription_handler
  )
  result = SubstrateConfig.interface.query(
    "Network", 
    "MinModelPeers", 
    subscription_handler=min_model_peers_subscription_handler
  )
  result = SubstrateConfig.interface.query(
    "Network", 
    "MaxModelPeers", 
    subscription_handler=max_model_peers_subscription_handler
  )
  result = SubstrateConfig.interface.query(
    "Network", 
    "MinStakeBalance", 
    subscription_handler=min_stake_balance_subscription_handler
  )
  result = SubstrateConfig.interface.query(
    "Network", 
    "TxRateLimit", 
    subscription_handler=tx_rate_limit_subscription_handler
  )
  result = SubstrateConfig.interface.query(
    "Network", 
    "MaxZeroConsensusEpochs", 
    subscription_handler=max_zero_consensus_epochs_subscription_handler
  )
  result = SubstrateConfig.interface.query(
    "Network", 
    "MinRequiredModelConsensusSubmitEpochs", 
    subscription_handler=min_required_model_consensus_submit_subscription_handler
  )
  result = SubstrateConfig.interface.query(
    "Network", 
    "MinRequiredPeerConsensusSubmitEpochs", 
    subscription_handler=min_required_peer_consensus_submit_epochs_subscription_handler
  )
  result = SubstrateConfig.interface.query(
    "Network", 
    "MinRequiredPeerConsensusInclusionEpochs", 
    subscription_handler=min_required_peer_consensus_inclusion_epochs_subscription_handler
  )
  result = SubstrateConfig.interface.query(
    "Network", 
    "MaximumOutlierDeltaPercent", 
    subscription_handler=maximum_outlier_delta_percent_subscription_handler
  )
  result = SubstrateConfig.interface.query(
    "Network", 
    "ConsensusBlocksInterval", 
    subscription_handler=consensus_blocks_interval_subscription_handler
  )
  result = SubstrateConfig.interface.query(
    "Network", 
    "ModelConsensusEpochUnconfirmedCount", 
    subscription_handler=model_consensus_epoch_unconfirm_count_subscription_handler
  )

  result = SubstrateConfig.interface.query(
    "Network", 
    "RemoveModelPeerEpochPercentage", 
    subscription_handler=remove_model_peer_epoch_percentage_subscription_handler
  )