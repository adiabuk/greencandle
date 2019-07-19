#!/usr/bin/env python

import sys
import os
from flask import Flask, send_file, abort
FLASK_APP = Flask(__name__)

@FLASK_APP.route('/<path:path>', methods=['GET'])
def return_file(path):
    sys.stderr.write(path)
    if path.startswith('graphs/') and path.endswith('.png') and os.path.isfile(path):
        return send_file(path, as_attachment=True)
    else:
        abort(404)

def main():
    FLASK_APP.run(debug=True, port=5002)

main()
