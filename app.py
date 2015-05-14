from __future__ import with_statement

from flask import Flask, request, abort, Response
from redislite import Redis
from contextlib import closing
import requests
import logging
import os
import tempfile
import sys
import json

from genshi.core import Markup

app = Flask("Odt2Pdf")
redis = Redis("odt2pdf.db")
# log to stderr
app.logger.setLevel(logging.WARNING)
app.logger.addHandler(logging.StreamHandler())

warn = app.logger.warning

APP_KEY = os.environ.get("APP_KEY")
FUSION_URL = os.environ.get("FUSION_URL", 'http://localhost:8765/form')

def format_with_linebreaks(inp):
    return json.dumps(inp)
    # .replace("\n", "\000A")

if not APP_KEY:
    print("You need to set the APP_KEY environment variable!")
    sys.exit(1)

def _fetch_template(url=False, headers=None, **kwargs):
    if not url:
        abort(400, "Your 'template' doesn't have any url ...")

    headers = dict() if headers is None else headers
    tmp_name = redis.get("{}".format(url))
    if redis.get("etag_{}".format(url)):
        headers['If-None-Match'] = redis.get("etag_{}".format(url))

    with closing(requests.get(url, stream=True, headers=headers, **kwargs)) as r:
        if r.status_code not in [204, 304]:
            # if we received a no-content or not-modified, we assume we are still up to date
            if r.status_code != 200:
                abort(400, "Received a non 200 response when downloading template: {}".format(r.status))


            # we have a new one, download it
            fd, filename = tempfile.mkstemp(suffix=".odt")
            for l in r.iter_content(1024):
                os.write(fd, l)

            os.close(fd)

            # and update the db
            redis.set("{}".format(url), filename)
            redis.set("etag_{}".format(url), r.headers.get("etag", None))
            if tmp_name:
                try:
                    os.remove(tmp_name)
                except:
                    pass
            tmp_name = filename

    print(tmp_name)
    return tmp_name



@app.route('/render/template/{}'.format(APP_KEY), methods=["POST"])
def render_template():
    # we are expecting a json payload
    payload = request.get_json()
    if not payload:
        abort(400, "No JSON content found")

    try:
        context = payload["context"]
    except KeyError:
        abort(400, "No context, no document!")


    try:
        reader = open(_fetch_template(**payload['template']), 'rb')

        # finally POST our request on the endpoint
        req = requests.post(FUSION_URL,
                          data={
                                "targetformat": payload.get("format", "ODT"),
                                "datadict": format_with_linebreaks(payload["context"]),
                                "image_mapping": "{}" },
                          files={'tmpl_file': reader},
                          stream=True)

        # don't forget to close our orginal odt file
    finally:
        reader.close()

    # see if it is a success or a failure
    # ATM the server only returns 400 errors... this may change
    if req.status_code > 400:
        abort(req.status_code, description="Rendering failed: {}".format(req.content))

    return Response(req.content, mimetype=req.headers['content-type'], headers={"Content-Disposition": "attachment"})



if __name__ == "__main__":
    app.debug = True
    app.run()