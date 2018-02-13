FROM nginx

ENV SERVER_NAME=localhost \
 ESC='$'

COPY django.tmpl /etc/nginx/django.tmpl

RUN mkdir /etc/nginx/sites-enabled
RUN ls -l /etc/nginx/sites-enabled
CMD /bin/bash -c "envsubst < /etc/nginx/django.tmpl > /etc/nginx/sites-enabled/django && nginx -g 'daemon off;' || cat /etc/nginx/sites-enabled/django"
