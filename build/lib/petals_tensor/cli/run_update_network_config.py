"""
Return peer data stored in the substrate config

Note: In dev mode the blockchain must be running

python -m petals_tensor.cli.run_update_network_config
"""
import logging
from petals_tensor.substrate import config as substrate_config
from petals_tensor.substrate.chain_functions import get_consensus_blocks_interval, get_max_model_peers, get_max_models, get_max_model_consensus_epochs, get_maximum_outlier_delta_percent, get_min_model_peers, get_min_required_model_consensus_submit_epochs, get_min_required_peer_consensus_inclusion_epochs, get_min_required_peer_consensus_submit_epochs, get_min_stake_balance, get_remove_model_peer_epoch_percentage, get_tx_rate_limit

logger = logging.getLogger(__name__)

def main():
  consensus_blocks_interval = get_consensus_blocks_interval(substrate_config.SubstrateConfig.interface)
  print("consensus_blocks_interval", consensus_blocks_interval)
  min_required_model_consensus_submit_epochs = get_min_required_model_consensus_submit_epochs(substrate_config.SubstrateConfig.interface)
  print("min_required_model_consensus_submit_epochs", min_required_model_consensus_submit_epochs)
  min_required_peer_consensus_submit_epochs = get_min_required_peer_consensus_submit_epochs(substrate_config.SubstrateConfig.interface)
  print("min_required_peer_consensus_submit_epochs", min_required_peer_consensus_submit_epochs)
  min_required_peer_consensus_inclusion_epochs = get_min_required_peer_consensus_inclusion_epochs(substrate_config.SubstrateConfig.interface)
  print("min_required_peer_consensus_inclusion_epochs", min_required_peer_consensus_inclusion_epochs)
  min_model_peers = get_min_model_peers(substrate_config.SubstrateConfig.interface)
  print("min_model_peers", min_model_peers)
  max_model_peers = get_max_model_peers(substrate_config.SubstrateConfig.interface)
  print("max_model_peers", max_model_peers)
  max_models = get_max_models(substrate_config.SubstrateConfig.interface)
  print("max_models", max_models)
  min_stake_balance = get_min_stake_balance(substrate_config.SubstrateConfig.interface)
  print("min_stake_balance", min_stake_balance)
  tx_rate_limit = get_tx_rate_limit(substrate_config.SubstrateConfig.interface)
  print("tx_rate_limit", tx_rate_limit)
  max_zero_consensus_epochs = get_max_model_consensus_epochs(substrate_config.SubstrateConfig.interface)
  print("max_zero_consensus_epochs", max_zero_consensus_epochs)
  maximum_outlier_delta_percent = get_maximum_outlier_delta_percent(substrate_config.SubstrateConfig.interface)
  print("maximum_outlier_delta_percent", float(int(str(maximum_outlier_delta_percent)) / 100))
  remove_model_peer_epoch_percentage = get_remove_model_peer_epoch_percentage(substrate_config.SubstrateConfig.interface)
  print("remove_model_peer_epoch_percentage", float(int(str(remove_model_peer_epoch_percentage)) / 10000))

  """
  Initialize Pickle
  """
  network_config = substrate_config.NetworkConfig()

  network_config.initialize(
    int(str(consensus_blocks_interval)),
    int(str(min_required_model_consensus_submit_epochs)),
    int(str(min_required_peer_consensus_submit_epochs)),
    int(str(min_required_peer_consensus_inclusion_epochs)),
    int(str(min_model_peers)),
    int(str(max_model_peers)),
    int(str(max_models)),
    int(str(tx_rate_limit)),
    int(str(min_stake_balance)),
    float(int(str(maximum_outlier_delta_percent)) / 100),
    int(str(max_zero_consensus_epochs)),
    float(int(str(remove_model_peer_epoch_percentage)) / 10000)
  )

  """
  Save Pickle
  """
  substrate_config.save_network_config(network_config)


if __name__ == "__main__":
    main()