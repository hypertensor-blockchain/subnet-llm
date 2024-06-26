from substrateinterface import SubstrateInterface, Keypair, ExtrinsicReceipt
from substrateinterface.exceptions import SubstrateRequestException
from tenacity import retry, stop_after_attempt, wait_exponential
# from petals.substrate.utils import save_last_submit_consensus_block, save_last_unconfirm_consensus_block

def submit_consensus_data(
  substrate: SubstrateInterface,
  keypair: Keypair,
  block: int,
  model_id: int,
  consensus_data
):
  """
  Submit consensus data on each epoch with no conditionals

  It is up to prior functions to decide whether to call this function

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  :param consensus_data: an array of data containing all AccountIds, PeerIds, and scores per model hoster

  Note: It's important before calling this to ensure the entrinsic will be successful.
        If the function reverts, the extrinsic is Pays::Yes
  """
  print("submitting consensus data...")

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

  """
  submit extrinsic (this is gasless unless it reverts)
  This will retry up to 4 times when except is returned
  """
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

def unconfirm_consensus_data(
  substrate: SubstrateInterface,
  keypair: Keypair,
  block: int,
  model_id: int,
):
  """
  Submit consensus data on each epoch with no conditionals

  It is up to prior functions to decide whether to call this function

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  :param consensus_data: an array of data containing all AccountIds, PeerIds, and scores per model hoster

  Note: It's important before calling this to ensure the entrinsic will be successful.
        If the function reverts, the extrinsic is Pays::Yes
  """

  # compose call
  call = substrate.compose_call(
    call_module='Network',
    call_function='unconfirm_consensus_data',
    call_params={
      'model_id': model_id,
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

  """
  submit extrinsic (this is gasless unless it reverts)
  This will retry up to 4 times when except is returned
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def submit_extrinsic():
    try:
      receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
      if receipt.is_success:
        # save_last_unconfirm_consensus_block(block)
        print('✅ Success, triggered events:')
        for event in receipt.triggered_events:
          print(f'* {event.value}')
      else:
        print('⚠️ Extrinsic Failed: ', receipt.error_message)
      return receipt
    except SubstrateRequestException as e:
      print("Failed to send: {}".format(e))

  return submit_extrinsic()

def add_model(
  substrate: SubstrateInterface,
  keypair: Keypair,
  model_path: str,
) -> ExtrinsicReceipt:
  """
  Add model validator as model peer to blockchain storage

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  """

  # compose call
  call = substrate.compose_call(
    call_module='Network',
    call_function='add_model',
    call_params={
      'model_path': model_path,
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

"""Not implemented yet"""
def vote_model_peer_dishonest(
  substrate: SubstrateInterface,
  keypair: Keypair,
  model_id: int,
  peer_id: str,
):
  """
  Vote a model peer dishonest to the blockchain

  In production this call will trigger an event subscription to all other peers
  interfaced with Hypertensor. They will then run a check on the peer to ensure
  their by acting as a client and running an input to get the expected hash back.
  If enough peers vote this peer as dishonest, they will be added to the blacklist
  and removed from the blockchains storage.

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  :param model_id: model ID
  :param peer_id: peer ID of the dishonest peer

  Note: It's important before calling this to ensure the entrinsic will be successful.
        If the function reverts, the extrinsic is Pays::Yes
  """
  call = substrate.compose_call(
    call_module='Network',
    call_function='vote_model_peer_dishonest',
    call_params={
      'model_id': model_id,
      'peer_id': peer_id
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

  """
  submit extrinsic (this is gasless unless it reverts)
  This will retry up to 4 times when except is returned
  """
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

def get_model_peers(
  substrate: SubstrateInterface,
  model_id: int,
):
  """
  Function to return all account_ids and peer_ids from the substrate Hypertensor Blockchain

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: model_peers_data
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_rpc_request():
    try:
      model_peers_data = substrate.rpc_request(
        method='network_getModelPeers',
        params=[
          model_id
        ]
      )
      return model_peers_data
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_rpc_request()

def get_model_peers_included(
  substrate: SubstrateInterface,
  model_id: int,
):
  """
  Function to return all account_ids and peer_ids from the substrate Hypertensor Blockchain

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: model_peers_data
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_rpc_request():
    try:
      model_peers_data = substrate.rpc_request(
        method='network_getModelPeersIncluded',
        params=[
          model_id
        ]
      )
      return model_peers_data
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_rpc_request()

def get_model_peers_submittable(
  substrate: SubstrateInterface,
  model_id: int,
):
  """
  Function to return all account_ids and peer_ids from the substrate Hypertensor Blockchain

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: model_peers_data
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_rpc_request():
    try:
      model_peers_data = substrate.rpc_request(
        method='network_getModelPeersSubmittable',
        params=[
          model_id
        ]
      )
      return model_peers_data
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_rpc_request()

async def get_model_peers_model_unconfirmed_count(
  substrate: SubstrateInterface,
  model_id: int,
):
  """
  Function to return all account_ids and peer_ids from the substrate Hypertensor Blockchain

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: model_peers_data
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_rpc_request():
    try:
      model_peers_data = substrate.rpc_request(
        method='network_getModelPeersModelUnconfirmedCount',
        params=[
          model_id
        ]
      )
      return model_peers_data
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_rpc_request()

def add_model_peer(
  substrate: SubstrateInterface,
  keypair: Keypair,
  model_id: int,
  peer_id: str,
  ip: str,
  port: int,
  stake_to_be_added: int,
) -> ExtrinsicReceipt:
  """
  Add model validator as model peer to blockchain storage

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  """

  # compose call
  call = substrate.compose_call(
    call_module='Network',
    call_function='add_model_peer',
    call_params={
      'model_id': model_id,
      'peer_id': peer_id,
      'ip': ip,
      'port': port,
      'stake_to_be_added': stake_to_be_added,
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
        # for event in receipt.triggered_events:
        #   print(f'* {event.value}')
      else:
        print('⚠️ Extrinsic Failed: ', receipt.error_message)
      return receipt
    except SubstrateRequestException as e:
      print("Failed to send: {}".format(e))

  return submit_extrinsic()

def update_model_peer(
  substrate: SubstrateInterface,
  keypair: Keypair,
  model_id: int,
  peer_id: str,
) -> ExtrinsicReceipt:
  """
  Update model validator as model peer to blockchain storage
  Can only update the peer_id in this function
  To update port, us `update_port()`

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  :param model_id: model ID
  :param peer_id: new peer_id
  """

  # compose call
  call = substrate.compose_call(
    call_module='Network',
    call_function='update_model_peer',
    call_params={
      'model_id': model_id,
      'peer_id': peer_id,
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
      else:
        print('⚠️ Extrinsic Failed: ', receipt.error_message)
      return receipt
    except SubstrateRequestException as e:
      print("Failed to send: {}".format(e))

  return submit_extrinsic()

def remove_model_peer(
  substrate: SubstrateInterface,
  keypair: Keypair,
  model_id: int,
):
  """
  Remove stake balance towards specified model

  Amount must be less than allowed amount that won't allow stake balance to be lower than
  the required minimum balance

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  """

  # compose call
  call = substrate.compose_call(
    call_module='Network',
    call_function='remove_model_peer',
    call_params={
      'model_id': model_id,
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

def update_port(
  substrate: SubstrateInterface,
  keypair: Keypair,
  model_id: int,
  port: int,
):
  """
  Add model validator as model peer to blockchain storage

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  :param port: updated port
  """

  # compose call
  call = substrate.compose_call(
    call_module='Network',
    call_function='update_port',
    call_params={
      'model_id': model_id,
      'port': port,
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

def add_to_stake(
  substrate: SubstrateInterface,
  keypair: Keypair,
  model_id: int,
  stake_to_be_added: int,
):
  """
  Add model validator as model peer to blockchain storage

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  :param stake_to_be_added: stake to be added towards model
  """

  # compose call
  call = substrate.compose_call(
    call_module='Network',
    call_function='add_to_stake',
    call_params={
      'model_id': model_id,
      'stake_to_be_added': stake_to_be_added,
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

def remove_stake(
  substrate: SubstrateInterface,
  keypair: Keypair,
  model_id: int,
  stake_to_be_removed: int,
):
  """
  Remove stake balance towards specified model

  Amount must be less than allowed amount that won't allow stake balance to be lower than
  the required minimum balance

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  :param stake_to_be_removed: stake to be removed from model
  """

  # compose call
  call = substrate.compose_call(
    call_module='Network',
    call_function='add_to_stake',
    call_params={
      'model_id': model_id,
      'stake_to_be_removed': stake_to_be_removed,
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

def get_balance(
  substrate: SubstrateInterface,
  address: str
):
  """
  Function to return account balance

  :param SubstrateInterface: substrate interface from blockchain url
  :param address: address of account_id
  :returns: account balance
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('System', 'Account', [address])
      return result.value['data']['free']
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_model_stake_balance(
  substrate: SubstrateInterface,
  model_id: int,
  address: str
):
  """
  Function to return an accounts stake balance towards a model

  :param SubstrateInterface: substrate interface from blockchain url
  :param address: address of account_id
  :returns: account stake balance towards model
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'AccountModelStake', [model_id, address])
      return result.value['data']
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_model_peer_account(
  substrate: SubstrateInterface,
  model_id: int,
  peer_id: str
):
  """
  Function to account_id of model hosting peer

  :param SubstrateInterface: substrate interface from blockchain url
  :param peer_id: peer_id of model validator
  :returns: account_id of model_id => peer_id
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'ModelPeerAccount', [model_id, peer_id])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_model_accounts(
  substrate: SubstrateInterface,
  model_id: int,
):
  """
  Function to account_id of model hosting peer

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: account_id's of model_id
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'ModelAccount', [model_id])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_model_path_id(
  substrate: SubstrateInterface,
  path: str
):
  """
  Function to get account_id of model hosting peer

  :param SubstrateInterface: substrate interface from blockchain url
  :param path: path of model
  :returns: model_id
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'ModelPaths', [path])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_model_data(
  substrate: SubstrateInterface,
  id: int
):
  """
  Function to get data struct of the model

  :param SubstrateInterface: substrate interface from blockchain url
  :param id: id of model
  :returns: model_id
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'ModelsData', [id])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_max_models(substrate: SubstrateInterface):
  """
  Function to get the maximum number of models allowed on the blockchain

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: max_models
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'MaxModels')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_min_model_peers(substrate: SubstrateInterface):
  """
  Function to get the minimum number of peers required to host a model

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: min_model_peers
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'MinModelPeers')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_max_model_peers(substrate: SubstrateInterface):
  """
  Function to get the maximum number of peers allowed to host a model

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: max_model_peers
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'MaxModelPeers')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_min_stake_balance(substrate: SubstrateInterface):
  """
  Function to get the minimum stake balance required to host a model
  
  :param SubstrateInterface: substrate interface from blockchain url
  :returns: min_stake_balance
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'MinStakeBalance')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_tx_rate_limit(substrate: SubstrateInterface):
  """
  Function to get the transaction rate limit

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: tx_rate_limit
  """
  
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'TxRateLimit')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_max_model_consensus_epochs(substrate: SubstrateInterface):
  """
  Function to get the maximum number of epochs allowed for model consensus

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: max_model_consensus_epochs
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'MaxModelConsensusEpochsErrors')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_min_required_model_consensus_submit_epochs(substrate: SubstrateInterface):
  """
  Function to get the minimum number of epochs required to submit model consensus

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: min_required_model_consensus_submit_epochs
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'MinRequiredModelConsensusSubmitEpochs')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_min_required_peer_consensus_submit_epochs(substrate: SubstrateInterface):
  """
  Function to get the minimum number of epochs required to submit peer consensus

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: min_required_peer_consensus_submit_epochs
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'MinRequiredPeerConsensusSubmitEpochs')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_min_required_peer_consensus_inclusion_epochs(substrate: SubstrateInterface):
  """
  Function to get the minimum number of epochs required to include peer consensus

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: min_required_peer_consensus_inclusion_epochs
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'MinRequiredPeerConsensusInclusionEpochs')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_maximum_outlier_delta_percent(substrate: SubstrateInterface):
  """
  Function to get the maximum outlier delta percent

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: maximum_outlier_delta_percent
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'MaximumOutlierDeltaPercent')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_remove_model_peer_epoch_percentage(substrate: SubstrateInterface):
  """
  Function to get the remove model peer epoch percentage

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: remove_model_peer_epoch_percentage
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'RemoveModelPeerEpochPercentage')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_consensus_blocks_interval(substrate: SubstrateInterface):
  """
  Function to get the consensus blocks interval

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: consensus_blocks_interval
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'ConsensusBlocksInterval')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()
