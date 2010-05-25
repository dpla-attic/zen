#freemixlib

__version__ = '0.9.1'

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


#Convenience decorator for registering services
def zservice(service_id):
    """Add the function as an Zen service

    This affect how the resource is registered in Zen:
      service_id - a string which identifies this service; should be a URL
    """
    def zregister(func):
        func.serviceid = service_id
        register_service(func)
        return func
    return zregister

