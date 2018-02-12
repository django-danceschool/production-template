FROM tutum/nginx

RUN rm /etc/nginx/sites-enabled/default

ENV LISTEN_PORT=80 \
  SERVER_NAME=_ \
  ESC='$'

COPY django.tmpl /etc/nginx/django.tmpl

CMD /bin/sh -c "envsubst < /etc/nginx/django.tmpl > /etc/nginx/sites-enabled/django && nginx -g 'daemon off;' || cat /etc/nginx/sites-enabled/django"