
"""
Filesystem interface
"""

import browsepy

browsepy.app.config.update(
    APPLICATION_ROOT="/data",
    directory_base="/data",
    directory_start="/data"
)

def main():
    """
    Web UI for browsing /data dir
    """
    browsepy.app.run(host='0.0.0.0', port=6000, debug=True, threaded=True)

if __name__ == '__main__':
    main()
