#freemixlib

__version__ = '0.8.9.9'

#Mapping from service ID URI too URL template and/or callable
SERVICES = {}

def register_service(s):
    '''
    info - either a callable, which has its URL as the serviceid attribute
           or a tuple of (serviceid, callable)
    Note: rgistration of remote services is done in the Zen section of Akara config, for now
    '''
    if callable(s):
        SERVICES[s.serviceid] = s
    else:
        SERVICES[s[0]] = s[1]

#Bootstrap in the built-in ("local") services
from zenlib import local

