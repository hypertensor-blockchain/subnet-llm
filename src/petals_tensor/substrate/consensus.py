import threading
import time
from petals_tensor.substrate.chain_functions import attest, get_epoch_length, get_min_required_model_consensus_submit_epochs, get_min_required_peer_consensus_submit_epochs, get_model_activated, get_model_data, get_model_path_id, get_rewards_submission, get_rewards_validator, validate
from petals_tensor.substrate.config import BLOCK_SECS, SubnetDataConfig, SubstrateConfig, load_subnet_config, load_model_validator_config, load_network_config, save_subnet_config
from petals_tensor.substrate.utils import get_consensus_data, get_eligible_consensus_block, get_next_eligible_submit_consensus_block, get_next_epoch_start_block, get_submittable_nodes, load_last_submit_consensus_block
from petals_tensor.validator.inference_validator import InferenceValidator
from hivemind.utils import get_logger

logger = get_logger(__name__)

class Consensus(threading.Thread):
  """
  Houses logic for validating and attesting consensus data per epochs for rewards

  This can be ran before or during a model activation.

  If before, it will wait until the subnet is successfully voted in, if the proposal to initialize the subnet fails,
  it will not stop running.

  If after, it will begin to validate and or attest epochs
  """
  def __init__(self, path: str):
    super().__init__()
    self.subnet_id = None
    self.path = path
    self.account_id = SubstrateConfig.account_id
    self.subnet_accepting_consensus = False
    self.subnet_node_eligible = False
    # self.subnet_initialized = False

    # blockchain constants
    self.epoch_length = int(str(get_epoch_length(SubstrateConfig.interface)))

    # delete pickles if exist

    # create clean pickles

  def run(self):
    while True:
      """"""
      try:
        # get epoch
        block_hash = SubstrateConfig.interface.get_block_hash()
        block_number = SubstrateConfig.interface.get_block_number(block_hash)
        logger.info("Block height: %s " % block_number)

        epoch = int(block_number / self.epoch_length)
        logger.info("Epoch: %s " % epoch)

        next_epoch_start_block = get_next_epoch_start_block(
          self.epoch_length, 
          block_number
        )
        remaining_blocks_until_next_epoch = next_epoch_start_block - block_number
        
        # Ensure subnet is activated
        if self.subnet_accepting_consensus == False:
          activated = self._activate_subnet()
          if activated == True:
            continue
          else:
            # Sleep until voting is complete
            time.sleep(remaining_blocks_until_next_epoch * BLOCK_SECS)
            continue

        # The subnet is activated at this point
        # 1. Check if subnet can accept consensus
        # 2. Check if node is submittable
        network_config = load_network_config()

        """
        Is subnet initialized
        """

        subnet_config = load_subnet_config()
        model_initialized = subnet_config.initialized
        min_required_model_consensus_submit_epochs = network_config.min_required_model_consensus_submit_epochs

        subnet_eligible_block = get_eligible_consensus_block(
          self.epoch_length, 
          model_initialized, 
          min_required_model_consensus_submit_epochs
        )

        is_subnet_consensus_eligible = subnet_eligible_block != None and block_number >= subnet_eligible_block

        # is subnet eligible for consensus (must be initialized for minimum required epochs)
        if is_subnet_consensus_eligible == False:
          delta = subnet_eligible_block - block_number
          logger.info("Model begins accepting consensus on block %s, going to sleep for %s blocks " % (subnet_eligible_block, delta))
          time.sleep(delta * BLOCK_SECS)
          continue



        """
        Is subnet node initialized and eligible to submit consensus
        """
        # subnet is eligible to accept consensus
        # check if we are submittable
        # in order to be submittable:
        # - Must stake onchain
        # - Must be Submittable subnet node class
        if self.subnet_node_eligible == False:
          submittable_nodes = get_submittable_nodes(SubstrateConfig.interface, self.subnet_id)

          for node_set in submittable_nodes:
            if node_set[0] == self.account_id:
              self.subnet_node_eligible = True
              break
          
          if self.subnet_node_eligible == False:
            logger.info("Node not eligible for consensus, sleeping until next epoch")
            time.sleep(remaining_blocks_until_next_epoch * BLOCK_SECS)
            continue

        # is epoch submitted yet

        # is validator?
        validator = self._get_validator(epoch)

        if validator == None:
          logger.info("Validator not chosen for epoch %s yet, checking next block" % epoch)
          time.sleep(BLOCK_SECS)
          continue
        else:
          logger.info("Validator for epoch %s is %s" % (epoch, validator))

        is_validator = validator == self.account_id
        if is_validator:
          logger.info("We're the chosen validator for epoch %s, validating and auto-attesting..." % epoch)
          # check if validated 
          validated = False
          if validated is False:
            self.validate()

          # continue to next epoch, no need to attest
          time.sleep(remaining_blocks_until_next_epoch * BLOCK_SECS)
          continue

        # we are not validator, we must attest or not attest
        # wait until validated by epochs chosen validator

        # get epoch before waiting for validator to validate to ensure we don't get stuck 
        initial_epoch = epoch
        attestation_complete = False
        logger.info("Starting attestation check")
        while True:
          # wait for validator on every block
          time.sleep(BLOCK_SECS)
          block_hash = SubstrateConfig.interface.get_block_hash()
          block_number = SubstrateConfig.interface.get_block_number(block_hash)
          logger.info("Block height: %s " % block_number)

          epoch = int(block_number / self.epoch_length)
          logger.info("Epoch: %s " % epoch)

          # If we made it to the next epoch, break
          # This likely means the chosen validator never submitted consensus data
          if epoch > initial_epoch:
            logger.info("Validator didn't submit consensus data, moving to the next epoch: %s" % epoch)
            break

          result = self.attest(epoch)
          if result == None:
            # If None, still waiting for validator to submit data
            continue
          else:
            break
      except Exception as e:
        logger.error("Consensus Error: %s" % e)

  def validate(self):
    """Get rewards data and submit consensus"""
    consensus_data = self._get_consensus_data()
    self._do_validate(consensus_data["peers"])

  def attest(self, epoch: int):
    """Get rewards data from another validator and attest that data if valid"""
    validator_consensus_data = self._get_validator_consensus_data(epoch)

    if validator_consensus_data == None:
      logger.info("Waiting for validator to submit")
      return None

    valid = True

    logger.info("Checking if we should attest the validators submission")


    """
    """
    # For testing
    # Simply validate to ensure mechanism compatibility

    # logger.info("Generating consensus data")
    # consensus_data = self._get_consensus_data()

    # self.should_attest(validator_consensus_data, consensus_data)

    # if len(validator_consensus_data) != len(consensus_data):
    #   valid = False

    # for i in range(len(consensus_data)):
    #   if consensus_data[i] != validator_consensus_data[i]:
    #       valid = False
    #       break

    # for data in consensus_data:
    #   for validator_data in validator_consensus_data:
    #     """"""
    #     is_valid = False
    #     if not is_valid:
    #       valid = False
    #       break

    if valid:
      logger.info("Validators data is confirmed valid, attesting data...")
      self._do_attest()
    else:
      logger.info("Validators data is not valid, skipping attestation.")
    
  def _do_validate(self, data):
    logger.info("Validating the epoch and submitting rewards data!")
    receipt = validate(
      SubstrateConfig.interface,
      SubstrateConfig.keypair,
      self.subnet_id,
      data
    )

  def _do_attest(self):
    logger.info("Attesting the current validators rewards data submission!")
    receipt = attest(
      SubstrateConfig.interface,
      SubstrateConfig.keypair,
      self.subnet_id,
    )
    
  def _get_consensus_data(self):
    """"""
    consensus_data = get_consensus_data(SubstrateConfig.interface, self.subnet_id)
    return consensus_data

  def _get_validator_consensus_data(self, epoch: int):
    """Get and return the consensus data from the current validator"""
    rewards_submission = get_rewards_submission(
      SubstrateConfig.interface,
      self.subnet_id,
      epoch
    )
    return rewards_submission

  def _get_validator(self, epoch):
    validator = get_rewards_validator(
      SubstrateConfig.interface,
      self.subnet_id,
      epoch
    )
    return validator
  
  def _activate_subnet(self):
    """
    Attempt to activate subnet

    Will wait for subnet to be voted in

    Returns:
      bool: True if subnet was successfully activated, False otherwise.
    """
    activated = get_model_activated(SubstrateConfig.interface, self.path)

    if activated['active'] == True:
      logger.info("Subnet activated, just getting things set up for consensus...")
      self.subnet_accepting_consensus = True
      subnet_id = get_model_path_id(
        SubstrateConfig.interface,
        self.path
      )
      self.subnet_id = int(str(subnet_id))

      subnet_data = get_model_data(
        SubstrateConfig.interface,
        subnet_id
      )

      subnet_config = SubnetDataConfig()
      # Override previous configuration
      subnet_config.initialize(
        True,
        int(str(subnet_id)),
        self.path,
        int(str(subnet_data["min_nodes"])),
        int(str(subnet_data["target_nodes"])),
        int(str(subnet_data["memory_mb"])),
        int(str(subnet_data["initialized"]))
      )

      """
      Save Pickle
      """
      save_subnet_config(subnet_config)
      return True
    else:
      return False

  def should_attest(validator_data, my_data):
      """Checks if two arrays of dictionaries match, regardless of order."""

      if len(validator_data) != len(my_data):
          return False

      set1 = set(frozenset(d.items()) for d in validator_data)
      set2 = set(frozenset(d.items()) for d in my_data)

      intersection = set1.intersection(set2)
      logger.info("Matching intersection of %s validator data" % ((len(set1)-intersection)/len(set1)))
      logger.info("Validator matching intersection of %s my data" % ((len(set2)-intersection)/len(set2)))

      return set1 == set2
