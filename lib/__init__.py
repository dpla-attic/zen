#freemixlib

__version__ = '0.9.0'

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
try:
    from zenlib import local
except ImportError:
    #This will be the case during install
    pass #Is this really a good idea?  What if there is really a problem?

