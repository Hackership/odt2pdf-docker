# odt2pdf

Microservice to render POD-Templated ODT-Files into PDFs given the contextual data.

## Features:

 - simple API to render ODT to PDF files
 - super tiny (less than 120 lines of python)
 - simple API_KEY-environment-variable to keep things secret
 - support for appy-pod templates
 - downloads the file for you
 - etag-based caching support

### Features of Docker:

 - fully stand-alone microservice
 - includes libreoffice-backend
 - includes all necessary python requirements
 - includes caching backend based on literedis
 - includes supervisord for both libre-office service and flask app
 - exposes port 5000 for your convinence

## API

It's a post to /render/template/API_KEY with a json payload looking like this:

    {
        template: {
            url: "http://something.com/file.odt",
            headers: {
                // optional headers to pass through to requests
                "X-AUTH-EXTRA": "SECRECT"
            },
            // any extra data is passed to the requests.get
            auth: ["A", "B"]
        },
        format: "PDF",
        // optional support for the target format. Default: PDF.

    }


## deploy

Easiest to just deploy with docker. Just run the following:

    export API_KEY=`tr -dc A-Za-z0-9_ < /dev/urandom | head -c 16 | xargs`
    docker run --name odt2pdf -p 5000:5000 -e API_KEY=$API_KEY hackership/odt2pdf
    echo "You can now access your odt2pdf server at http://localhost:5000/"
    echo "And the API key is $API_KEY"

