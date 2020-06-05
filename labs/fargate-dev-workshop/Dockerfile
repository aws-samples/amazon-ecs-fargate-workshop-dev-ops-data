FROM httpd:latest

RUN apk -q add libcap

#Change access righs to conf, logs, bin from root to www-data
RUN chown -hR www-data:www-data /usr/local/apache2/

#setcap to bind to privileged ports as non-root
RUN setcap 'cap_net_bind_service=+ep' /usr/local/apache2/bin/httpd
RUN getcap /usr/local/apache2/bin/httpd

COPY ./app/ /usr/local/apache2/htdocs/

#Run as a www-data
USER www-data
