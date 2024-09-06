# Good to go
import sys
import warnings

# from eventlet import greenpool
from eventlet import support
import socket # Changed

def connect(addr, family=socket.AF_INET, bind=None):
    """Convenience function for opening client sockets.

    :param addr: Address of the server to connect to.  For TCP sockets, this is a (host, port) tuple.
    :param family: Socket family, optional.  See :mod:`socket` documentation for available families.
    :param bind: Local address to bind to, optional.
    :return: The connected green socket object.
    """
    sock = socket.socket(family, socket.SOCK_STREAM)
    if bind is not None:
        sock.bind(bind)
    sock.connect(addr)
    return sock


class ReuseRandomPortWarning(Warning):
    pass


class ReusePortUnavailableWarning(Warning):
    pass


def listen(addr, family=socket.AF_INET, backlog=50, reuse_addr=True, reuse_port=None):
    """Convenience function for opening server sockets.  This
    socket can be used in :func:`~eventlet.serve` or a custom ``accept()`` loop.

    Sets SO_REUSEADDR on the socket to save on annoyance.

    :param addr: Address to listen on.  For TCP sockets, this is a (host, port)  tuple.
    :param family: Socket family, optional.  See :mod:`socket` documentation for available families.
    :param backlog:

        The maximum number of queued connections. Should be at least 1; the maximum
        value is system-dependent.

    :return: The listening green socket object.
    """
    sock = socket.socket(family, socket.SOCK_STREAM)
    if reuse_addr and sys.platform[:3] != 'win':
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if family in (socket.AF_INET, socket.AF_INET6) and addr[1] == 0:
        if reuse_port:
            warnings.warn(
                '''listen on random port (0) with SO_REUSEPORT is dangerous.
                Double check your intent.
                Example problem: https://github.com/eventlet/eventlet/issues/411''',
                ReuseRandomPortWarning, stacklevel=3)
    elif reuse_port is None:
        reuse_port = True
    if reuse_port and hasattr(socket, 'SO_REUSEPORT'):
        # NOTE(zhengwei): linux kernel >= 3.9
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # OSError is enough on Python 3+
        except OSError as ex:
            if support.get_errno(ex) in (22, 92):
                # A famous platform defines unsupported socket option.
                # https://github.com/eventlet/eventlet/issues/380
                # https://github.com/eventlet/eventlet/issues/418
                warnings.warn(
                    '''socket.SO_REUSEPORT is defined but not supported.
                    On Windows: known bug, wontfix.
                    On other systems: please comment in the issue linked below.
                    More information: https://github.com/eventlet/eventlet/issues/380''',
                    ReusePortUnavailableWarning, stacklevel=3)

    sock.bind(addr)
    sock.listen(backlog)
    return sock


class StopServe(Exception):
    """Exception class used for quitting :func:`~eventlet.serve` gracefully."""
    pass


def wrap_ssl(sock, *a, **kw):
    """Convenience function for converting a regular socket into an
    SSL socket.  Has the same interface as :func:`ssl.wrap_socket`,
    but can also use PyOpenSSL. Though, note that it ignores the
    `cert_reqs`, `ssl_version`, `ca_certs`, `do_handshake_on_connect`,
    and `suppress_ragged_eofs` arguments when using PyOpenSSL.

    The preferred idiom is to call wrap_ssl directly on the creation
    method, e.g., ``wrap_ssl(connect(addr))`` or
    ``wrap_ssl(listen(addr), server_side=True)``. This way there is
    no "naked" socket sitting around to accidentally corrupt the SSL
    session.

    :return Green SSL object.
    """
    return wrap_ssl_impl(sock, *a, **kw)


try:
    import ssl
    wrap_ssl_impl = ssl.wrap_socket
except ImportError:
    # trying PyOpenSSL
    try:
        from OpenSSL import SSL # Changed
    except ImportError:
        def wrap_ssl_impl(*a, **kw):
            raise ImportError(
                "To use SSL with Eventlet, you must install PyOpenSSL or use Python 2.7 or later.")
    else:
        def wrap_ssl_impl(sock, keyfile=None, certfile=None, server_side=False,
                          cert_reqs=None, ssl_version=None, ca_certs=None,
                          do_handshake_on_connect=True,
                          suppress_ragged_eofs=True, ciphers=None):
            # theoretically the ssl_version could be respected in this line
            context = SSL.Context(SSL.SSLv23_METHOD)
            if certfile is not None:
                context.use_certificate_file(certfile)
            if keyfile is not None:
                context.use_privatekey_file(keyfile)
            context.set_verify(SSL.VERIFY_NONE, lambda *x: True)

            connection = SSL.Connection(context, sock)
            if server_side:
                connection.set_accept_state()
            else:
                connection.set_connect_state()
            return connection