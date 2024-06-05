import json
import http.server
import socketserver
from typing import Tuple
from http import HTTPStatus
from petals_tensor.substrate import config as substrate_config
# import os
# import signal
import time
# import multiprocessing as mp

"""Untested code, all comments are assumed"""

class Handler(http.server.SimpleHTTPRequestHandler):
  """Its up to the server to set the inbound security rules for the server port you designate for socket calls"""
  
  """Temporary list
  @to-do: dynamically list all validator IPs"""
  white_list_ips = ["127.0.0.1", "127.0.0.1"]
  last_call = 0

  def __init__(self, request: bytes, client_address: Tuple[str, int], server: socketserver.BaseServer):
    super().__init__(request, client_address, server)

  @property
  def api_response(self):
    return json.dumps({"message": "Expected hash will be here"}).encode()

  def do_GET(self):
    timestamp = time.time()
    if self.path == '/' and self.client_address[0] in self.white_list_ips:
      Handler.last_call = timestamp
      self.send_response(HTTPStatus.OK)
      self.send_header("Content-Type", "application/json")
      self.end_headers()
      self.wfile.write(bytes(self.api_response))

if __name__ == "__main__":
  try:
    model_validator_config = substrate_config.load_model_validator_config()
    PORT = model_validator_config.port
    server = socketserver.TCPServer(("0.0.0.0", PORT), Handler)
    socketserver.TCPServer.allow_reuse_address = True
    print(f"Server started at {PORT}")
    server.serve_forever()
  except KeyboardInterrupt:
    print("Caught KeyboardInterrupt, shutting down")
  finally:
    print(f"Server shutting down")
    # server.shutdown()
    server.server_close()

