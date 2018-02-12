#!/bin/bash

# List all available IP addresses, but set the eth0 address as default

echo "AVAILABLE IP ADDRESSES\n----------------------"
ifconfig | awk -v RS="\n\n" '{ for (i=1; i<=NF; i++) if ($i == "inet" && $(i+1) ~ /^addr:/) address = substr($(i+1), 6); if (address != "127.0.0.1") printf "%s\t%s\n", $1, address }'
DEFAULT_IP="$(ifconfig eth0 | grep "inet addr" | cut -d ':' -f 2 | cut -d ' ' -f 1)"

read -p "\nEnter desired Swarm IP address [${DEFAULT_IP}]: " IP || IP="${DEFAULT_IP}"

read -p "\nEnter your server's domain and subdomain name(s), separated by spaces. [${DEFAULT_IP}]: "

# Initialize the Docker Swarm
docker swarm init --advertise-addr $IP

# Generate the DB username and passwords as secrets
POSTRES_USER=$(openssl rand -base64 20) 
POSTGRES_PASSWORD=$(openssl rand -base64 20)

docker secret create postgres_user $POSTRES_USER
docker secret create postgres_password $POSTGRES_PASSWORD
docker secret create postgres_url "postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/danceschool_web"

# Generate a Django secret key
openssl rand -base64 30 | docker secret create django_secret_key -

SSL_SET=false

# Require an SSL certificate either by having a file provided, or by generating one using OpenSSL
while [! $SSL_SET ]


PS3='\nPlease select a source for an SSL certificate: '
options=("Provide an SSL Certificate" "Generate Using OpenSSL" "Quit")
select opt in "${options[@]}"
do
    case $opt in
        "Provide an SSL Certificate")
            read -p "\nEnter location of SSL certificate (usually *.crt): " PROVIDED_CERT_PATH
            if [ ! -f PROVIDED_CERT_PATH ]; then
                echo "File not found!"
                continue
            fi

            read -p "\nEnter location of SSL certificate key (usually *.key): " PROVIDED_CERT_KEY_PATH
            if [ ! -f PROVIDED_CERT_KEY_PATH ]; then
                echo "File not found!"
                continue
            fi

            # Add provided SSL information as Docker secrets
            docker secret create site.key $PROVIDED_CERT_KEY_PATH
            docker secret create site.crt $PROVIDED_CERT_PATH

            # Ready to break out of the loop
            SSL_SET=true
            ;;
        "Generate Using OpenSSL")
            echo "Generating Certificate using OpenSSL"
            mkdir ./openssl

            # This command will provide the usual prompts for information needed to generate the certificate
            openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout ./openssl/nginx-selfsigned.key -out ./openssl/nginx-selfsigned.crt

            # Add provided SSL information as Docker secrets and remove the OpenSSL files
            docker secret create site.key ./openssl/nginx-selfsigned.key
            docker secret create site.crt ./openssl/nginx-selfsigned.crt
            rm -r ./openssl

            # Ready to break out of the loop
            SSL_SET=true
            ;;
        "Quit")
            echo "\nUnable to proceed with Docker setup."
            break
            ;;
        *) echo invalid option;;
    esac
done