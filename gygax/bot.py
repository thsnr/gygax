# -*- coding: utf-8 -*-

import logging

import gygax.irc
import gygax.modules

log = logging.getLogger(__name__)

class Bot(gygax.irc.Client):

    """A concrete implementation of :class:`gygax.irc.Client` which supports
    configuration and dynamically loadable modules.
    """

    def __init__(self, **config):
        """Creates a new IRC bot and initializes it from config."""
        super().__init__(config["bot"]["nick"], config["bot"]["real"])
        self._config = config
        self._commands = {}
        self._ticks = {}
        self._tick_count = 0

        for module in config["bot"].get("modules", "").split():
            self._load_module(module)

    def run(self):
        """Connect to the IRC server and start the bot."""
        config = self._config["bot"]
        autosend = config.get("autosend")
        if autosend:
            # autosend commands are semicolon-separated; strip any surrounding
            # whitespace and drop empty commands.
            autosend = autosend.split(";")
            autosend = map(lambda s: s.strip(), autosend)
            autosend = filter(None, autosend)

        super().run((config["server"], int(config["port"])),
                channels=config.get("channels", "").split() or None,
                password=config.get("password"),
                autosend=autosend or None)

    def _load_module(self, name):
        try:
            module = gygax.modules.load_module(name)
            self._bind(module)
            log.info("loaded module {}".format(name))
            return True
        except Exception as e:
            log.exception("failed to load module {}: {}".format(name, e))
            return False

    def _bind(self, module):
        if hasattr(module, "reset"):
            module.reset(self, self._config.get("module_" + module.__name__))
        for _, func in vars(module).items():
            if hasattr(func, "command"):
                log.debug("binding {} to {}".format(func.command, func.__name__))
                self._commands[func.command] = func
            if hasattr(func, "tick"):
                log.debug("calling {} after every {} tick(s)".format(func.__name__, func.tick))
                if module in self._ticks:
                    self._ticks[module.__name__].append(func)
                else:
                    self._ticks[module.__name__] = [func]

    def handle(self, sender, recipient, text):
        def reply(text):
            if recipient == self.nick:
                nick, _, _ = gygax.irc.split_name(sender)
                self.message(nick, text)
            else:
                self.message(recipient, text)
        self.reply = reply

        for command, func in self._commands.items():
            if text == command or text.startswith(command + " "):
                args = text[len(command):].strip()
                try:
                    func(self, sender, args)
                except Exception as e:
                    log.exception("{} failed: {}".format(command, e))
                    self.reply("something went wrong")
                finally:
                    break

    def tick(self):
        self._tick_count += 1
        for module, funcs in self._ticks.items():
            for func in funcs:
                if self._tick_count % func.tick == 0:
                    try:
                        func(self)
                    except Exception as e:
                        log.exception("ticking {}.{} failed: {}".format(module, func.__name__, e))
