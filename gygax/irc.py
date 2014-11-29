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

    @property
    def password(self):
        """The connection password used."""
        return self._password

    def __init__(self, nick, real):
        """Creates a new IRC client and initializes its attributes."""
        super().__init__()
        self.set_terminator(b"\r\n")
        self._incoming = []

        self._nick = nick
        self._real = real
        self._channels = set()
        self._password = None

    def run(self, address, channels=None, password=None):
        """Connect to an IRC server and start the client's main loop.

        :param tuple address: A tuple ``(host, port)`` with the address of the
            IRC server to connect to.
        :param iter channels: The list of channels to join on startup.
        :param str password: The optional connection password to use.
        """
        self._channels = channels or self.channels
        self._password = password or self.password

        print("Connecting to {}:{}...".format(*address), end="", flush=True)
        self.create_socket()
        self.connect(address)
        asyncore.loop()

    def handle_connect(self):
        print("connected!")
        print("Registering...", end="", flush=True)
        if self.password:
            self._command("PASS", self.password)
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

        message = " ".join(message_parts).encode("utf-8")
        if len(message) > 510:
            message = message[:510]
            print("WARNING: Truncated too long message: {}".format(message))

        print("DEBUG: pushing {}".format(message))
        self.push(message + b"\r\n")

    def message(self, recipient, text):
        """Send a private message to the IRC network.

        :param str recipient: The recipient of the message. Can be a user or a
            channel name.
        :param str text: The text of the private message to send.
        """
        self._command("PRIVMSG", recipient, text)

    def collect_incoming_data(self, data):
        self._incoming.append(data.decode("utf-8"))

    def found_terminator(self):
        message = "".join(self._incoming)
        self._incoming = []

        print("DEBUG: received {}".format(message))
        prefix, command, params = _parse_message(message)
        def _ignore(*args):
            print("DEBUG: Ignoring unhandled command {}".format(command))

        getattr(self, "_on_" + command, _ignore)(prefix, params)

    def join(self, *channels):
        """Join IRC channels.

        :param str \*channels: Positional :func:`str` arguments containing
            the channels to join.
        """
        for channel in channels:
            print("Joining channel {}...".format(channel), end="", flush=True)
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

    def handle_close(self):
        print("Connection closed!")
        self.close()

    # The following functions are invoked when the corresponding command is
    # received from the IRC server.

    def _on_004(self, prefix, params):
        # The server sends Replies 001 to 004 upon successful registration.
        print("registered!")
        self.join(*self.channels)
        self._channels = set()  # Will be filled by _on_JOIN with channels
                                # successfully joined.

    def _on_JOIN(self, prefix, params):
        print("joined!")
        self.channels.add(params[0])

    def _on_PING(self, prefix, params):
        self._command("PONG", ":" + params[0])

    def _on_INVITE(self, prefix, params):
        nick, channel = params
        print("Invited to join channel {} by {}".format(channel, prefix))
        self.join(channel)

    def _on_KICK(self, prefix, params):
        channel, nick, message = params
        if nick == self.nick:
            print("Kicked from channel {} by {}".format(channel, prefix))
            self.channels.remove(channel)

    def _on_PRIVMSG(self, prefix, params):
        self.handle(prefix, params[0], "".join(params[1:]).lstrip(":"))


def _parse_message(message):
    """Parses the message into a ``(prefix, command, params)`` tuple."""
    # From http://tools.ietf.org/html/rfc2812#section-2.3.1:
    # message = [ ":" prefix SPACE ] command [ params ]
    prefix = None
    if message.startswith(":"):
        prefix, message = message[1:].split(" ", 1)

    command = message
    params = None
    if " " in message:
        command, params = message.split(" ", 1)

    # params = *14( SPACE middle ) [ SPACE ":" trailing ]
    #        =/ 14( SPACE middle ) [ SPACE [ ":" ] trailing ]
    # Note that we already removed the first SPACE of params.
    if params:
        if params.startswith(":"):
            params = (params[1:],)
        elif " :" in params:
            middles, trailing = params.split(" :", 1)
            params = middles.split(" ") + [trailing]
        else:
            params = params.split(" ", 14)
            if params[-1].startswith(":"):
                params[-1] = params[-1][1:]  # strip the optional ":"
        params = tuple(params)  # make params read-only

    return prefix, command, params

def split_name(name):
    nick, rest = name.split("!", 1)
    user, host = rest.split("@", 1)
    return nick, user, host
