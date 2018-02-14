#!/bin/bash

# List all available IP addresses, but set the eth0 address as default

echo -e "AVAILABLE IP ADDRESSES\n----------------------"
ifconfig | awk -v RS="\n\n" '{ for (i=1; i<=NF; i++) if ($i == "inet" && $(i+1) ~ /^addr:/) address = substr($(i+1), 6); if (address != "127.0.0.1") printf "%s\t%s\n", $1, address }'
DEFAULT_IP="$(ifconfig eth0 | grep "inet addr" | cut -d ':' -f 2 | cut -d ' ' -f 1)"

read -p "Enter desired Swarm IP address [${DEFAULT_IP}]: " IP
IP=${IP:-$DEFAULT_IP}

read -p "Enter your server's domain and subdomain name(s), separated by spaces. [${DEFAULT_IP}]: " SERVER_NAME
SERVER_NAME=${SERVER_NAME:-$DEFAULT_IP}

# Initialize the Docker Swarm
docker swarm init --advertise-addr $IP

# Generate the DB username and passwords as secrets
POSTGRES_USER=$(< /dev/urandom tr -dc A-Za-z0-9 | head -c${1:-32})
POSTGRES_PASSWORD==$(< /dev/urandom tr -dc A-Za-z0-9 | head -c${1:-32})

echo "${POSTGRES_USER}" | docker secret create postgres_user -
echo "${POSTGRES_PASSWORD}" | docker secret create postgres_password -
echo "postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/danceschool_web" | docker secret create postgres_url -

# Generate a Django secret key
echo $(< /dev/urandom tr -dc A-Za-z0-9 | head -c${1:-32}) | docker secret create django_secret_key -

SSL_SET="false"

# Require an SSL certificate either by having a file provided, or by generating one using OpenSSL
echo -e '\n\nPlease select a source for an SSL certificate:\n'

options=("Provide an SSL Certificate" "Generate Using OpenSSL" "Quit")
select opt in "${options[@]}"
do
    case $opt in
        "Provide an SSL Certificate")
            echo -e "\n"

            read -p "Enter location of SSL certificate (usually *.crt): " PROVIDED_CERT_PATH
            if [ ! -f PROVIDED_CERT_PATH ]; then
                echo "File not found!"
                continue
            fi

            read -p "Enter location of SSL certificate key (usually *.key): " PROVIDED_CERT_KEY_PATH
            if [ ! -f PROVIDED_CERT_KEY_PATH ]; then
                echo "File not found!"
                continue
            fi

            # Add provided SSL information as Docker secrets
            docker secret create site.key $PROVIDED_CERT_KEY_PATH
            docker secret create site.crt $PROVIDED_CERT_PATH

            # Ready to break out of the loop
            break

            ;;
        "Generate Using OpenSSL")
            echo -e "\nGenerating Certificate using OpenSSL\n\n"
            mkdir ./openssl

            # This command will provide the usual prompts for information needed to generate the certificate
            openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout ./openssl/nginx-selfsigned.key -out ./openssl/nginx-selfsigned.crt

            # Add provided SSL information as Docker secrets and remove the OpenSSL files
            docker secret create site.key ./openssl/nginx-selfsigned.key
            docker secret create site.crt ./openssl/nginx-selfsigned.crt
            rm -r ./openssl

            # Ready to break out of the loop
            break

            ;;
        "Quit")
            echo -e "\nUnable to proceed with Docker setup."
            break
            ;;
        *) echo invalid option;;
    esac
done

# Build the Nginx and Gunicorn images so that they can be deployed to the stack
docker build -t danceschool_nginx ./docker/nginx
docker build -f ./docker/web/Dockerfile -t danceschool_web .

# Create the persistent Postgres volume so that we can initialize the database
docker volume create danceschool_postgres
docker run -d --name danceschool_postgres_temp -v danceschool_postgres:/var/lib/postgresql/data postgres:latest
sleep 5;
docker exec danceschool_postgres_temp psql -U postgres -c "CREATE USER ${POSTGRES_USER} PASSWORD '${POSTGRES_PASSWORD}'"
docker exec danceschool_postgres_temp psql -U postgres -c "CREATE DATABASE danceschool_postgres OWNER ${POSTGRES_USER}"
docker stop danceschool_postgres_temp
docker rm danceschool_postgres_temp
