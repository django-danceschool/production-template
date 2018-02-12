#!/bin/bash

echo "AVAILABLE IP ADDRESSES\n----------------------"

ifconfig | awk -v RS="\n\n" '{ for (i=1; i<=NF; i++) if ($i == "inet" && $(i+1) ~ /^addr:/) address = substr($(i+1), 6); if (address != "127.0.0.1") printf "%s\t%s\n", $1, address }'

read -p "\nEnter desired Swarm IP address: " ip

# Initialize the Docker Swarm
sudo docker swarm init --advertise-addr $ip

# Generate the DB username and passwords as secrets
openssl rand -base64 20 | sudo docker secret create postgres_user -
openssl rand -base64 20 | sudo docker secret create postgres_password -

# Generate a Django secret key
openssl rand -base64 30 | sudo docker secret create django_secret_key -

PS3='Please select a source for an SSL certificate: '
options=("Provide an SSL Certificate" "Generate Using OpenSSL" "Quit")
select opt in "${options[@]}"
do
    case $opt in
        "Provide an SSL Certificate")
            ;;
        "Generate Using OpenSSL")
            echo "Generating Certificate using OpenSSL"
            openssl genrsa -out "root-ca.key" 4096
            openssl req \
                -new -key "root-ca.key" \
                -out "root-ca.csr" -sha256 \
                -subj '/C=US/ST=CA/L=San Francisco/O=Docker/CN=Swarm Secret Example CA'
            cat <<EOT >> root-ca.cnf
[root_ca]
basicConstraints = critical,CA:TRUE,pathlen:1
keyUsage = critical, nonRepudiation, cRLSign, keyCertSign
subjectKeyIdentifier=hash
EOT

            openssl x509 -req  -days 3650  -in "root-ca.csr" \
                -signkey "root-ca.key" -sha256 -out "root-ca.crt" \
                -extfile "root-ca.cnf" -extensions \
                root_ca
            openssl genrsa -out "site.key" 4096
            openssl req -new -key "site.key" -out "site.csr" -sha256 \
                -subj '/C=US/ST=CA/L=San Francisco/O=Docker/CN=localhost'

            cat <<EOT >> site.cnf
[server]
authorityKeyIdentifier=keyid,issuer
basicConstraints = critical,CA:FALSE
extendedKeyUsage=serverAuth
keyUsage = critical, digitalSignature, keyEncipherment
subjectAltName = DNS:localhost, IP:127.0.0.1
subjectKeyIdentifier=hash
EOT

            openssl x509 -req -days 750 -in "site.csr" -sha256 \
                -CA "root-ca.crt" -CAkey "root-ca.key"  -CAcreateserial \
                -out "site.crt" -extfile "site.cnf" -extensions server
            ;;
        "Quit")
            break
            ;;
        *) echo invalid option;;
    esac
done

# Add SSL certificates information as Docker secrets
docker secret create site.key site.key
docker secret create site.crt site.crt
docker secret create site.conf site.conf