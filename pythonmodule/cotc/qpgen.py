import importlib
  
def load_mpc(name, horizon):
  try:
    return importlib.import_module('cotc.qpgenimp.{}.qpbnb{}'.format(name, horizon))
  except ModuleNotFoundError as e:
    pass
  raise ModuleNotFoundError('No {} MPC is defined for horizon {}'.format(name, horizon))

