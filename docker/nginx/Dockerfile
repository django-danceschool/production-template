FROM nginx

ENV ESC='$'

COPY django.tmpl /etc/nginx/django.tmpl

RUN mkdir /etc/nginx/sites-enabled
RUN ls -l /etc/nginx/sites-enabled
CMD /bin/bash -c "envsubst < /etc/nginx/django.tmpl > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;' || cat /etc/nginx/conf.d/default.conf"
