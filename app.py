from __future__ import with_statement

from flask import Flask, request, abort, send_file
from redislite import Redis
from contextlib import closing
from appy.pod.renderer import Renderer
import requests
import logging
import os
import tempfile
import sys

app = Flask("Odt2Pdf")
redis = Redis("odt2pdf.db")
# log to stderr
app.logger.setLevel(logging.WARNING)
app.logger.addHandler(logging.StreamHandler())

warn = app.logger.warning

APP_KEY = os.environ.get("APP_KEY")

UNOPYTHON = os.environ.get("UNOPYTHON", "")

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
                abort(400, "Received a non 200 response when downloading template: {}".format(r.status_code))


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

    return tmp_name


@app.route("/")
def hello():
    return """<html><head>
<title>ODT 2 PDF Microservice</title>
<style>
body {
  padding: 25vh 20vw;
  font-family: Helvetica Neue, Helvetica, sans-serif;
}
</style>
</head>
<body>
<h1>Congrats, it's up!</h1>
<p>This is the <a href="https://github.com/hackership/odt2pdf/">odt2pdf</a> Microservice (based on docker), allowing you to easily render ODT-Files with <a href="http://www.appyframework.org/pod.html" target="_blank">POD-Template</a> information into fully fledged PDFs.</p>
<p>This is a private instance and can only accessed with the knowledge of the <pre>API_KEY</pre>, but if you want to create your own its rather easy. Just follow the steps described <a href="https://github.com/hackership/odt2pdf/#deploy">here</a>.

</body>
</html>
"""

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

    suffix = payload.get("format", "pdf")

    template = _fetch_template(**payload['template'])

    fd, target = tempfile.mkstemp(suffix=".{}".format(suffix))
    os.close(fd)
    os.remove(target)

    try:
        # FIXME: we are not cleaning up our target documents, are we?
        r = Renderer(template, context, target,
                     pythonWithUnoPath=UNOPYTHON,
                     forceOoCall=True,
                     overwriteExisting=True)
        r.run()

        return send_file(target, as_attachment=True)
    finally:
        try:
            os.remove(target)
        except:
            pass



if __name__ == "__main__":
    app.debug = True
    app.run()