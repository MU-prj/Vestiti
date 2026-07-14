"""Camerino adapters package: pluggable interfaces to the outside world.

All external I/O (product sources, try-on providers, checkout, notifications)
goes through the interfaces defined here. CI only ever exercises mock
implementations; real implementations sit behind credentials.
"""

__version__ = "0.1.0"
