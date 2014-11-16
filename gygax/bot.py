# -*- coding: utf-8 -*-

import gygax.irc
import gygax.modules

class Bot(gygax.irc.Client):

    """A concrete implementation of :class:`gygax.irc.Client` which supports
    configuration and dynamically loadable modules.
    """

    def __init__(self, **config):
        """Creates a new IRC bot and initializes it from config."""
        super().__init__(config["nick"], config["real"])
        self._config = config
        self._commands = {}

        for module in config["modules"].split(" "):
            self._load_module(module)

    def run(self):
        """Connect to the IRC server and start the bot."""
        super().run((self._config["server"], int(self._config["port"])),
                self._config["channels"].split(" "), self._config["password"])

    def _load_module(self, name):
        try:
            module = gygax.modules.load_module(name)
        except Exception as e:
            print("Failed to load module {}: {}".format(name, e))
            return False
        else:
            self._bind(module)
            print("Loaded module", name)
            return True

    def _bind(self, module):
        if hasattr(module, "reset"):
            module.reset(self, self._config)
        for _, func in vars(module).items():
            if hasattr(func, "command"):
                print("Binding", func.command, "to", func.__name__)
                self._commands[func.command] = func

    def handle(self, sender, recipient, text):
        def reply(text):
           if recipient == self.nick:
               self.message(sender, text)
           else:
               self.message(recipient, text)
        self.reply = reply

        for command, func in self._commands.items():
            if text.startswith(command):
                args = text[len(command):].strip()
                try:
                    func(self, sender, args)
                except Exception as e:
                    print("Error:", func.__name__, "failed:", e)
                    self.reply("something went wrong")
                finally:
                    break
