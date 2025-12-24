
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from graphiti_core import Graphiti
import inspect

print(inspect.signature(Graphiti.add_episode))
