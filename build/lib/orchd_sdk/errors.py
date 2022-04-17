class InvalidInputError(Exception):
    """
    Invalid input given.
    """


class ReactorError(Exception):
    """Raise on internal Errors in the Reactor."""


class SinkError(Exception):
    """ Raised on Sink errors."""


class ReactionError(Exception):
    """ Raised on Reaction Management and Operation errors."""


class ReactionHandlerError(Exception):
    """ Raised by ReactionHandler implementations."""
