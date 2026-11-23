# syntax=docker/dockerfile:1

# A tiny static server for the unlock host.
#
# The base image is chosen for one reason: the console only caches a page for
# offline use when the manifest arrives as `text/cache-manifest`. BusyBox httpd
# needs a config file for that; nginx already ships a mime.types that knows the
# extensions, and the two locations below make it explicit rather than assumed.

FROM nginx:1.27-alpine

RUN printf '%s\n' \
    'server {' \
    '    listen       80;' \
    '    server_name  _;' \
    '    root         /usr/share/nginx/html;' \
    '    index        index.html;' \
    '' \
    '    # The folder names are firmware ranges; a listing helps nobody.' \
    '    autoindex off;' \
    '' \
    '    # Set per location, not as a types block: a second types block' \
    '    # would fight the mime.types that nginx.conf already includes.' \
    '    location ~* \.(manifest|appcache)$ {' \
    '        default_type text/cache-manifest;' \
    '        add_header Cache-Control "no-cache, must-revalidate";' \
    '    }' \
    '' \
    '    location / {' \
    '        try_files $uri $uri/ =404;' \
    '        add_header Cache-Control "no-cache, must-revalidate";' \
    '    }' \
    '}' \
    > /etc/nginx/conf.d/default.conf

COPY . /usr/share/nginx/html

# The repository is not the site: tools, CI and docs do not need to be
# reachable from a console.
RUN rm -rf /usr/share/nginx/html/tools \
           /usr/share/nginx/html/.github \
           /usr/share/nginx/html/.git \
           /usr/share/nginx/html/Dockerfile \
           /usr/share/nginx/html/docker-compose.yml \
           /usr/share/nginx/html/.dockerignore

# Normalise modes. A checkout made under a restrictive umask (0077 is common on
# servers) arrives as 0600, and nginx runs as another user: it answers 403 for
# files that exist, which looks exactly like a missing page. Do not rely on the
# mode the files happened to have here.
RUN find /usr/share/nginx/html -type d -exec chmod 755 {} + \
    && find /usr/share/nginx/html -type f -exec chmod 644 {} +

EXPOSE 80
