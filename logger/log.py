"""Logging support for aioms.
aioms uses three logger streams:

* ``aioms.access``: request logging for aioms's HTTP servers
* ``aioms.application``: Logging of errors from application code
* ``aioms.general``: General-purpose logging, including any errors or warnings from aioms itself.

These streams may be configured independently using the standard library's
`logging` module.  For example, you may wish to send ``aioms.access`` logs to a separate file for analysis.
"""


import logging

access_log = logging.getLogger("aioms.access")
app_log = logging.getLogger("aioms.application")
gen_log = logging.getLogger("aioms.general")