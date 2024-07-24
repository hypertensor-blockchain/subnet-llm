class Error(Exception):
  pass

class SubscriptionException(Error):
  """Exception for stopping subscriptions to blocks and stopping consensus"""
  def __init__(self, msg):
    self.msg = msg
