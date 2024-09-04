"""
Substrate config file for storing blockchain configuration and parameters in a pickle
to avoid remote blockchain calls
"""
import dataclasses
from substrateinterface import SubstrateInterface, Keypair
import pickle

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(Path.cwd(), '.env'))

"""Store your mnemonic phrase in the `.env` file"""
PHRASE = os.getenv('PHRASE')

# local
LOCAL_URL = os.getenv('LOCAL_RPC')
# development
"""Enter a valid URL and port of a RPC node"""
DEV_URL = os.getenv('DEV_RPC')
# live
LIVE_URL = os.getenv('LIVE_RPC')

# s per block
BLOCK_SECS = 6

# percentage of latter end of an epoch to recheck model health if needed
PERCENTAGE_EPOCH_HEALTH_CONSENSUS_RECHECK = .35

@dataclasses.dataclass
class SubstrateConfig:
  """
  Fill in the `.env` file in the root directory with your mnemonic phrase
  """
  url: str = DEV_URL  # url to substrate
  interface: SubstrateInterface = SubstrateInterface(url=DEV_URL)
  keypair: Keypair = Keypair.create_from_uri(PHRASE)
  account_id: str = Keypair.create_from_uri(PHRASE).ss58_address

class SubnetDataConfig:
  """
  The data fills in when running `python -m petals.cli.run_server`
  """
  _instance = None

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def initialize(
    self, 
    activated: bool, 
    id: int, 
    path: str, 
    min_nodes: int, 
    target_nodes: int, 
    memory_mb: int, 
    initialized: int
  ):
    self.activated = activated
    self.id = id
    self.path = path
    self.min_nodes = min_nodes
    self.target_nodes = target_nodes
    self.memory_mb = memory_mb
    self.initialized = initialized

def save_subnet_config(data: SubnetDataConfig):
  """
  Save the model data configuration

  Args:
    data (SubnetDataConfig): The model data configuration
  """

  dbfile = open('model_data_config', 'wb')
  pickle.dump(data, dbfile)                    
  dbfile.close()

def load_subnet_config():
  """
  Load the model data configuration

  Returns:
    SubnetDataConfig: The model data configuration
  """
  with open('model_data_config', 'rb') as dbfile:
    db = pickle.load(dbfile)
    return db

  # dbfile = open('model_data_config', 'rb')    
  # db = pickle.load(dbfile)
  
  # # for keys in db:
  # dbfile.close()
  # return db

class ModelValidatorConfig:
  """
  Fill in the `.env` file in the root directory with your mnemonic phrase

  The data fills in when running `python -m petals.cli.run_server`
  """
  _instance = None
  account_id: str = Keypair.create_from_uri(PHRASE).ss58_address

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def initialize(self, peer_id: str, ip: str, port: int, initialized: int):
    self.peer_id = peer_id
    self.ip = ip
    self.port = port
    self.initialized = initialized
    self.removed = 0

  def remove(self, removed: int):
    self.removed = removed

def save_model_validator_config(data: ModelValidatorConfig):
  """
  Save the model validator configuration

  Args:
    data (ModelValidatorConfig): The model validator configuration
  """

  with open('model_validator_config', 'wb') as dbfile:
    pickle.dump(data, dbfile, pickle.HIGHEST_PROTOCOL)
  # dbfile = open('model_validator_config', 'wb')
  # pickle.dump(data, dbfile)                    
  # dbfile.close()

def load_model_validator_config():
  """
  Load the model validator configuration

  Returns:
    ModelValidatorConfig: The model validator configuration
  """

  with open('model_validator_config', 'rb') as dbfile:
    db = pickle.load(dbfile)
    return db

class NetworkConfig:
  """
  Run `python -m petals.cli.run_update_network_config` to fill
  """
  _instance = None

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def initialize(
    self,
    epoch_length: int,
    min_required_model_consensus_submit_epochs: int,
    min_required_peer_consensus_submit_epochs: int,
    min_required_peer_consensus_inclusion_epochs: int,
    min_model_peers: int,
    max_model_peers: int,
    max_models: int,
    tx_rate_limit: int,
    min_stake_balance: int,
    maximum_outlier_delta_percent: float,
    max_zero_consensus_epochs: int,
    remove_model_peer_epoch_percentage: float
  ):
    self.epoch_length = epoch_length
    self.min_required_model_consensus_submit_epochs = min_required_model_consensus_submit_epochs
    self.min_required_peer_consensus_submit_epochs = min_required_peer_consensus_submit_epochs
    self.min_required_peer_consensus_inclusion_epochs = min_required_peer_consensus_inclusion_epochs
    self.min_model_peers = min_model_peers
    self.max_model_peers = max_model_peers
    self.max_models = max_models
    self.tx_rate_limit = tx_rate_limit
    self.min_stake_balance = min_stake_balance
    self.maximum_outlier_delta_percent = maximum_outlier_delta_percent
    self.max_zero_consensus_epochs = max_zero_consensus_epochs
    self.remove_model_peer_epoch_percentage = remove_model_peer_epoch_percentage

def save_network_config(data: NetworkConfig):
  """
  Save the network configuration

  Args:
    data (NetworkConfig): The network configuration
  """

  dbfile = open('network_config', 'wb')
  pickle.dump(data, dbfile)                    
  dbfile.close()

def load_network_config():
  """
  Load the network configuration

  Returns:
    NetworkConfig: The network configuration
  """

  dbfile = open('network_config', 'rb')    
  db = pickle.load(dbfile)
  dbfile.close()
  return db

class NetworkRuntimeParameters:
  """
  Run `python -m petals.cli.run_update_network_config` to fill
  """
  _instance = None

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def initialize(
    self,
    epoch_length: int,
    min_required_model_consensus_submit_epochs: int,
    min_required_peer_consensus_submit_epochs: int,
    min_required_peer_consensus_inclusion_epochs: int,
    min_model_peers: int,
    max_model_peers: int,
    max_models: int,
    tx_rate_limit: int,
    min_stake_balance: int,
    maximum_outlier_delta_percent: float,
    max_zero_consensus_epochs: int,
    remove_model_peer_epoch_percentage: float
  ):
    self.epoch_length = epoch_length
    self.min_required_model_consensus_submit_epochs = min_required_model_consensus_submit_epochs
    self.min_required_peer_consensus_submit_epochs = min_required_peer_consensus_submit_epochs
    self.min_required_peer_consensus_inclusion_epochs = min_required_peer_consensus_inclusion_epochs
    self.min_model_peers = min_model_peers
    self.max_model_peers = max_model_peers
    self.max_models = max_models
    self.tx_rate_limit = tx_rate_limit
    self.min_stake_balance = min_stake_balance
    self.maximum_outlier_delta_percent = maximum_outlier_delta_percent
    self.max_zero_consensus_epochs = max_zero_consensus_epochs
    self.remove_model_peer_epoch_percentage = remove_model_peer_epoch_percentage

def save_network_config(data: NetworkConfig):
  """
  Save the network configuration

  Args:
    data (NetworkConfig): The network configuration
  """

  dbfile = open('network_config', 'wb')
  pickle.dump(data, dbfile)                    
  dbfile.close()

def load_network_config():
  """
  Load the network configuration

  Returns:
    NetworkConfig: The network configuration
  """

  dbfile = open('network_config', 'rb')    
  db = pickle.load(dbfile)
  dbfile.close()
  return db
