#!/usr/bin env python
#pylint: disable=no-member,no-name-in-module

"""
Filesystem interface
"""
import logging
import browsepy
from setproctitle import setproctitle
from greencandle.lib.common import arg_decorator
from greencandle.lib import config

browsepy.app.config.update(
    APPLICATION_ROOT="/data",
    directory_base="/data",
    directory_start="/data"
)

@arg_decorator
def main():
    """
    Web UI for browsing /data dir
    """
    config.create_config()
    setproctitle(f"{config.main.base_env}-filesystem_api")
    logging.basicConfig(level=logging.ERROR)
    if float(config.main.logging_level) > 10:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        log.disabled = True
    browsepy.app.run(host='0.0.0.0', port=6000, debug=False, threaded=True)

if __name__ == '__main__':
    main()
