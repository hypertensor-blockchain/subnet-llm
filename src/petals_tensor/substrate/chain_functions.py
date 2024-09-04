from substrateinterface import SubstrateInterface, Keypair, ExtrinsicReceipt
from substrateinterface.exceptions import SubstrateRequestException
from tenacity import retry, stop_after_attempt, wait_exponential
# from petals.substrate.utils import save_last_submit_consensus_block, save_last_unconfirm_consensus_block

def validate(
  substrate: SubstrateInterface,
  keypair: Keypair,
  subnet_id: int,
  data
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
    call_function='validate',
    call_params={
      'subnet_id': subnet_id,
      'data': data
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

  """
  submit extrinsic
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

def attest(
  substrate: SubstrateInterface,
  keypair: Keypair,
  subnet_id: int
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
    call_function='attest',
    call_params={
      'subnet_id': subnet_id,
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

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

def submit_consensus_data(
  substrate: SubstrateInterface,
  keypair: Keypair,
  block: int,
  subnet_id: int,
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
      'subnet_id': subnet_id,
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
  subnet_id: int,
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
      'subnet_id': subnet_id,
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

def remove_subnet(
  substrate: SubstrateInterface,
  keypair: Keypair,
  subnet_id: str,
) -> ExtrinsicReceipt:
  """
  Add model validator as model peer to blockchain storage

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  """

  # compose call
  call = substrate.compose_call(
    call_module='Network',
    call_function='remove_subnet',
    call_params={
      'subnet_id': subnet_id,
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

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
  subnet_id: int,
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
  :param subnet_id: model ID
  :param peer_id: peer ID of the dishonest peer

  Note: It's important before calling this to ensure the entrinsic will be successful.
        If the function reverts, the extrinsic is Pays::Yes
  """
  call = substrate.compose_call(
    call_module='Network',
    call_function='vote_model_peer_dishonest',
    call_params={
      'subnet_id': subnet_id,
      'peer_id': peer_id
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

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
  subnet_id: int,
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
        method='network_getSubnetNodes',
        params=[
          subnet_id
        ]
      )
      return model_peers_data
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_rpc_request()

def get_model_peers_included(
  substrate: SubstrateInterface,
  subnet_id: int,
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
        method='network_getSubnetNodesIncluded',
        params=[subnet_id]
      )
      return model_peers_data
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_rpc_request()

def get_model_peers_submittable(
  substrate: SubstrateInterface,
  subnet_id: int,
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
        method='network_getSubnetNodesSubmittable',
        params=[
          subnet_id
        ]
      )
      return model_peers_data
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_rpc_request()

async def get_model_peers_model_unconfirmed_count(
  substrate: SubstrateInterface,
  subnet_id: int,
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
        method='network_getSubnetNodesUnconfirmedCount',
        params=[
          subnet_id
        ]
      )
      return model_peers_data
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_rpc_request()

async def get_consensus_data(
  substrate: SubstrateInterface,
  subnet_id: int,
  epoch: int
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
        method='network_getConsensusData',
        params=[
          subnet_id,
          epoch
        ]
      )
      return model_peers_data
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_rpc_request()

async def get_accountant_data(
  substrate: SubstrateInterface,
  subnet_id: int,
  id: int
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
        method='network_getAccountantData',
        params=[
          subnet_id,
          id
        ]
      )
      return model_peers_data
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_rpc_request()

def add_subnet_node(
  substrate: SubstrateInterface,
  keypair: Keypair,
  subnet_id: int,
  peer_id: str,
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
    call_function='add_subnet_node',
    call_params={
      'subnet_id': subnet_id,
      'peer_id': peer_id,
      'stake_to_be_added': stake_to_be_added,
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

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
  subnet_id: int,
  peer_id: str,
) -> ExtrinsicReceipt:
  """
  Update model validator as model peer to blockchain storage
  Can only update the peer_id in this function
  To update port, us `update_port()`

  :param substrate: interface to blockchain
  :param keypair: keypair of extrinsic caller. Must be a peer in the model
  :param subnet_id: model ID
  :param peer_id: new peer_id
  """

  # compose call
  call = substrate.compose_call(
    call_module='Network',
    call_function='update_model_peer',
    call_params={
      'subnet_id': subnet_id,
      'peer_id': peer_id,
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

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

def remove_subnet_node(
  substrate: SubstrateInterface,
  keypair: Keypair,
  subnet_id: int,
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
    call_function='remove_subnet_node',
    call_params={
      'subnet_id': subnet_id,
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

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
  subnet_id: int,
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
      'subnet_id': subnet_id,
      'port': port,
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

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
  subnet_id: int,
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
      'subnet_id': subnet_id,
      'stake_to_be_added': stake_to_be_added,
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

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
  subnet_id: int,
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
    call_function='remove_stake',
    call_params={
      'subnet_id': subnet_id,
      'stake_to_be_removed': stake_to_be_removed,
    }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

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
  subnet_id: int,
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
      result = substrate.query('Network', 'AccountSubnetStake', [address, subnet_id])
      print("get_model_stake_balance: ", result)
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_model_peer_account(
  substrate: SubstrateInterface,
  subnet_id: int,
  peer_id: str
):
  """
  Function to account_id of model hosting peer

  :param SubstrateInterface: substrate interface from blockchain url
  :param peer_id: peer_id of model validator
  :returns: account_id of subnet_id => peer_id
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'SubnetNodeAccount', [subnet_id, peer_id])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_model_accounts(
  substrate: SubstrateInterface,
  subnet_id: int,
):
  """
  Function to account_id of model hosting peer

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: account_id's of subnet_id
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'SubnetAccount', [subnet_id])
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
  :returns: subnet_id
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'SubnetPaths', [path])
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
  :returns: subnet_id
  """
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'SubnetsData', [id])
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
      result = substrate.query('Network', 'MaxSubnets')
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
      result = substrate.query('Network', 'MinSubnetNodes')
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
      result = substrate.query('Network', 'MaxSubnetNodes')
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

# def get_max_model_consensus_epochs(substrate: SubstrateInterface):
#   """
#   Function to get the maximum number of epochs allowed for model consensus

#   :param SubstrateInterface: substrate interface from blockchain url
#   :returns: max_model_consensus_epochs
#   """

#   @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
#   def make_query():
#     try:
#       result = substrate.query('Network', 'MaxSubnetConsensusEpochsErrors')
#       return result
#     except SubstrateRequestException as e:
#       print("Failed to get rpc request: {}".format(e))

#   return make_query()

def get_min_required_model_consensus_submit_epochs(substrate: SubstrateInterface):
  """
  Function to get the minimum number of epochs required to submit model consensus

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: min_required_model_consensus_submit_epochs
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'MinRequiredSubnetConsensusSubmitEpochs')
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
      result = substrate.query('Network', 'SubnetNodeClassEpochs', ['Submittable'])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

# def get_min_required_peer_consensus_submit_epochs(substrate: SubstrateInterface):
#   """
#   Function to get the minimum number of epochs required to submit peer consensus

#   :param SubstrateInterface: substrate interface from blockchain url
#   :returns: min_required_peer_consensus_submit_epochs
#   """

#   @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
#   def make_query():
#     try:
#       result = substrate.query('Network', 'MinRequiredPeerConsensusSubmitEpochs')
#       return result
#     except SubstrateRequestException as e:
#       print("Failed to get rpc request: {}".format(e))

#   return make_query()

def get_min_required_peer_consensus_inclusion_epochs(substrate: SubstrateInterface):
  """
  Function to get the minimum number of epochs required to include peer consensus

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: min_required_peer_consensus_inclusion_epochs
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'SubnetNodeClassEpochs', ['Included'])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_idles(substrate: SubstrateInterface, subnet_id: int):
  """
  Get list of all accounts eligible for consensus inclusion

  :param SubstrateInterface: substrate interface from blockchain url
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'SubnetNodesClasses', [subnet_id, 'Idle'])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_included(substrate: SubstrateInterface, subnet_id: int):
  """
  Get list of all accounts eligible for consensus inclusion

  :param SubstrateInterface: substrate interface from blockchain url
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'SubnetNodesClasses', [subnet_id, 'Included'])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_submittables(substrate: SubstrateInterface, subnet_id: int):
  print('get_submittables')
  """
  Get list of all accounts eligible for consensus submissions

  :param SubstrateInterface: substrate interface from blockchain url
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'SubnetNodesClasses', [subnet_id, 'Submittable'])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_accountants(substrate: SubstrateInterface, subnet_id: int):
  """
  Get list of all accounts eligible for accountant submissions

  :param SubstrateInterface: substrate interface from blockchain url
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'SubnetNodesClasses', [subnet_id, 'Accountant'])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

# def get_min_required_peer_consensus_inclusion_epochs(substrate: SubstrateInterface):
#   """
#   Function to get the minimum number of epochs required to include peer consensus

#   :param SubstrateInterface: substrate interface from blockchain url
#   :returns: min_required_peer_consensus_inclusion_epochs
#   """

#   @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
#   def make_query():
#     try:
#       result = substrate.query('Network', 'MinRequiredPeerConsensusInclusionEpochs')
#       return result
#     except SubstrateRequestException as e:
#       print("Failed to get rpc request: {}".format(e))

#   return make_query()

# def get_maximum_outlier_delta_percent(substrate: SubstrateInterface):
#   """
#   Function to get the maximum outlier delta percent

#   :param SubstrateInterface: substrate interface from blockchain url
#   :returns: maximum_outlier_delta_percent
#   """

#   @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
#   def make_query():
#     try:
#       result = substrate.query('Network', 'MaximumOutlierDeltaPercent')
#       return result
#     except SubstrateRequestException as e:
#       print("Failed to get rpc request: {}".format(e))

#   return make_query()

# def get_remove_model_peer_epoch_percentage(substrate: SubstrateInterface):
#   """
#   Function to get the remove model peer epoch percentage

#   :param SubstrateInterface: substrate interface from blockchain url
#   :returns: remove_model_peer_epoch_percentage
#   """

#   @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
#   def make_query():
#     try:
#       result = substrate.query('Network', 'RemoveSubnetNodeEpochPercentage')
#       return result
#     except SubstrateRequestException as e:
#       print("Failed to get rpc request: {}".format(e))

#   return make_query()

def get_model_activated(substrate: SubstrateInterface, path: str):
  """
  Function to get the maximum number of peers allowed to host a model

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: max_model_peers
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'SubnetActivated', [path])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_epoch_length(substrate: SubstrateInterface):
  """
  Function to get the epoch length as blocks per epoch

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: epoch_length
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.get_constant('Network', 'EpochLength')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_rewards_validator(
  substrate: SubstrateInterface,
  subnet_id: int,
  epoch: int
):
  """
  Function to get the consensus blocks interval

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: epoch_length
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'SubnetRewardsValidator', [subnet_id, epoch])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_rewards_submission(
  substrate: SubstrateInterface,
  subnet_id: int,
  epoch: int
):
  """
  Function to get the consensus blocks interval

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: epoch_length
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('Network', 'SubnetRewardsSubmission', [subnet_id, epoch])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()


"""
Subnet Democracy
"""
def propose(
  substrate: SubstrateInterface,
  keypair: Keypair,
  subnet_data,
  subnet_nodes,
  proposal_type: str
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
    call_module='SubnetDemocracy',
    call_function='propose',
    call_params={
      'subnet_data': subnet_data,
      'subnet_nodes': subnet_nodes,
      'proposal_type': proposal_type,    
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

def cast_vote(
  substrate: SubstrateInterface,
  keypair: Keypair,
  proposal_index: int,
  vote_amount: int,
  vote: int
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
    call_module='SubnetDemocracy',
    call_function='cast_vote',
    call_params={
      'proposal_index': proposal_index,
      'vote_amount': vote_amount,
      'vote': vote
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

def execute_proposal(
  substrate: SubstrateInterface,
  keypair: Keypair,
  proposal_index: int,
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
    call_module='SubnetDemocracy',
    call_function='execute',
    call_params={ 'proposal_index': proposal_index }
  )

  # create signed extrinsic
  extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

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

def get_subnet_proposal(substrate: SubstrateInterface, proposal_id: int):
  """
  Function to get the maximum number of peers allowed to host a model

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: max_model_peers
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('SubnetDemocracy', 'Proposals', [proposal_id])
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()

def get_subnet_proposals_count(substrate: SubstrateInterface):
  """
  Function to get the maximum number of peers allowed to host a model

  :param SubstrateInterface: substrate interface from blockchain url
  :returns: max_model_peers
  """

  @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(4))
  def make_query():
    try:
      result = substrate.query('SubnetDemocracy', 'PropCount')
      return result
    except SubstrateRequestException as e:
      print("Failed to get rpc request: {}".format(e))

  return make_query()
