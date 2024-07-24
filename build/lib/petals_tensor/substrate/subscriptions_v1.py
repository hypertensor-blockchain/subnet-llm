from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException
from tenacity import retry, stop_after_attempt, wait_exponential
from config import load_model_config, load_model_validator_config, load_network_config, save_model_config, save_model_validator_config, save_network_config, SubstrateConfig
from chain_data import ModelPeerData
from utils import get_blockchain_peers_consensus_data, get_consensus_data, get_next_eligible_submit_consensus_block, is_in_consensus_steps, load_last_submit_consensus_block, load_last_unconfirm_consensus_block, load_unconfirm_consensus_count, save_last_submit_consensus_block, save_last_unconfirm_consensus_block, save_unconfirm_consensus_count
from submit_consensus import eligible_to_submit_consensus_data, eligible_to_unconfirm_consensus_data
from chain_functions import get_model_peers, get_model_peers_model_unconfirmed_count, submit_consensus_data, unconfirm_consensus_data

# source .venv/bin/activate
# python src/petals/substrate/subscriptions_v1.py

def block_subscription_handler(obj, update_nr, subscription_id):
  """
  Block subsctipion handler used for submitting consensus data only
  """
  block_number = obj['header']['number']
  print(f"New block #{block_number}")

  network_config = load_network_config()

  in_consensus_steps = is_in_consensus_steps(
    block_number,
    network_config.consensus_blocks_interval, 
  )

  if in_consensus_steps == False: 
    model_config = load_model_config()
    model_id = model_config.id
    model_initialized = model_config.initialized

    min_required_model_consensus_submit_epochs = network_config.min_required_model_consensus_submit_epochs
    min_required_peer_consensus_submit_epochs = network_config.min_required_peer_consensus_submit_epochs

    model_validator_config = load_model_validator_config()

    last_submit_consensus_block = load_last_submit_consensus_block()
    last_unconfirm_consensus_block = load_last_unconfirm_consensus_block()

    next_submit_consensus_block = get_next_eligible_submit_consensus_block(
      network_config.consensus_blocks_interval, 
      last_submit_consensus_block
    )

    next_unconfirm_consensus_block = get_next_eligible_submit_consensus_block(
      network_config.consensus_blocks_interval, 
      last_unconfirm_consensus_block
    )

    can_submit = block_number > next_submit_consensus_block
    print("can_submit ->", can_submit)
    can_unconfirm = block_number > next_unconfirm_consensus_block
    print("can_unconfirm ->", can_unconfirm)
    can_submit_or_unconfirm = can_submit or can_unconfirm

    """variables for undoing consensus submit or unconfirm"""
    """
    Wait until the latter portion of the epoch to undo either a submission or unconfirm
    """
    consensus_blocks_interval = network_config.consensus_blocks_interval
    print("consensus_blocks_interval ->", consensus_blocks_interval)
    latter_of_epoch_undo_percentage = 0.10
    latter_blocks_span = consensus_blocks_interval * latter_of_epoch_undo_percentage
    print("latter_blocks_span ->", latter_blocks_span)
    min_block = block_number - (block_number % consensus_blocks_interval) + consensus_blocks_interval - latter_blocks_span
    print("min_block ->", min_block)
    max_block = consensus_blocks_interval + block_number - (block_number % consensus_blocks_interval)
    print("max_block ->", max_block)

    """If in span of blocks to submit unconfirm"""
    in_undo_blocks_span = min_block <= block_number < max_block
    print("in_undo_blocks_span ->", in_undo_blocks_span)
    """Only undo every 10 blocks"""
    in_undo_block = block_number % 10 == 0
    print("in_undo_block ->", in_undo_block)

    """
    There are 3 possible calls
    Steps 1 and 2 are not required and are only here as a backup to keep model peers in uniform

    1. Unconfirm consensus (second step possibility) 
      • If already submitted consensus and model is broken
    2. Submit consensus data (second step possibility)
      • If already unconfirmed and model is healthy
    3. (first step) Submit consensus data (if model is healthy) or unconfirm (if model is broken)
      • This is the first call of all 3
    """
    if in_undo_blocks_span and in_undo_block and can_submit == False and can_unconfirm == True:
      print("if in_undo_blocks_span 1 ->")
      """Previously submitted consensus data - check if model is broken to unconfirm"""
      unconfirm_consensus_count = load_unconfirm_consensus_count()
      """
      Only check to unconfirm is others have
      We want to avoid getting peers data if unneeded
      """
      if unconfirm_consensus_count > 0:
        """
        Update as last unconfirm consensus block whether we do or don't
        to avoid checking multiple times
        """
        save_last_unconfirm_consensus_block(block_number)

        """Double check blockchain data `can unconfirm data`"""
        eligible_to_unconfirm = eligible_to_unconfirm_consensus_data(
          SubstrateConfig.interface, 
          model_validator_config.account_id,
          block_number,
          model_id,
          model_initialized,
          min_required_model_consensus_submit_epochs,
          network_config.consensus_blocks_interval,
          min_required_peer_consensus_submit_epochs,
        )

        if eligible_to_unconfirm == True:
          """Get hosting data - Check if model is in broken state"""
          consensus_data = get_consensus_data(SubstrateConfig.interface, model_id)

          """If model is broken, unconfirm data"""
          if consensus_data["model_state"] == "broken":
            unconfirm_consensus_data(
              SubstrateConfig.interface,
              SubstrateConfig.keypair,
              block_number,
              model_id,
            )
    elif in_undo_blocks_span and in_undo_block and can_submit == True and can_unconfirm == False:
      print("if in_undo_blocks_span 2 ->")
      """Previously unconfirmed consensus data - check if model is healthy to submit consensus"""
      """
      Update as last submit consensus block whether we do or don't
      to avoid checking multiple times
      """
      save_last_submit_consensus_block(block_number)

      """Double check blockchain data `can submit data`"""
      eligible_to_submit = eligible_to_submit_consensus_data(
        SubstrateConfig.interface, 
        model_validator_config.account_id,
        block_number,
        model_id,
        model_initialized,
        min_required_model_consensus_submit_epochs,
        network_config.consensus_blocks_interval,
        min_required_peer_consensus_submit_epochs,
      )

      if eligible_to_submit == True:
        """Get hosting data - Check if model is in healthy state"""
        consensus_data = get_consensus_data(SubstrateConfig.interface, model_id)

        """If model is healthy, submit consensus data"""
        if consensus_data["model_state"] == "healthy":
          submit_consensus_data(
            SubstrateConfig.interface,
            SubstrateConfig.keypair,
            block_number,
            model_id,
            consensus_data
          )
    elif can_submit_or_unconfirm:
      print("else in_undo_blocks_span ->")
      """Has not yet submitted consensus data or unconfirmed consensus data"""
      consensus_data = get_consensus_data(SubstrateConfig.interface, model_id)


      """If model is broken or zero peers, unconfirm data"""
      if consensus_data["model_state"] == "broken" or len(consensus_data["peers"]) == 0:
        """Double check blockchain data `can unconfirm data`"""
        eligible_to_unconfirm = eligible_to_unconfirm_consensus_data(
          SubstrateConfig.interface, 
          model_validator_config.account_id,
          block_number,
          model_id,
          model_initialized,
          min_required_model_consensus_submit_epochs,
          network_config.consensus_blocks_interval,
          min_required_peer_consensus_submit_epochs,
        )
        if eligible_to_unconfirm:
          unconfirm_consensus_data(
            SubstrateConfig.interface,
            SubstrateConfig.keypair,
            block_number,
            model_id
          )
      elif len(consensus_data["peers"]) > 0:
        """If model is healthy with peers, submit consensus data"""
        """Double check blockchain data `can submit data`"""
        model_config = load_model_config()

        eligible_to_submit = eligible_to_submit_consensus_data(
          SubstrateConfig.interface, 
          model_validator_config.account_id,
          block_number,
          model_id,
          model_initialized,
          min_required_model_consensus_submit_epochs,
          network_config.consensus_blocks_interval,
          min_required_peer_consensus_submit_epochs,
        )

        if eligible_to_submit:
          submit_consensus_data(
            SubstrateConfig.interface,
            SubstrateConfig.keypair,
            block_number,
            model_id,
            consensus_data
          )

# def block_subscription_handler(obj, update_nr, subscription_id):
#   """
#   Block subsctipion handler used for submitting consensus data only
#   """
#   block_number = obj['header']['number']
#   print(f"New block #{block_number}")

#   network_config = load_network_config()

#   in_consensus_steps = is_in_consensus_steps(
#     block_number,
#     network_config.consensus_blocks_interval, 
#   )

#   if in_consensus_steps == False: 

#     last_submit_consensus_block = load_last_submit_consensus_block()
#     last_unconfirm_consensus_block = load_last_unconfirm_consensus_block()
#     unconfirm_count = load_unconfirm_consensus_count()

#     next_submit_consensus_block = get_next_eligible_submit_consensus_block(
#       network_config.consensus_blocks_interval, 
#       last_submit_consensus_block
#     )

#     next_unconfirm_consensus_block = get_next_eligible_submit_consensus_block(
#       network_config.consensus_blocks_interval, 
#       last_unconfirm_consensus_block
#     )

#     can_submit = block_number > next_submit_consensus_block
#     can_unconfirm = block_number > next_unconfirm_consensus_block
#     can_submit_or_unconfirm = can_submit or can_unconfirm

#     if can_submit_or_unconfirm:
#       result = get_model_peers(
#         substrate,
#       )
#       model_peers_data = ModelPeerData.list_from_vec_u8(result["result"])
#       print("model_peers_data: ", model_peers_data)

#       consensus_data = get_blockchain_peers_consensus_data(model_peers_data)
#       print("consensus_data: ", consensus_data)

#       if consensus_data["peers"] == "broken":
#         """If model is broken unconfirm data"""
#         unconfirm_consensus_data(
#           substrate,
#           SubstrateConfig.keypair,
#           consensus_data
#         )
#       elif len(consensus_data["peers"]) > 0:
#         """If model is healthy with peers submit consensus data"""
#         submit_consensus_data(
#           substrate,
#           SubstrateConfig.keypair,
#           consensus_data
#         )



#     is_model_broken = True 
#     consensus_data = {}



#     """
#     If unconfirm count is greater than 0 validate this is true
#     """
#     if unconfirm_count > 0:
#       eligible_to_unconfirm = eligible_to_unconfirm_consensus_data(
#         substrate,
#         model_validator_config.account_id,
#         block_number,
#         network_config.consensus_blocks_interval,
#       )
#     else:
#       """"""


#     if consensus_data["state"] == "healthy" and eligible_to_submit["eligible"]:
#       """"""

#     elif consensus_data["state"] == "broken" and eligible_to_unconfirm["eligible"]:
#       """"""











#     model_config = load_model_config()
#     model_validator_config = load_model_validator_config()

#     eligible_to_submit = eligible_to_submit_consensus_data(
#       substrate, 
#       model_validator_config.account_id,
#       block_number,
#       network_config.consensus_blocks_interval,
#       model_config.id,
#     )

#     print("eligible_to_submit: ", eligible_to_submit)

#     if eligible_to_submit["eligible"]:
#       result = get_model_peers(
#         substrate,
#       )
#       model_peers_data = ModelPeerData.list_from_vec_u8(result["result"])
#       print("model_peers_data: ", model_peers_data)

#       consensus_data = get_blockchain_peers_consensus_data(model_peers_data)
#       print("consensus_data: ", consensus_data)

#       if consensus_data["peers"] == "broken":
#         unconfirm_consensus_data(
#           substrate,
#           SubstrateConfig.keypair,
#           consensus_data
#         )
#       elif len(consensus_data["peers"]) > 0:
#         submit_consensus_data(
#           substrate,
#           SubstrateConfig.keypair,
#           consensus_data
#         )

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

def model_consensus_epoch_unconfirm_count_subscription_handler(obj, update_nr, subscription_id):
  count = int(str(obj.value))
  save_unconfirm_consensus_count(count)

  if count > 0:
    network_config = load_network_config()
    last_unconfirm_consensus_block = load_last_unconfirm_consensus_block()
    next_unconfirm_consensus_block = get_next_eligible_submit_consensus_block(
      network_config.consensus_blocks_interval, 
      last_unconfirm_consensus_block
    )

    block_header = SubstrateConfig.interface.get_block_header()
    block_number = block_header['header']['number']

    """
    Save unconfirmed consensus block even if we don't unconfirm
    This will keep up from checking too many times and using unneeded computations
    """
    save_last_unconfirm_consensus_block(block_number)

    can_unconfirm = block_number > next_unconfirm_consensus_block
    if can_unconfirm:
      model_config = load_model_config()
      model_id = model_config.id
      model_initialized = model_config.initialized

      model_validator_config = load_model_validator_config()

      min_required_model_consensus_submit_epochs = network_config.min_required_model_consensus_submit_epochs
      min_required_peer_consensus_submit_epochs = network_config.min_required_peer_consensus_submit_epochs

      """If model is broken unconfirm data"""
      """Double check blockchain can unconfirm data"""
      eligible_to_unconfirm = eligible_to_unconfirm_consensus_data(
        SubstrateConfig.interface, 
        model_validator_config.account_id,
        block_number,
        model_id,
        model_initialized,
        min_required_model_consensus_submit_epochs,
        network_config.consensus_blocks_interval,
        min_required_peer_consensus_submit_epochs,
      )

      if eligible_to_unconfirm == True:
        consensus_data = get_consensus_data(SubstrateConfig.interface, model_id)

        if consensus_data["peers"] == "broken":
          if eligible_to_unconfirm:
            unconfirm_consensus_data(
              SubstrateConfig.interface, 
              SubstrateConfig.keypair,
              block_number,
              model_id
            )

def initialize_subscribe_block_headers():
  SubstrateConfig.interface.subscribe_block_headers(block_subscription_handler)

initialize_subscribe_block_headers()

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