# Copyright (c) Microsoft. All rights reserved.

# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

import os, threading, json, time, socket
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib
from socketserver import ThreadingMixIn
from datetime import datetime
from base64 import b64encode, b64decode
from evaluator import get_results

def log(msg):
    return "[%s] %s" % (datetime.now(), str(msg))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class Server(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', "*")
        self.send_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept")
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def _set_img_headers(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', "*")
        self.send_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept")
        self.send_header('Content-type', 'image/png')
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', "*")
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept")
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        results = {'status':False, 'results':[], 'verbose':None}
        received = str(int(time.time()*1000))
        self._set_img_headers()
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        content_type = 'png' if ('png' in self.headers['Content-Type']) else 'jpg'
        try:
            raw_data = self.rfile.read(content_length) # <--- Gets the data itself
            data = json.loads(raw_data.decode('utf8'))["input_df"][0]['image base64 string']
        except Exception as err:
            print("[ERROR]", err)
            return

        results["results"] = get_results(self.evaluator, data, self.cfg)
        results["status"] = True
        results["verbose"] = {
          'received': received,
          'resloved': str(int(time.time()*1000)),
          'host': socket.gethostname()
        }
        self.wfile.write(bytes(json.dumps(results), "utf8"))
        
    @classmethod
    def bind_evaluator(self, _evaluator,  _cfg):
        self.evaluator = _evaluator
        self.cfg = _cfg
