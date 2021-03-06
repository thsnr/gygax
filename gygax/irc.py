# -*- coding: utf-8 -*-

"""
:mod:`gygax.irc` --- Internet Relay Chat client.
================================================

:mod:`gygax.irc` implements all functionality needed to communicate with an IRC
server. It does so using :mod:`asynchat` from the Python Standard Library,
which handles all asynchronous network complexities and leaves :mod:`gygax.irc`
only with the task of handling the IRC protocol.

:mod:`gygax.irc` defines the abstract class :class:`Client`, which can be
subclassed and provided an implementation for the :func:`Client.handle` method
to build IRC bots or custom clients.
"""

import asynchat
import asyncore
import logging
import time

log = logging.getLogger(__name__)

class Client(asynchat.async_chat):

    """An abstract class which implements a minimal, but functional subset of
    the IRC client protocol.

    :param str nick: The client's nickname to use. Also used as the username.
    :param str real: The client's realname to use.

    Handles most IRC messages itself, but on private messages (messages sent to
    the client directly or to a channel the client is on) calls the
    :meth:`handle` abstract method. This method can be overridden by subclasses
    to create IRC bots or custom clients.
    """

    @property
    def nick(self):
        """The client's nickname. Also used as the username."""
        return self._nick

    @property
    def real(self):
        """The client's realname."""
        return self._real

    @property
    def channels(self):
        """A :func:`set` containing the channels the client is connected to."""
        return self._channels

    def __init__(self, nick, real):
        """Creates a new IRC client and initializes its attributes."""
        super().__init__()
        self.set_terminator(b"\r\n")
        self._incoming = []

        self._nick = nick
        self._real = real
        self._channels = set()
        self._password = None
        self._autosend = list()

    def run(self, address, channels=None, password=None, autosend=None):
        """Connect to an IRC server and start the client's main loop.

        :param tuple address: A tuple ``(host, port)`` with the address of the
            IRC server to connect to.
        :param iter channels: The list of channels to join on startup.
        :param str password: The optional connection password to use.
        :param iter autosend: The list of messages to send after successful
            registration with the server, but before joining any channels.
        """
        self._channels = channels or set()
        self._password = password
        self._autosend = autosend or list()

        log.info("connecting to {}:{}...".format(*address))
        self.create_socket()
        self.connect(address)
        asyncore.loop()

    def handle_connect(self):
        log.info("connected")
        log.info("registering as {}...".format(self.nick))
        if self._password:
            self._command("PASS", self._password)
        self._command("NICK", self.nick)
        self._command("USER", self.nick, "0", "*", self.real)

    def _command(self, command, *args):
        """Send a command to the IRC server."""
        message_parts = [command]
        if args:
            args = list(args)
            if " " in args[-1]:
                args[-1] = ":" + args[-1]
            message_parts += args
        self._push(" ".join(message_parts))

    def _push(self, message):
        message = message.encode("utf-8")
        if len(message) > 510:
            newlen = 510
            while message[newlen] & 0xc0 == 0x80:  # UTF-8 continuation byte
                newlen -= 1
            log.warning("truncating message from {} to {} bytes".format(
                len(message), newlen))
            message = message[:newlen]

        log.debug("pushing {}".format(message.decode("utf-8")))
        self.push(message + b"\r\n")

    def message(self, recipient, text):
        """Send a private message to the IRC network.

        :param str recipient: The recipient of the message. Can be a user or a
            channel name.
        :param str text: The text of the private message to send.
        """
        self._command("PRIVMSG", recipient, text)

    def collect_incoming_data(self, data):
        self._incoming.append(data)

    def found_terminator(self):
        message = b"".join(self._incoming).decode("utf-8")
        self._incoming = []

        log.debug("received {}".format(message))
        prefix, command, params = _parse_message(message)
        def _ignore(*args):
            log.debug("ignoring unhandled command {}".format(command))

        getattr(self, "_on_" + command, _ignore)(prefix, params)

    def join(self, *channels):
        """Join IRC channels.

        :param str \*channels: Positional :func:`str` arguments containing
            the channels to join.
        """
        for channel in channels:
            log.info("joining channel {}...".format(channel))
            self._command("JOIN", channel)

    def quit(self, message="Quit"):
        """Terminate the session with the IRC network.

        :param str message: The quit message to send to the IRC network.
        """
        self._command("QUIT", message)

    def handle(self, sender, recipient, text):
        """Handles a private message received from the IRC network.

        An abstract method called when the client received a private message
        from the IRC network. This can be overridden to respond or take some
        action when a private message is received.

        Note that messages sent to a channel are also considered private
        messages.

        Default implementation raises a
        :class:`exceptions.NotImplementedError`.

        :param str sender: The sender of the private message.
        :param str recipient: The recipient of the private message. Either only
            the IRC client or a channel the IRC client is on.
        :param str text: The text contained in the private message.
        """
        raise NotImplementedError("must be implemented in subclass")

    def tick(self):
        """Called on every PING message from the server.

        Default implementation does nothing. Can be overridden to perform
        periodic tasks.
        """
        pass

    def handle_close(self):
        log.info("connection closed")
        self.close()

    # The following functions are invoked when the corresponding command is
    # received from the IRC server.

    def _on_004(self, prefix, params):
        # The server sends Replies 001 to 004 upon successful registration.
        log.info("registered")
        for message in self._autosend:
            self._push(message)
            time.sleep(1)  # give the server time to handle the message
        self.join(*self.channels)
        self._channels = set()  # Will be filled by _on_JOIN with channels
                                # successfully joined.

    def _on_JOIN(self, prefix, params):
        nick, _, _ = split_name(prefix)
        if nick == self.nick:
            log.info("joined channel {}".format(params[0]))
            self.channels.add(params[0])

    def _on_PING(self, prefix, params):
        self._command("PONG", ":" + params[0])
        self.tick()

    def _on_INVITE(self, prefix, params):
        nick, channel = params
        log.info("invited to join channel {} by {}".format(channel, prefix))
        self.join(channel)

    def _on_KICK(self, prefix, params):
        channel, nick, message = params
        if nick == self.nick:
            log.info("kicked from channel {} by {}".format(channel, prefix))
            self.channels.remove(channel)

    def _on_PRIVMSG(self, prefix, params):
        self.handle(prefix, params[0], "".join(params[1:]).lstrip(":"))


def _parse_message(message):
    """Parses the message into a ``(prefix, command, params)`` tuple."""
    # From http://tools.ietf.org/html/rfc2812#section-2.3.1:
    # message = [ ":" prefix SPACE ] command [ params ]
    # params  = *14( SPACE middle ) [ SPACE ":" trailing ]
    #         =/ 14( SPACE middle ) [ SPACE [ ":" ] trailing ]
    prefix = None
    if message.startswith(":"):
        prefix, message = _pop_message(message)
        prefix = prefix[1:]

    command, message = _pop_message(message)

    params = list()
    while message and not message.startswith(":") and len(params) < 14:
        middle, message = _pop_message(message)
        params.append(middle)
    if message:  # trailing
        if message.startswith(":"):
            message = message[1:]
        params.append(message)
    params = tuple(params)  # make params read-only

    return prefix, command, params or None

def _pop_message(message):
    """Pops the top-most space-separated component from the message."""
    if " " in message:
        component, message = message.split(" ", 1)
        return component, message.lstrip(" ")
    return message, ""


def split_name(name):
    nick, rest = name.split("!", 1)
    user, host = rest.split("@", 1)
    return nick, user, host
