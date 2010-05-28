__all__ = ['create_proxy', 'POST_BODY', 'POST_RESPONSE']

from akara import request

#Create a proxy function for a service available over HTTP
def create_proxy(service_id, method, resultmap, *xarg, **xkwarg):
    """Add the function as an Zen service

    This affect how the resource is registered in Zen:
      service_id - a string which identifies this service; should be a URL
    """
    endpoint = find_peer_service(request.environ, service_id)

    def premap(env, arg, kwarg):
        if POST_BODY in xarg:
            index = xarg.index(POST_BODY)
            env['body'] = arg[index]
        return

    def postmap(env, resp, content):
        result = [None]*len(resultmap)
        if POST_RESPONSE in resultmap:
            index = resultmap.index(POST_RESPONSE)
            result[index] = content
        if not isinstance(resultmap, tuple):
            result = result[0]
        env['result'] = result
        return

    def proxy_func(*arg, **kwarg):
        #FIXME: Implement URL templates
        #FIXME: Support headers spec
        premap(locals(), arg, kwarg)
        resp, content = H.request(endpoint, method, body=body, headers=headers)
        postmap(locals(), resp, content)
        return result

    proxy_func.serviceid = service_id
    register_service(proxy_func)
    return func

#
#Singletons to indicate how HTTP constructs are interpreted
POST_BODY = object()
POST_RESPONSE = object()

