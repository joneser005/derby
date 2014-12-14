import logging

log = logging.getLogger('runner')

_GOODBYE_MESSAGE = u'Goodbye'

def web_socket_do_extra_handshake(request):
    # This example handler accepts any request. See origin_check_wsh.py for how
    # to reject access from untrusted scripts based on origin value.
    print('ws_resource', request.ws_resource)
    print('ws_origin', request.ws_origin)
    print('ws_version', request.ws_version)
    log.info("ws connection established")
    pass  # Always accept.


def web_socket_transfer_data(request):
    while True:
        line = request.ws_stream.receive_message()
        log.debug('Request received')
        if line is None:
            return
        if isinstance(line, unicode):
            request.ws_stream.send_message(line, binary=False)
            if line == _GOODBYE_MESSAGE:
                return
        else:
            request.ws_stream.send_message(line, binary=True)

def web_socket_passive_closing_handshake(request):
    print("Client closed ws connection.  Good dog!");