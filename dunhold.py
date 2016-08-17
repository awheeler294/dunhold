#!/usr/bin/python
#!/usr/bin/env python
#!python
import sys

from src.utilityClasses import QuitException
from src.engine import Controller

try:
    controller = Controller()
    controller.initialize_game()
except QuitException:
    sys.exit()
