"""
Discovery Event Definition
"""


class WatchedEvent:

    def __init__(self, name: str = 'WatchedEvent', func=None):
        self.name = name
        self.func = func


class ServiceWatchedEvent(WatchedEvent):
    """
    A change on Discovery that a Watcher is able to respond to.
    The :class:`ServiceWatchedEvent` declare service has changed for add , del, modified.
    An instance of :class:`ServiceWatchedEvent` will be passed to registered watch functions.
    """

    def __init__(self, func=None):
        super(ServiceWatchedEvent, self).__init__(name='ServiceWatchedEvent', func=func)