# -*- coding: utf-8 -*-

import imp
import os
import os.path

def list_modules():
    return " ".join(map(lambda fn: fn[:-3],
            filter(lambda fn: fn.endswith(".py") and not fn.startswith("_"),
                os.listdir(os.path.dirname(__file__)))))

def load_module(module):
    path = os.path.join(os.path.dirname(__file__), module + ".py")
    return imp.load_source(module, path)
