import itertools
import random
import threading
from typing import Dict, List, Optional
import dataclasses
import time
import multiprocessing as mp

# from petals_tensor.substrate.config import load_subnet_config
from petals_tensor.validator.config import AccountantData, AccountantDataPeerParams, PeerInferenceResults, PeerInferenceSequenceData, PeerValidationData
from petals_tensor.validator.routing.sequence_manager import MissingBlocksError
from petals_tensor.data_structures import RemoteSpanInfo
from petals_tensor.health.state_updater import get_peers_data_list
# from petals_tensor.substrate.chain_functions import propose_model_peer_dishonest, vote_model_peer_dishonest
from petals_tensor.utils.auto_config import AutoDistributedModelForCausalLMValidator
# from petals_tensor.substrate import config as substrate_config

from transformers import AutoTokenizer
# import numpy as np
import torch
from hivemind.utils.logging import get_logger
from hivemind import PeerID

import pprint 

logger = get_logger(__name__)

# TODO: make substrate_config a class
# from hypertensor import HypertensorClient

"""Timespan per inference validation per peer"""
TIMESPAN_PER_PEER = 300
STRICT_BLOCK_WAIT = 300
MODULE_CONTAINER_WAIT = 90

"""Inference configuration"""

# DO NOT change these. All accountants must have the same inference validation configuration
RTOL = 1e-03 # relative
ATOL = 8e-01 # absolute

VTOL = 0.8 # valid tolerance of each peers position in the sequence, this is a percentage of each positions validity

class InferenceValidator(threading.Thread):
    """
    Runs Inference validation logic, runs per epoch,
    called by Server to start processing before ModuleContainers load, 
    inherits Server reference to update variables in the Server,
    and updates the server's state.
    """

    def __init__(self, server, model_name, num_model_blocks: int, my_peer_id: str, num_blocks: int, start: bool):
        super().__init__()
        self.server = server
        self.model = AutoDistributedModelForCausalLMValidator.from_pretrained(model_name)
        # self.client = substrate_config.SubstrateConfig
        self.peers_data = None
        self.peers_data_to_validate = None
        self.validated_peer_ids = None
        # If peers preceding in the sequence are not valid, everyone after them will be invalid
        # We will need to rerun the sequence and recheck
        self.revalidate_peer_ids = None
        self.last_timestamp = 0
        self.my_peer_id = my_peer_id
        self.model_name = model_name
        self.num_blocks = num_blocks
        self.num_model_blocks = num_model_blocks
        self.ranges = list(itertools.combinations(range(0,num_model_blocks+1), 2))

        self.my_inference_sequence_cache = None

        # Is this epochs accountant required to submit data
        self.is_accountant = False
        self.accountant_data = AccountantData()

        # model_config = load_subnet_config()
        # self.model_id = model_config.id
        self.model_id = None


        # TODO: Get blacklisted peers to automatically create a dishonesty proposal for them


        # epoch represents the time it takes to validate each peer they are designated to validdate inference
        # TODO: Make universal for each accountant to pull from the same storage backend
        self.epoch = 0

        # tokenizer = AutoTokenizer.from_pretrained(model_name)
        # self.input_data = tokenizer("A cat sat", return_tensors="pt")["input_ids"]
        self.input_data = "A cat sat"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        # self.input_tensor = self.tokenizer(self.input_data, return_tensors="pt")["input_ids"]

        if start:
            self.run_in_background(await_ready=True)

        self.stop = threading.Event()

    # def run2(self):
    #     while True:
    #         # Begin epoch 
    #         epoch = self._get_epoch()

    #         # Reset accountant data for the new epoch
    #         self.accountant_data.reset()

    #         # Ensure that module container is created
    #         logger.info(f"Verifying validator blocks have begun")
    #         if self.server.module_container is None:
    #             # Restart loop
    #             logger.info("Module container not loaded yet")
    #             time.sleep(30)
    #             continue

    #         # Ensure that module container is initialized
    #         logger.info(f"Verifying validator blocks are healthy")
    #         if not self.server.module_container.is_healthy():
    #             # Restart loop
    #             logger.info("Module container not healthy yet")
    #             time.sleep(30)
    #             continue

    #         try:
    #             """Set as validator for full control over blocks"""
    #             # In prod, ensure peer CAN be an accountant by checking blockchain status
    #             logger.info("Setting status to validator")
    #             self.server.is_validator = True

    #             while True:
    #                 # Updating peers per epoch
    #                 # We block updating peers if already updated here
    #                 # In prod this will check timestamps and epochs
    #                 if self.epoch == 0 and self.peers_data_to_validate is None:
    #                     # Restart loop
    #                     logger.info("Updating peers within the epoch")
    #                     self.update_peers()
                    
    #                 # This is in the while True because in case peer_data is None
    #                 if self.peers_data_to_validate is None:
    #                     # Restart loop
    #                     logger.info("peers_data is None, sleeping for 30s and trying again")
    #                     time.sleep(30)
    #                     continue

    #                 """Get each peer matchig the range of blocks"""
    #                 logger.info("Retrieving peers to validate")
    #                 for range in self.ranges:
    #                     span_start = range[0]
    #                     span_end = range[1]

    #                     # Get peers data in this range
    #                     peers_data = self._get_peers_data_in_range(span_start, span_end)
    #                     peers_len = len(peers_data)

    #                     if peers_len == 0:
    #                         # Move onto next range
    #                         continue

    #                     print(span_start, span_end)

    #                     logger.info(f"Found {peers_len} peers to validate with span {span_start}:{span_end}")

    #                     # Update up to validators max blocks
    #                     if span_end - span_start > self.num_blocks:
    #                         logger.info(f"Peer blocks are greater than validator blocks of {self.num_blocks}, updating sequence to match max validator span")
    #                         span_end = span_start + self.num_blocks
    #                         # span_start = span_end - self.num_blocks

    #                     block_indices = f"{span_start}:{span_end}"

    #                     # Update validator block spans
    #                     logger.info(f"Updating validator blocks to {block_indices} if needed".format())
    #                     self.server.update_strict_block_indices(block_indices)

    #                     while True:
    #                         # Do something pythonic than just sleep
    #                         time.sleep(30)

    #                         # Wait for new blocks to be healthy
    #                         logger.info(f"Verifying validator blocks have begun")
    #                         if self.server.module_container is None:
    #                             # Restart loop
    #                             logger.info("Module container not loaded yet")
    #                             time.sleep(MODULE_CONTAINER_WAIT)
    #                             continue

    #                         # start_block = self.server.server_info.start_block
    #                         # end_block = self.server.server_info.end_block
    #                         start_block = self.server.module_container.server_info.start_block
    #                         end_block = self.server.module_container.server_info.end_block

    #                         print("validator current start block", start_block)
    #                         print("validator current end   block", end_block)

    #                         if start_block != span_start and end_block != span_end:
    #                             logger.info("Blocks don't match yet")
    #                             time.sleep(MODULE_CONTAINER_WAIT)
    #                             continue

    #                         # Example: Wait until blocks are updated
    #                         # This is a hack attempt - need to instead check for that blocks have been updated to the correct spans
    #                         logger.info(f"Verifying validator blocks are healthy")

    #                         if not self.server.module_container.is_healthy():
    #                             # Restart loop
    #                             logger.info("Module container not healthy yet")
    #                             time.sleep(MODULE_CONTAINER_WAIT)
    #                             continue

    #                         # Run inference on expected block spans to get expected output
    #                         logger.info(f"Running inference as validator for expected output")
    #                         output = self.run_inference(
    #                             self.input_data, 
    #                             span_start,
    #                             span_end,
    #                             peer_id=self.my_peer_id
    #                         )

    #                         """Do something here to reset"""
    #                         if output is None:
    #                             logger.error("Error running inference, retrying...")
    #                             # If there is an error, the peers that broke the inference sequence will be blacklisted
    #                             # Try again
    #                             time.sleep(12)
    #                             continue

    #                         logger.info(f"Successfully ran inference as validator for expected output")
    #                         break

    #                     # TODO: Get multiple peers in one generate() call instead of per peer
    #                     #       if able to validate inference between multiple peers at once
    #                     #       i.e. if validator has 18 blocks and 2 peers each have 9 blocks
    #                     #            equalling 18, validate in one generate() call

    #                     # Iterate each peer and validate inference
    #                     logger.info(f"Beginning inference validation on peers within range")
    #                     for peer_data in peers_data:
    #                         time.sleep(30)

    #                         peer_id = peer_data['peer_id']
    #                         logger.info(f"peer_data in peers_data {peer_id}")

    #                         # Add peer to be in sequence to check blocks spans
    #                         peers = [{
    #                             'peer_id':peer_id,
    #                             'start':span_start,
    #                             'end':span_end,
    #                         }]

    #                         # Run inference on peer and check if output is expected
    #                         logger.info(f"Validating inference on {peer_id} with indices {block_indices}")
    #                         valid = self.validate_inference(
    #                             self.input_data,
    #                             span_start,
    #                             span_end,
    #                             output, 
    #                             peer_id,
    #                             peers
    #                         )

    #                         # If not valid, propose or vote dishonesty
    #                         if valid == False:
    #                             logger.info(f"Inference is not valid for {peer_id}")
    #                             self.initiate_dishonesty(peer_id)
    #                         else:
    #                             logger.info(f"Inference is valid for {peer_id}")

    #                 # `break` once all peers are checked and wait until next epoch to start again
    #                 logger.info(f"Inference validation on epoch {self.epoch} completed successfully")
    #                 break
    #         except Exception as e:
    #             print("Error here 123", e)
    #         finally:
    #             self.server.remove_strict_block_indices()
    #             self.server.is_validator = False
    #             seconds_remaining_in_epoch = self._get_seconds_remaining_in_epoch()
    #             logger.info(f"Next epoch is {seconds_remaining_in_epoch} seconds away, sleeping for remaining time")
    #             time.sleep(seconds_remaining_in_epoch)

    # def run3(self):
    #     while True:
    #         # Begin epoch 
    #         epoch = self._get_epoch()

    #         # Reset accountant data for the new epoch
    #         self.accountant_data.reset()

    #         # Ensure that module container is created
    #         logger.info(f"Verifying validator blocks have begun")
    #         if self.server.module_container is None:
    #             # Restart loop
    #             logger.info("Module container not loaded yet")
    #             time.sleep(30)
    #             continue

    #         # Ensure that module container is initialized
    #         logger.info(f"Verifying validator blocks are healthy")
    #         if not self.server.module_container.is_healthy():
    #             # Restart loop
    #             logger.info("Module container not healthy yet")
    #             time.sleep(30)
    #             continue

    #         try:
    #             """Set as validator for full control over blocks"""
    #             # In prod, ensure peer CAN be an accountant by checking blockchain status
    #             logger.info("Setting status to validator")
    #             self.server.is_validator = True

                    
    #             logger.info("Getting all ranges for Accountant")
    #             spans = []
    #             for index, value in enumerate(range(0, self.num_blocks+self.num_blocks-0, self.num_blocks)):
    #                 spans.append([value, value + self.num_blocks])

    #             print("spans", spans)                        

    #             for span in spans:
    #                 # Run sequence as Accountant for every span to cover full layer

    #                 span_start = span[0]
    #                 span_end = span[1]

    #                 block_indices = f"{span_start}:{span_end}"

    #                 self.server.update_strict_block_indices(block_indices)

    #                 while True:
    #                     logger.info(f"Verifying validator blocks have begun")
    #                     if self.server.module_container is None:
    #                         # Restart loop
    #                         logger.info("Module container not loaded yet")
    #                         time.sleep(MODULE_CONTAINER_WAIT)
    #                         continue

    #                     start_block = self.server.module_container.server_info.start_block
    #                     end_block = self.server.module_container.server_info.end_block

    #                     if start_block != span_start and end_block != span_end:
    #                         logger.info("Blocks don't match yet")
    #                         time.sleep(MODULE_CONTAINER_WAIT)
    #                         continue

    #                     # Example: Wait until blocks are updated
    #                     # This is a hack attempt - need to instead check for that blocks have been updated to the correct spans
    #                     logger.info(f"Verifying validator blocks are healthy")
    #                     if not self.server.module_container.is_healthy():
    #                         # Restart loop
    #                         logger.info("Module container not healthy yet")
    #                         time.sleep(MODULE_CONTAINER_WAIT)
    #                         continue

    #                     logger.info(f"Getting all peer spans")
    #                     peer_spans = []
    #                     for index, value in enumerate(range(0, self.num_blocks, 2)):
    #                         if index == 0:
    #                             peer_spans.append({
    #                                 'peer_id':self.my_peer_id,
    #                                 'start':value,
    #                                 'end':value + 1,
    #                             })
    #                         else:
    #                             peer_spans.append({
    #                                 'peer_id':self.my_peer_id,
    #                                 'start':value-index,
    #                                 'end':value-index + 1,
    #                             })

    #                     print("peer_spans", peer_spans)                        
    #                     logger.info(f"Running inference as an Accountant on block indices {block_indices}")
    #                     self.run_inference_as_accountant(
    #                         self.input_data, 
    #                         peers=peer_spans
    #                     )

    #                     break     

    #             # Begin injecting peers into layer to verify inference 
    #             # No peers can be back to back to not possibly disrupt the next peers output
    #             # if any of them are dishonest.




    #             # `break` once all peers are checked and wait until next epoch to start again
    #             logger.info(f"Inference validation on epoch {self.epoch} completed successfully")
    #             break
    #         except Exception as e:
    #             print("Error here 7899", e)
    #         finally:
    #             self.server.remove_strict_block_indices()
    #             self.server.is_validator = False
    #             seconds_remaining_in_epoch = self._get_seconds_remaining_in_epoch()
    #             logger.info(f"Next epoch is {seconds_remaining_in_epoch} seconds away, sleeping for remaining time")
    #             time.sleep(seconds_remaining_in_epoch)

    # def run2(self):
    #     """
    #         1. Find the least amount of blocks to validate
    #             - We find the lowest end block and the highest start block as the span to validate
    #             - Accountant always starts at 0 though instead of the lowest end block until future iterations
    #         2. Run inference on the least amount of blocks starting at 0 up to the max block using Accountant only for inference sequence
    #             - This can take multiple iterations to complete
    #                 - e.g. If the accountant has 40/80 blocks and the max block is 80, it will take
    #                 2 iterations to complete
    #             - This sequence data is cached locally to use in validations in order to save on compute
    #               for the validating remote sequence runs including peers
    #             - By using only the Accountant in the sequence, the accountants data is assumed honest so others can not corrupt
    #               the sequence data
    #                 - This also allows other accountants to know for sure that another accountant is dishonest because the data they 
    #                   submit is always checked against their own
    #         3. Run inference of other peers to validate by injecting them inside the blocks using the cached data
    #             - Only the block(s) used to validate peers are used in the sequence for inference
    #             - The other blocks not selected for the sequence are not ran and the cached data is used in its place instead
    #         4. Validate accountant inference outputs from the first accountant-only runs versus the peers we validated
    #             - Validate by checking relative and absolute tolerances
    #         -  If chosen epoch-Accountant, submit all data of each peers data to the blockchain
    #         -  If an Accountant in general, and found a dishonest peer, submit a dishonesty proposal
    #     """
    #     while True:
    #         # Begin epoch 
    #         epoch = self._get_epoch()

    #         # Reset accountant data for the new epoch
    #         self.accountant_data.reset()

    #         # Ensure that module container is created
    #         logger.info(f"Verifying validator blocks have begun")
    #         if self.server.module_container is None:
    #             # Restart loop
    #             logger.info("Module container not loaded yet")
    #             time.sleep(30)
    #             continue

    #         # Ensure that module container is initialized
    #         logger.info(f"Verifying validator blocks are healthy")
    #         if not self.server.module_container.is_healthy():
    #             # Restart loop
    #             logger.info("Module container not healthy yet")
    #             time.sleep(30)
    #             continue

    #         try:
    #             logger.info("Setting status to validator")
    #             self.server.is_validator = True

    #             if self.epoch == 0 and self.peers_data_to_validate is None:
    #                 # Restart loop
    #                 logger.info("Updating peers within the epoch")
    #                 self.update_peers()

    #             # logger.info("Getting sequences of peers to validate")
    #             # validation_sequences = self.get_validation_sequences()
    #             # logger.info(f"Found {len(validation_sequences)} sequences")

    #             # print("validation_sequences ", validation_sequences)

    #             # Get max start block 
    #             logger.info(f"Getting min/max blocks for Accountant to get inference data of")
    #             # blocks = self.get_min_max_start_block_from_sequences(validation_sequences)
    #             blocks = self.get_min_max_start_block()

    #             min_block = 0
    #             max_block = blocks[1]
    #             print("min_block ", min_block)
    #             print("max_block ", max_block)
    #             print("num_blocks", self.num_blocks)

    #             logger.info("Getting all ranges for Accountant to run inference sequences")
    #             spans = []
    #             for index, value in enumerate(range(0, max_block+max_block-min_block, self.num_blocks)):
    #                 if index == 0:
    #                     spans.append([value, value + self.num_blocks])
    #                 else:
    #                     print(value + self.num_blocks)
    #                     if value + self.num_blocks > max_block:
    #                         if value + self.num_blocks - self.num_blocks != max_block:
    #                             spans.append([value + self.num_blocks - self.num_blocks, max_block])
    #                         break
    #                     else:
    #                         spans.append([value + self.num_blocks - self.num_blocks, value + self.num_blocks])

    #             print("spans", spans)   

    #             accountant_spans = []
    #             for span in spans:
    #                 start = span[0]
    #                 end = span[1]
    #                 print("start", start)   
    #                 print("end  ", end)   

    #                 accountant_span_ranges = []
    #                 for index, value in enumerate(range(start, end+end-start, 2)):
    #                     if index == 0:
    #                         # accountant_span_ranges.append([value, value + 1])
    #                         accountant_span_ranges.append({
    #                             'peer_id':self.my_peer_id,
    #                             'start':value,
    #                             'end':value + 1,
    #                         })
    #                     else:
    #                         # accountant_span_ranges.append([value-index, value-index + 1])
    #                         accountant_span_ranges.append({
    #                             'peer_id':self.my_peer_id,
    #                             'start':value-index,
    #                             'end':value-index + 1,
    #                         })

    #                 accountant_spans.append(accountant_span_ranges)

    #             print("accountant_spans", accountant_spans)

    #             logger.info("Running inference on accountant spans and storing inference results")
    #             for accountant_span in accountant_spans:
    #                 print("accountant_span", accountant_span)

    #                 span_start = accountant_span[0]["start"]
    #                 span_end = accountant_span[-1]["end"]

    #                 print("span_start", span_start)
    #                 print("span_end  ", span_end)

    #                 block_indices = f"{span_start}:{span_end}"
    #                 print("block_indices", block_indices)

    #                 logger.info(f"Updating strict blocks to {block_indices} if needed")
    #                 self.server.update_strict_block_indices(block_indices)
    #                 while True:
    #                     logger.info(f"Verifying validator blocks have begun")
    #                     if self.server.module_container is None:
    #                         # Restart loop
    #                         logger.info("Module container not loaded yet")
    #                         time.sleep(MODULE_CONTAINER_WAIT)
    #                         continue

    #                     # start_block = self.server.module_container.server_info.start_block
    #                     # end_block = self.server.module_container.server_info.end_block

    #                     range_overlap = self.server.do_strict_blocks_overlap()

    #                     # if start_block != span_start and end_block != span_end:
    #                     # If the range doesn't overlap, we then wait for strict blocks to update
    #                     if not range_overlap:
    #                         logger.info("Blocks don't match yet")
    #                         time.sleep(MODULE_CONTAINER_WAIT)
    #                         continue

    #                     # Example: Wait until blocks are updated
    #                     # This is a hack attempt - need to instead check for that blocks have been updated to the correct spans
    #                     logger.info(f"Verifying validator blocks are healthy")
    #                     if not self.server.module_container.is_healthy():
    #                         # Restart loop
    #                         logger.info("Module container not healthy yet")
    #                         time.sleep(MODULE_CONTAINER_WAIT)
    #                         continue
                        
    #                     logger.info(f"Running inference as an Accountant on block indices {block_indices} and storing results")
    #                     self.run_inference_as_accountant(
    #                         self.input_data, 
    #                         peers=accountant_span
    #                     )

    #                     break

    #             logger.info("Complete inference sequence as Accountant using self")
    #             ####

    #             logger.info(f"Building sequence of spans {block_indices}")
    #             for span in spans:
    #                 start = span[0]
    #                 end = span[1]

    #                 tensors = []
    #                 span_ranges = []
    #                 for x in range(start, end):
    #                     peer = self.get_peer_to_inject_in_sequence(x)
    #                     if peer is None:
    #                         # Get tensors from accountants cached state
    #                         input_tensors = self.get_account_input_tensors(x, x+1)
    #                         if input_tensors is not None:
    #                             print(f"number of input tensors: {len(input_tensors)}")
    #                             tensors.append(input_tensors)
    #                         else:
    #                             # Redundant
    #                             span_ranges.append({
    #                                 'peer_id': self.my_peer_id,
    #                                 'start':x,
    #                                 'end':x+1,
    #                             })
    #                     else:
    #                         span_ranges.append({
    #                             'peer_id':peer["peer_id"],
    #                             'start':x,
    #                             'end':x+1,
    #                         })

    #                 logger.info(f"Running inference with {len(tensors)} input tensors and {len(span_ranges)} peers")
    #                 self.run_inference_as_accountant(
    #                     self.input_data, 
    #                     peers=span_ranges,
    #                     input_tensor=tensors
    #                 )


    #         except Exception as e:
    #             print("Error 1551", e)
    #         finally:
    #             self.server.remove_strict_block_indices()
    #             self.server.is_validator = False
    #             seconds_remaining_in_epoch = self._get_seconds_remaining_in_epoch()
    #             logger.info(f"Next epoch is {seconds_remaining_in_epoch} seconds away, sleeping for remaining time")
    #             time.sleep(seconds_remaining_in_epoch)

    def run(self):
        """
            1. Find the least amount of blocks to validate
                - We find the lowest end block and the highest start block as the span to validate
                - Accountant always starts at 0 though instead of the lowest end block until future iterations
            2. Run inference on the least amount of blocks starting at 0 up to the max block using Accountant only for inference sequence
                - This can take multiple iterations to complete
                    - e.g. If the accountant has 40/80 blocks and the max block is 80, it will take
                    2 iterations to complete
                - This sequence data is cached locally to use in validations in order to save on compute
                  for the validating remote sequence runs including peers
                - By using only the Accountant in the sequence, the accountants data is assumed honest so others can not corrupt
                  the sequence data
                    - This also allows other accountants to know for sure that another accountant is dishonest because the data they 
                      submit is always checked against their own
            3. Run inference of other peers to validate by injecting them inside the blocks using the cached data
                - Only the block(s) used to validate peers are used in the sequence for inference
                - The other blocks not selected for the sequence are not ran and the cached data is used in its place instead
            4. Validate accountant inference outputs from the first accountant-only runs versus the peers we validated
                - Validate by checking relative and absolute tolerances
            -  If chosen epoch-Accountant, submit all data of each peers data to the blockchain
            -  If an Accountant in general, and found a dishonest peer, submit a dishonesty proposal


            Servers:        [00] [01] [02] [03] [04] [05] [06] [07] [08] [09] [10] [11] [12]
            Server Indexes: [   0   ]    |    |    |    |    |    |    |    |    |    |    |
                                 [   1   ]    |    |    |    |    |    |    |    |    |    |
                                      [   2   ]    |    |    |    |    |    |    |    |    |
                                           [   3   ]    |    |    |    |    |    |    |    |
                                                [   4   ]    |    |    |    |    |    |    |
                                                     [   5   ]    |    |    |    |    |    |
                                                          [   6   ]    |    |    |    |    |
                                                               [   7   ]    |    |    |    |
                                                                    [   8   ]    |    |    |
                                                                         [   9   ]    |    |
                                                                              [   10  ]    |
                                                                                   [   11  ]

                            """
        while True:
            # Begin epoch 
            epoch = self._get_epoch()

            # Reset accountant data for the new epoch
            self.accountant_data.reset()

            # Ensure that module container is created
            logger.info(f"Verifying validator blocks have begun")
            if self.server.module_container is None:
                # Restart loop
                logger.info("Module container not loaded yet")
                time.sleep(30)
                continue

            # Ensure that module container is initialized
            logger.info(f"Verifying validator blocks are healthy")
            if not self.server.module_container.is_healthy():
                # Restart loop
                logger.info("Module container not healthy yet")
                time.sleep(30)
                continue

            try:
                logger.info("Setting status to validator")
                self.server.is_validator = True

                if self.epoch == 0 and self.peers_data_to_validate is None:
                    # Restart loop
                    logger.info("Updating peers within the epoch")
                    self.update_peers()

                logger.info("Getting sequences of peers to validate")
                peers_validation_spans = self.get_peers_validation_spans()
                logger.info(f"Found {len(peers_validation_spans)} sequences")

                print("peers_validation_spans ", peers_validation_spans)

                # Get max start block 
                logger.info(f"Getting min/max blocks for Accountant to get inference data of")
                blocks = self.get_min_max_start_block_from_sequences(peers_validation_spans)
                # blocks = self.get_min_max_start_block()

                min_block = 0
                max_block = blocks[1]
                num_blocks = self.num_blocks
                print("self.num_blocks", self.num_blocks)
                if num_blocks > max_block:
                    num_blocks = max_block
                print("min_block ", min_block)
                print("max_block ", max_block)
                print("num_blocks", num_blocks)

                logger.info("Getting all ranges for Accountant to run inference sequences based on peers distributions")
                spans = []
                for index, value in enumerate(range(0, max_block+max_block-min_block, num_blocks)):
                    if index == 0:
                        spans.append([value, value + num_blocks])
                    else:
                        print(value + num_blocks)
                        if value + num_blocks > max_block:
                            if value + num_blocks - num_blocks != max_block:
                                spans.append([value + num_blocks - num_blocks, max_block])
                            break
                        else:
                            spans.append([value + num_blocks - num_blocks, value + num_blocks])

                print("spans", spans)

                logger.info("Gathering sequence to run as Accountant to cache the data")
                accountant_spans = []
                for span in spans:
                    start = span[0]
                    end = span[1]
                    print("start", start)   
                    print("end  ", end)   

                    accountant_span_ranges = []
                    for index, value in enumerate(range(start, end+end-start, 2)):
                        if index == 0:
                            # accountant_span_ranges.append([value, value + 1])
                            accountant_span_ranges.append({
                                'peer_id':self.my_peer_id,
                                'start':value,
                                'end':value + 1,
                            })
                        else:
                            # accountant_span_ranges.append([value-index, value-index + 1])
                            accountant_span_ranges.append({
                                'peer_id':self.my_peer_id,
                                'start':value-index,
                                'end':value-index + 1,
                            })

                    accountant_spans.append(accountant_span_ranges)

                print("accountant_spans", accountant_spans)

                logger.info("Running inference on accountant spans and storing inference results")
                for accountant_span in accountant_spans:
                    span_start = accountant_span[0]["start"]
                    span_end = accountant_span[-1]["end"]

                    print("accountant_span span_start", span_start)
                    print("accountant_span span_end  ", span_end)

                    block_indices = f"{span_start}:{span_end}"
                    print("accountant_span block_indices", block_indices)

                    logger.info(f"Updating strict blocks to {block_indices} if needed")
                    self.server.update_strict_block_indices(block_indices)
                    while True:
                        logger.info(f"Verifying validator blocks have begun")
                        if self.server.module_container is None:
                            # Restart loop
                            logger.info("Module container not loaded yet")
                            time.sleep(MODULE_CONTAINER_WAIT)
                            continue

                        start_block = self.server.module_container.server_info.start_block
                        end_block = self.server.module_container.server_info.end_block

                        if start_block != span_start and end_block != span_end:
                            logger.info("Blocks don't match yet")
                            time.sleep(MODULE_CONTAINER_WAIT)
                            continue

                        # Example: Wait until blocks are updated
                        # This is a hack attempt - need to instead check for that blocks have been updated to the correct spans
                        logger.info(f"Verifying validator blocks are healthy")
                        if not self.server.module_container.is_healthy():
                            # Restart loop
                            logger.info("Module container not healthy yet")
                            time.sleep(MODULE_CONTAINER_WAIT)
                            continue
                        
                        logger.info(f"Running inference as an Accountant on block indices {block_indices} and storing results")
                        self.run_inference_as_accountant(
                            self.input_data, 
                            peers=accountant_span
                        )
                        # print("\nself.my_inference_sequence_cache")
                        # pprint.pprint(self.my_inference_sequence_cache)

                        break

                logger.info("Complete inference sequence as Accountant using self")
                logger.info(f"Accountant has {len(self.my_inference_sequence_cache)} results cached")

                ####
                # Go peer by peer using cached data and injecting peer inside sequence to limit computations
                # Current implementation only supports double spans as in 0:1 or 2:3
                logger.info(f"Building sequence of spans {block_indices} to run sequence with other peers")                
                for peer_validation_span in peers_validation_spans:
                    print("peer_validation_span peers_validation_spans", peer_validation_span)
                    # Iterate and validate peer by peer
                    for peer in peer_validation_span:
                        print("peer_validation_span peer", peer)
                        tensors = []
                        span_ranges = []
                        block = 0
                        # Get full range of cache history if available to limit computation
                        while block <= max_block:
                            if peer["start"] == block:
                                # Add peer to sequence
                                span_ranges.append(peer)
                                block = peer["end"]
                            else:
                                # Add accountant sequence cache to sequence
                                input_tensors = self.get_account_input_tensors(block, block+1)
                                print("\npeer_validation_span input_tensors")
                                print("\n", block, block+1)
                                pprint.pprint(input_tensors)
                                if input_tensors is not None:
                                    tensors.append(input_tensors)
                                    block = input_tensors[0]["span_end"]
                                else:
                                    # If None, it will be filled in automatically when running the remote inference sequence
                                    block += 1

                        # Combine tensors into one array
                        sequence_tensors = []
                        for arr in tensors:
                            sequence_tensors += arr

                        logger.info(f"Running inference with {len(sequence_tensors)} input tensors and {len(span_ranges)} peers")

                        sequence_data = self.run_inference_with_tensors(
                            self.input_data, 
                            peers=span_ranges,
                            input_tensor=sequence_tensors
                        )
                        print("before validate_inference_results", peer)
                        self.validate_inference_results(peer, sequence_data)
                        break #testing

                # for peer_validation_span in peers_validation_spans:
                #     print("peer_validation_span peers_validation_spans", peer_validation_span)
                #     # Iterate and validate peer by peer
                #     for peer in peer_validation_span:
                #         print("peer_validation_span peer", peer)
                #         tensors = []
                #         span_ranges = []
                #         block = 0
                #         # Get full range of cache history if available to limit computation
                #         while block <= max_block:
                #             peer_span = next((x for x in peer if x['start'] == block), None)
                #             print("peer peer_span", peer_span)

                #             if peer_span is not None:
                #                 span_ranges.append(peer_span)
                #                 block = peer_span["end"]
                #             else:
                #                 input_tensors = self.get_account_input_tensors(block, block+1)
                #                 print("\npeer_validation_span input_tensors")
                #                 print("\n", block, block+1)
                #                 pprint.pprint(input_tensors)
                #                 if input_tensors is not None:
                #                     tensors.append(input_tensors)
                #                     block = input_tensors[0]["span_end"]
                #                 else:
                #                     block += 1

                #         sequence_tensors = []
                #         for arr in tensors:
                #             sequence_tensors += arr

                #         logger.info(f"Running inference with {len(sequence_tensors)} input tensors and {len(span_ranges)} peers")

                #         sequence_data = self.run_inference_with_tensors(
                #             self.input_data, 
                #             peers=span_ranges,
                #             input_tensor=sequence_tensors
                #         )
                #         self.validate_inference_results(peer_validation_span["peer_id"], sequence_data)
                #         break #testing

                # for peer_validation_span in peers_validation_spans:
                #     """"""
                #     print("peer_validation_span peers_validation_spans", peer_validation_span)
                #     tensors = []
                #     span_ranges = []
                #     block = 0
                #     # Get full range of cache history if available to limit computation
                #     while block <= max_block:
                #         peer_span = next((x for x in peer_validation_span if x['start'] == block), None)
                #         print("peer_validation_span peer_span", peer_span)

                #         if peer_span is not None:
                #             span_ranges.append(peer_span)
                #             block = peer_span["end"]
                #         else:
                #             input_tensors = self.get_account_input_tensors(block, block+1)
                #             print("\npeer_validation_span input_tensors")
                #             print("\n", block, block+1)
                #             pprint.pprint(input_tensors)
                #             if input_tensors is not None:
                #                 tensors.append(input_tensors)
                #                 block = input_tensors[0]["span_end"]
                #             else:
                #                 block += 1

                #     sequence_tensors = []
                #     for arr in tensors:
                #         sequence_tensors += arr

                #     logger.info(f"Running inference with {len(sequence_tensors)} input tensors and {len(span_ranges)} peers")
                #     self.run_inference_as_accountant(
                #         self.input_data, 
                #         peers=span_ranges,
                #         input_tensor=sequence_tensors
                #     )

                #     sequence_data = self.run_inference_with_tensors(
                #         self.input_data, 
                #         peers=span_ranges,
                #         input_tensor=sequence_tensors
                #     )
                #     self.validate_inference_results(peer_validation_span["peer_id"], sequence_data)
                #     break #testing

                print('\naccountant_data\n')
                pprint.pprint(self.accountant_data.data)

            except Exception as e:
                logger.error("Error 1551", e)
            finally:
                self.server.remove_strict_block_indices()
                self.server.is_validator = False
                seconds_remaining_in_epoch = self._get_seconds_remaining_in_epoch()
                logger.info(f"Next epoch is {seconds_remaining_in_epoch} seconds away, sleeping for remaining time")
                time.sleep(seconds_remaining_in_epoch)

    def run_in_background(self, await_ready=True, timeout=None):
        self.start()

    def shutdown(self):
        logger.info("Shutting down inference validator")
        self.stop.set()
        self.exit()

    def set_deterministic(self):
        torch.manual_seed(0)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # def get_validation_sequences(self) -> List:
    #     peers_data_to_validate = self.peers_data_to_validate
    #     validation_sequences = []
    #     while len(peers_data_to_validate) > 0:
    #         validation_sequence = []
    #         block = 0
    #         while block < self.num_model_blocks:
    #             peers = [i for i in peers_data_to_validate if i['span_start'] <= block <= i["span_end"]]
    #             print("peers", peers)
    #             if len(peers) > 0:
    #                 chosen_peer = min(peers, key=lambda x:x["span_end"] - block)
    #             else:
    #                 block += 1
    #                 continue

    #             end = block
    #             if chosen_peer["span_end"] >= block + 1:
    #                 end = block + 1

    #             validation_sequence.append(
    #                 {
    #                     "peer_id": chosen_peer['peer_id'],
    #                     "start": block,
    #                     "end": end,
    #                 }
    #             )
    #             block = end
    #             peers_data_to_validate.remove(chosen_peer)
    #             if len(peers_data_to_validate) == 0:
    #                 break
    #         validation_sequences.append(validation_sequence)
    #     return validation_sequences

    def get_peers_validation_spans(self) -> List:
        """
        Get 1 block span for each peer in the subnet: e.g. 0:1, 119:120

        This data is used to check each peer peer by peer and get the min and max blocks to validate
        """
        peers_data_to_validate = self.peers_data_to_validate
        validation_sequences = []
        while len(peers_data_to_validate) > 0:
            validation_sequence = []
            block = 0
            while block < self.num_model_blocks:
                peers = [i for i in peers_data_to_validate if i['span_start'] <= block <= i["span_end"]]
                print("peers", peers)
                if len(peers) == 0:
                    block += 1
                    continue

                for peer in peers:
                    validation_sequence.append(
                        {
                            "peer_id": peer['peer_id'],
                            "start": block,
                            "end": block+1,
                        }
                    )
                    peers_data_to_validate.remove(peer)

                block += 1

                if len(peers_data_to_validate) == 0:
                    break
            validation_sequences.append(validation_sequence)
        return validation_sequences

    # def get_validation_sequences2(self) -> List:
    #     print("get_validation_sequences2")
    #     peers_data_to_validate = self.peers_data_to_validate
        
    #     sequences = []
    #     while len(peers_data_to_validate) > 0:
    #         time.sleep(1)
    #         sequence = []
    #         for block in range(0, self.num_model_blocks):
    #             print("block", block)
    #             peers = [i for i in peers_data_to_validate if i['span_start'] <= block <= i["span_end"]]
    #             print("peers", peers)
    #             if len(peers) == 0:
    #                 continue
    #             elif len(peers) > 1:
    #                 chosen_peer = min(peers, key=lambda x:block - x["span_start"])
    #             else:
    #                 chosen_peer = peers[0]
    #             print("chosen_peer", chosen_peer)
    #             sequence.append(
    #                 {
    #                     "peer_id": chosen_peer['peer_id'],
    #                     "start": block,
    #                     "end": block + 1,
    #                 }
    #             )
    #             peers_data_to_validate.remove(chosen_peer)

    #             if len(peers_data_to_validate) == 0:
    #                 break
    #             # list(filter(lambda x: x['peer_id'] != chosen_peer['peer_id'], peers_data_to_validate))
    #         sequences.append(sequence)

    #     return sequences

    def get_min_max_start_block_from_sequences(self, sequences) -> List:
        """Get span of blocks validator must get outputs for as Accountant"""
        start_block = 0
        end_block = self.num_model_blocks

        for sequence in sequences:
            start_block = min(sequence, key=lambda x: x['start'])['start']
            end_block = max(sequence, key=lambda x: x['end'])['end']

        return [0, end_block]

    # def get_min_max_start_block(self) -> List:
    #     """
    #     Return the range for accountant to check

    #     The minimum for lowest_end_block is 0
    #     The maximum for highest_start_block is self.num_model_blocks

    #     This functions assumes there are more than one peer in the the subnet
    #     """
    #     lowest_end_block = self.num_model_blocks + 1
    #     highest_start_block = 0
    #     for peer in self.peers_data_to_validate:
    #         start_block = peer['span_start']
    #         end_block = peer['span_end']
    #         if start_block > highest_start_block:
    #             highest_start_block = start_block
    #         if end_block < lowest_end_block:
    #             lowest_end_block = end_block

    #     highest_start_block += 1
    #     if lowest_end_block > 0:
    #         lowest_end_block -= 1

    #     if highest_start_block < lowest_end_block:
    #         highest_start_block = lowest_end_block + 1

    #     return [lowest_end_block, highest_start_block]
        
    # def run_inference(
    #     self, 
    #     input_data, 
    #     span_start,
    #     span_end,
    #     peers: Optional[List[Dict]] = None, 
    #     peer_id: Optional[str] = None
    # ):
    #     """Run inference and return the results from the span_start to the span_end"""
    #     # TODO: Get inference only up to the end block required to run inference checks to save on compute
    #     _input_data = self.tokenizer(input_data, return_tensors="pt")["input_ids"]

    #     if peers is not None:
    #         inference_session_data, outputs = self.model.generate(
    #             _input_data, 
    #             peers=peers,
    #             max_new_tokens=5
    #         )
    #     elif peer_id is not None:
    #         inference_session_data, outputs = self.model.generate(
    #             _input_data, 
    #             peer_id=peer_id, 
    #             max_new_tokens=5
    #         )
    #         inference_data = self.get_peer_inference_results(inference_session_data, peer_id, span_start, span_end)

    #     print("run_inference results", outputs)
    #     print("run_inference inference_data", inference_data["outputs"])

    #     return inference_data["outputs"] if inference_data is not None else None
    #     # return outputs

    def run_inference_as_accountant(
        self, 
        input_data, 
        peers: List[Dict],
    ):
        try:
            """Run inference and return the results from the span_start to the span_end"""
            # TODO: Get inference only up to the end block required to run inference checks to save on compute
            _input_data = self.tokenizer(input_data, return_tensors="pt")["input_ids"]

            inference_session_data, outputs = self.model.generate_with_tensors(
                _input_data, 
                peers=peers,
                max_new_tokens=5,
            )

            my_inference_sequence_cache = self.get_accountant_inference_results(inference_session_data)
            self.push_inference_sequence_cache(my_inference_sequence_cache)

        except Exception as e:
            logger.warning(f"Accountant Inference Validation Error: {e}")

    def run_inference_with_tensors(
        self, 
        input_data, 
        peers: List[Dict],
        input_tensor: Optional[torch.Tensor] = None, 
    ):
        try:
            """Run inference and return the results from the span_start to the span_end"""
            # TODO: Get inference only up to the end block required to run inference checks to save on compute
            _input_data = self.tokenizer(input_data, return_tensors="pt")["input_ids"]

            inference_session_data, outputs = self.model.generate_with_tensors(
                _input_data, 
                peers=peers,
                max_new_tokens=5,
                tensors=input_tensor
            )
            return inference_session_data
        except Exception as e:
            logger.warning(f"Accountant Inference Validation Error: {e}")

    def push_inference_sequence_cache(self, sequence: List):
        """This data sent in here should only be matched with self.my_peer_id"""
        if self.my_inference_sequence_cache is None:
            self.my_inference_sequence_cache = sequence
        else:
            for data in sequence:
                span_found = next((x for x in self.my_inference_sequence_cache if x['server_idx'] == data["server_idx"]), None)
                
                """Append span data if none exists"""
                if span_found is None:
                    self.my_inference_sequence_cache.append(data)

    # def get_peers_to_inject_in_sequence(
    #     self, 
    #     span_start, 
    #     span_end
    # ):
    #     peer_candidates = []
    #     for peer in self.peers_data_to_validate:
    #         if peer['span_start'] <= span_start <= peer['span_end'] and peer['span_start'] <= span_end <= peer['span_end']:
    #             peer_candidates.append(peer)

    #     if len(peer_candidates) == 0:
    #         logger.info(f"No peer found for span_start: {span_start}, span_end: {span_end}")
    #         return None
    #     else:
    #         chosen_peer = min(peer_candidates, key=lambda x:x['end']-x['start'])
    #         return chosen_peer

    # def get_peer_to_inject_in_sequence(self, block):
    #     peer_candidates = []
    #     for peer in self.peers_data_to_validate:
    #         # Get peers overlapping block
    #         if peer['span_start'] <= block <= peer['span_end'] and peer["peer_id"] != self.my_peer_id:
    #             peer_candidates.append(peer)

    #     if len(peer_candidates) == 0:
    #         logger.info(f"No peer found for block: {block}")
    #         return None
    #     else:
    #         chosen_peer = min(peer_candidates, key=lambda x:block - x["span_start"])
    #         logger.info(f"Peer found for block: {block}, peer_id: {chosen_peer['peer_id']}")
    #         peer_to_inject = next((x for x in self.peers_data_to_validate if x['peer_id'] == chosen_peer["peer_id"]), None)
    #         if peer_to_inject is not None:
    #             # Update validate list by removing peer chosen
    #             self.peers_data_to_validate = list(filter(lambda x: x['peer_id'] != chosen_peer['peer_id'], self.peers_data_to_validate))
            
    #         return peer_to_inject

    def get_account_input_tensors(self, start, end) -> List:
        """Return all sequence outputs that match the start and end blocks"""
        print(f"get_account_input_tensors start {start}, end {end}")

        inference_sequence_cache = [i for i in self.my_inference_sequence_cache if i['span_start'] == start and i['span_end'] == end]
         
        print("get_account_input_tensors inference_sequence_cache \n")
        pprint.pprint(inference_sequence_cache)

        if inference_sequence_cache is None or len(inference_sequence_cache) == 0:
            return None

        return inference_sequence_cache

    # def validate_inference(
    #     self, 
    #     input_data, 
    #     span_start, 
    #     span_end, 
    #     expected_outputs, 
    #     peer_id: str,
    #     peers: List[Dict]
    # ) -> bool:
    #     """Validate the inference from the span_start - span_end"""
    #     try:
    #         _input_data = self.tokenizer(input_data, return_tensors="pt")["input_ids"]

    #         # Perform inference
    #         inference_session_data, outputs = self.model.generate(
    #             _input_data, 
    #             peers=peers, 
    #             max_new_tokens=5
    #         )

    #         inference_data = self.get_peer_inference_results(inference_session_data, peer_id, span_start, span_end)
    #         print("validate_inference inference_data", inference_data)

    #         # TODO: Add edge checking
    #         if inference_data is not None:
    #             outputs = inference_data["outputs"]
    #             expected_outputs_tensor_sum = torch.sum(expected_outputs)
    #             outputs_tensor_sum = torch.sum(outputs)

    #             tensor_diff = expected_outputs_tensor_sum - outputs_tensor_sum
    #             tensor_sum = outputs_tensor_sum

    #             logger.info(f"Tensor sum diff is:              {tensor_diff}/{-tensor_diff}")
    #             logger.info(f"Max tensor sum diff is:          {-ATOL}/{ATOL}")
    #             logger.info(f"Expected output tensor sum is:   {expected_outputs_tensor_sum}")
    #             logger.info(f"Validating output tensor sum is: {outputs_tensor_sum}")

    #             logger.info("expected_outputs: \n")
    #             pprint.pprint(expected_outputs)
    #             logger.info("outputs: \n")
    #             pprint.pprint(outputs)

    #             valid = torch.allclose(expected_outputs, outputs, rtol=RTOL, atol=ATOL, equal_nan=False)

    #             accountant_data_peer_params = AccountantDataPeerParams(
    #                 peer_id=peer_id,
    #                 input_tensor=_input_data,
    #                 data=[PeerInferenceSequenceData(
    #                     peer_id=peer_id,
    #                     position=0,
    #                     span_start=int(span_start),
    #                     span_end=int(span_end),
    #                     accountant_tensor_sum=float(expected_outputs_tensor_sum),
    #                     tensor_sum=float(tensor_sum),
    #                     valid=valid,
    #                 )]
    #             )
                
    #             # peer_inference_data = PeerInferenceSequenceData(
    #             #     peer_id=peer_id,
    #             #     span_start=span_start,
    #             #     span_end=span_end,
    #             #     accountant_tensor_sum=expected_outputs_tensor_sum,
    #             #     tensor_sum=tensor_sum,
    #             #     valid=valid,
    #             # )
    #             self.accountant_data.add_data(accountant_data_peer_params)

    #             # rtol: relative tolerance at 1e-03 or as float 0.001
    #             # atol: absolute tolerance at 8e-01 or as float 0.8
    #             # equal_nan: True to compare NaN's as equal, False otherwise.
    #             # If both are False, then NaN's will be treated as unequal.
    #             # If both are True, then NaN's will be treated as equal.
    #             # If both are None, then the behavior is equivalent to False.
    #             return valid
    #         else:
    #             logger.info(f"Inference data is None")
    #             accountant_data_peer_params = AccountantDataPeerParams(
    #                 peer_id=peer_id,
    #                 input_tensor=_input_data,
    #                 data=[PeerInferenceSequenceData(
    #                     peer_id=peer_id,
    #                     position=0,
    #                     span_start=int(span_start),
    #                     span_end=int(span_end),
    #                     accountant_tensor_sum=float(0),
    #                     tensor_sum=float(0),
    #                     # accountant_tensor=str(""),
    #                     # peer_tensor=str(""),
    #                     valid=False,
    #                 )]
    #             )

    #             # peer_inference_data = PeerInferenceSequenceData(
    #             #     peer_id=peer_id,
    #             #     span_start=span_start,
    #             #     span_end=span_end,
    #             #     accountant_tensor_sum=0,
    #             #     tensor_sum=0,
    #             #     valid=False,
    #             # )
    #             self.accountant_data.add_data(accountant_data_peer_params)

    #             return False
    #     except Exception as e:
    #         logger.warning(f"Inference Validation Error: {e}")
    #         accountant_data_peer_params = AccountantDataPeerParams(
    #             peer_id=peer_id,
    #             input_tensor=None,
    #             data=[PeerInferenceSequenceData(
    #                 peer_id=peer_id,
    #                 position=0,
    #                 span_start=int(span_start),
    #                 span_end=int(span_end),
    #                 accountant_tensor_sum=float(0),
    #                 tensor_sum=float(0),
    #                 valid=False,
    #             )]
    #         )

    #         # peer_inference_data = PeerInferenceSequenceData(
    #         #     peer_id=peer_id,
    #         #     span_start=span_start,
    #         #     span_end=span_end,
    #         #     accountant_tensor_sum=0,
    #         #     tensor_sum=0,
    #         #     valid=False,
    #         # )
    #         self.accountant_data.add_data(accountant_data_peer_params)

    #         return False

    #     # Check if the output matches the expected output
    #     # TODO: Add edge checking
    #     # return torch.equal(outputs, expected_outputs)

    def validate_inference_results(self, peer_data, inference_session_data):
        peer_id = peer_data["peer_id"]
        start = peer_data["start"]
        end = peer_data["end"]

        peer_validation_data = PeerValidationData(
            input_tensor=None,
            a_tol=ATOL,
            r_tol=RTOL,
            data=[] # PeerInferenceResults
        )
        
        peer_inference_results = PeerInferenceResults(
            span_start=start,
            span_end=end,
            data=[] # PeerInferenceSequenceData
        )

        """Iterate inference results for a given peer"""
        for session in inference_session_data:
            if session["peer_id"] != peer_id:
                continue

            # Get cached accountant inference session data to check against
            span_start = session["span_start"]
            span_end = session["span_end"]
            position = session["position"]

            print("validate_inference_results span_start", span_start)
            print("validate_inference_results span_end", span_end)
            print("validate_inference_results position", position)

            # Find cached results to compare
            accountant_inference_cache = self.get_inference_by_position(
                self.my_peer_id, 
                self.my_inference_sequence_cache, 
                span_start, 
                span_end, 
                position
            )
            
            if accountant_inference_cache is None or len(accountant_inference_cache) == 0:
                continue

            print("\n validate_inference_results accountant_inference_cache\n")
            pprint.pprint(accountant_inference_cache)

            # Peers outputs
            outputs = session["outputs"]
            # Accountants outputs
            expected_outputs = accountant_inference_cache["outputs"]

            expected_outputs_tensor_sum = torch.sum(expected_outputs)
            outputs_tensor_sum = torch.sum(outputs)

            tensor_diff = expected_outputs_tensor_sum - outputs_tensor_sum

            valid = torch.allclose(expected_outputs, outputs, rtol=RTOL, atol=ATOL, equal_nan=False)

            logger.info(f"Tensor sum diff is:              {tensor_diff}/{-tensor_diff}")
            logger.info(f"Max tensor sum diff is:          {-ATOL}/{ATOL}")
            logger.info(f"Expected output tensor sum is:   {expected_outputs_tensor_sum}")
            logger.info(f"Validating output tensor sum is: {outputs_tensor_sum}")
            logger.info(f"Inference valid status:          {valid}")

            peer_inference_sequence = PeerInferenceSequenceData(
                position=position,
                accountant_tensor_sum=expected_outputs_tensor_sum,
                tensor_sum=outputs_tensor_sum,
                valid=valid
            )

            peer_inference_results.data.append(peer_inference_sequence)

        peer_validation_data.data.append(peer_inference_results)

        valid_all = True
        valid = []
        for data in peer_validation_data.data:
            print("data ->", data)
            print("data.data ->", data.data)
            valid.append(data.data.valid)

        valid_count = len(valid)
        valid_true = sum(valid)

        valid_rate = valid_true / valid_count if valid_count > 0 else 0
        if valid_rate < VTOL:
            valid_all = False

        self.accountant_data.add_data(
            AccountantDataPeerParams(
                peer_id=peer_id,
                valid=valid_all,
                data=peer_validation_data,
            )
        )

    def get_accountant_inference_results(self, inference_session_data) -> List:
        """Append the inference results by the accountant only"""
        inference_data = []
        for data in inference_session_data:
            if data['peer_id'].__eq__(self.my_peer_id):
                inference_data.append(data)
        return inference_data

    # def get_accountant_inference_cache(self, start, end, position) -> List:
    #     """Return cached inference sequence data for a given start, end, and position"""
    #     inference_data = []
    #     for data in self.my_inference_sequence_cache:
    #         if data['span_start'] == start and data['span_end'] == end and data['position'] == position:
    #             inference_data.append(data)
    #     return inference_data

    def get_inference_by_position(self, peer_id, sequence_data, start, end, position) -> List:
        """Return cached inference sequence data for a given start, end, and position"""
        # inference_data = []
        for data in sequence_data:
            if data['peer_id'] == peer_id and data['span_start'] == start and data['span_end'] == end and data['position'] == position:
                # inference_data.append(data)
                return data
        return None

    # def get_peer_inference_results(self, inference_session_data, peer_id, span_start, span_end):
    #     inference_data = None
    #     for data in inference_session_data:
    #         if data['peer_id'].__eq__(peer_id) and data['span_start'] == span_start and data['span_end'] == span_end:
    #             inference_data = data
    #             break
    #     return inference_data

    def initiate_dishonesty(self, peer_id):
        """
        Propose the peer as dishonest on the blockchain
            If already proposed, then vote
        """

        # Check if proposal already exists
        proposal_exists = True 
        # if proposal_exists:
        #     tx_hash = vote_model_peer_dishonest(
        #         self.client.substrate_interface,
        #         self.client.keypair,
        #         model_id=0,  # Example: model id
        #         peer_id=peer_id,  # Example: peer id to vote as dishonest
        #     )
        # else:
        #     tx_hash = propose_model_peer_dishonest(
        #         self.client.substrate_interface,
        #         self.client.keypair,
        #         model_id=0,  # Example: model id
        #         peer_id=peer_id,  # Example: peer id to vote as dishonest
        #     )

        tx_hash = 0

        print(f"Proposed dishonest peer {peer_id} with transaction hash: {tx_hash}")

    def submit_accountant_data(self, data: str):
        """
        Submit data to the blockchain if chosen accountant on the epoch.

        The data must be formatted as a string to send to the blockchain
        This data can then be used for other subnet nodes to pull from the blockchain storage
        """
        # tx_hash = submit_data(
        #     self.client.substrate_interface,
        #     self.client.keypair,
        #     data=data,
        # )

    def update_peers(self):
        self.peers_data = []
        self.peers_data_to_validate = []
        peers_data_list = get_peers_data_list()
        for peer in peers_data_list:
            logger.info(f"update_peers peer_id: {peer['peer_id'] }")
            if peer['peer_id'] != self.my_peer_id:  # Exclude the validator from the peer list
                self.peers_data.append(peer)

        self.peers_data_to_validate = self.peers_data

    def _get_peer_data(self, peer_id):
        return next((x for x in self.peers_data_to_validate if x['peer_id'] == peer_id), None)

    def _get_peers_data_in_range(self, span_start: int, span_end: int) -> List:
        peers_data: List = []
        for peer in self.peers_data_to_validate:
            if peer['peer_id'] != self.my_peer_id and peer['span_start'] == span_start and peer['span_end'] == span_end:  # Exclude the validator from the peer list
                peers_data.append(peer)

        return peers_data 
    
    def _get_peers_data_within_range(self, span_start: int, span_end: int) -> List:
        """
        Get peers that are within the given range
        ex: If span_start: 0, span_end: 20
            results = [0:20, 5:15, 10:20]
        """
        peers_data: List = []
        for peer in self.peers_data_to_validate:
            if (peer['peer_id'] != self.my_peer_id and 
                peer['span_start'] >= span_start and 
                peer['span_end'] <= span_end
            ):  # Exclude the validator from the peer list
                peers_data.append(peer)

        return peers_data
    
    def _get_sequence_for_inference(self, peers_data) -> List:
        """"""
        peers = []
        total_peers = len(peers_data)
        min_span = self.num_blocks + 1
        for peer in peers_data:
            span_len = int(peer["span_end"]) - int(peer["span_start"])
            if span_len < min_span:
                min_span = span_len

        max_span = 0

    def _is_accountant(self) -> bool:
        """Check blockchain if self is the chosen accountant to submit inference validataion data for the epoch"""
        # accountant_account_id = get_epoch_accountant(
        #     SubstrateConfig.interface, 
        #     SubstrateConfig.keypair,
        #     self.model_id
        # )
        # if accountant_account_id == SubstrateConfig.account_id:
        #     self.is_accountant = True
        # else:
        #     self.is_accountant = False

        return self.is_accountant

    def _get_epoch(self):
        """Do math to get epoch number from blockchain"""
        # block_hash = SubstrateConfig.interface.get_block_hash()
        # block_number = SubstrateConfig.interface.get_block_number(block_hash)
        # network_config = load_network_config()
        # min_required_model_consensus_submit_epochs = network_config.min_required_model_consensus_submit_epochs
        # min_required_peer_consensus_submit_epochs = network_config.min_required_peer_consensus_submit_epochs
        # min_model_peers = network_config.min_model_peers
        # epoch_length = network_config.epoch_length

        return 1

    def _get_seconds_remaining_in_epoch(self) -> int:
        """
        Get how much time is left in the epoch until the next epoch
        
        This is used to wait until the next epoch to begin inference validation again
        """
        return 100
    
    def compare_accountant_data():
        """
        Compare the current accountant data to self
        """
        # accountant_data = get_previous_accountant_data(
        #     SubstrateConfig.interface, 
        #     SubstrateConfig.keypair,
        #     self.model_id
        # )

    def proof_of_stake(self, peer_id: PeerID):
        """remove a given peer from the routing table. If the routing is no longer possible, trigger an update"""
        # if peer_id is not None:
        #     logger.debug(f"Peer {peer_id} did not respond, banning it temporarily")
        #     self.state.banned_peers.register_failure(peer_id)
        # with self.lock_changes:
        #     should_update = False
        #     for info in self.state.sequence_info.block_infos:
        #         info.servers.pop(peer_id, None)
        #         if not info.servers:
        #             should_update = True
        #     if should_update:
        #         self.ready.clear()
        #         self.update(wait=False)
