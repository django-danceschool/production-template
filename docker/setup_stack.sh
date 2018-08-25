#!/bin/bash

swarm_initialize () {
    # Initializes a new Docker Swarm if that is necessary.
    SWARM_EXISTS=$(docker swarm ca > /dev/null 2>&1 && echo 1 || echo 0)
    if [ $SWARM_EXISTS -lt 1 ]; then
        echo -e "AVAILABLE IP ADDRESSES\n----------------------"
        ifconfig | awk -v RS="\n\n" '{ for (i=1; i<=NF; i++) if ($i == "inet" && $(i+1) ~ /^addr:/) address = substr($(i+1), 6); if (address != "127.0.0.1") printf "%s\t%s\n", $1, address }'
        DEFAULT_IP="$(ifconfig eth0 | grep "inet addr" | cut -d ':' -f 2 | cut -d ' ' -f 1)"

        read -p "Enter desired Swarm IP address [${DEFAULT_IP}]: " IP
        IP=${IP:-$DEFAULT_IP}

        # Initialize the Docker Swarm
        docker swarm init --advertise-addr $IP

        echo "Docker Swarm successfully initialized."
    else
        echo "Docker Swarm already exists."
    fi
}

create_volumes () {
    # Create volumes for static files, uploaded media, and the Postgres database.
    # Docker volumes can be created repeatedly without consequence, so this requires
    # no condition checks.

    echo -e "Ensuring that Docker volumes exist."

    docker volume create danceschool_postgres
    docker volume create danceschool_staticfiles
    docker volume create danceschool_media
    docker volume create danceschool_privatemedia
    docker volume create danceschool_certs
}

create_postgres_secrets () {
    DB_EXISTS=$(docker exec danceschool_postgres_temp psql -U postgres -c "\list"| grep -c "danceschool_postgres")

    POSTGRES_USER=$(< /dev/urandom tr -dc a-z | head -c${1:-32})
    echo "${POSTGRES_USER}" | docker secret create postgres_user -

    POSTGRES_PASSWORD==$(< /dev/urandom tr -dc A-Za-z0-9 | head -c${1:-32})
    echo "${POSTGRES_PASSWORD}" | docker secret create postgres_password -

    echo "postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/danceschool_postgres" | docker secret create postgres_url -

    # Create the Postgres user based on the new credentials
    docker exec danceschool_postgres_temp psql -U postgres -c "CREATE USER ${POSTGRES_USER} PASSWORD '${POSTGRES_PASSWORD}'"

    if [ $DB_EXISTS -ge 1 ] ; then
        docker exec danceschool_postgres_temp psql -U postgres -c "ALTER DATABASE danceschool_postgres OWNER TO ${POSTGRES_USER}"
        docker exec danceschool_postgres_temp psql -U postgres -d danceschool_postgres -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${POSTGRES_USER}"
        docker exec danceschool_postgres_temp psql -U postgres -d danceschool_postgres -c "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ${POSTGRES_USER}"
    else
        docker exec danceschool_postgres_temp psql -U postgres -c "CREATE DATABASE danceschool_postgres OWNER ${POSTGRES_USER}"            
    fi

}


check_postgres_secrets () {
    echo -e "\nCreating Postgres and secret key secrets if they do not already exist."

    # Get the list of existing secrets to see if new ones need to be created/updated
    EXISTING_SECRET_LIST="$(docker secret ls)"

    # Persistent data volumes can be created repeatedly with no ill effects, so ensure at the outset
    # that the volume for the Postgres data exists.
    docker volume create danceschool_postgres
    docker run -d --name danceschool_postgres_temp -v danceschool_postgres:/var/lib/postgresql/data postgres:latest
    sleep 3;

    # These need to be checked individually first in case some are specified and others are not.
    POSTGRES_USER_EXISTS=$(grep -c "postgres_user" <<< $EXISTING_SECRET_LIST)
    POSTGRES_PASSWORD_EXISTS=$(grep -c "postgres_password" <<< $EXISTING_SECRET_LIST)
    POSTGRES_URL_EXISTS=$(grep -c "postgres_url" <<< $EXISTING_SECRET_LIST)
    DB_EXISTS=$(docker exec danceschool_postgres_temp psql -U postgres -c "\list"| grep -c "danceschool_postgres")

    # Remove all existing secrets unless all three are specified
    if [ $POSTGRES_USER_EXISTS -lt 1 ] || [ $POSTGRES_PASSWORD_EXISTS -lt 1 ] || [ $POSTGRES_URL_EXISTS -lt 1 ] || [ $DB_EXISTS -lt 1 ]; then

        echo "Postgres credentials do not exist or database does not exist. Preparing to create new credentials."

        if [ $POSTGRES_USER_EXISTS -ge 1 ] ; then
            docker secret rm postgres_user
        fi
        if [ $POSTGRES_USER_EXISTS -ge 1 ] ; then
            docker secret rm postgres_password
        fi
        if [ $POSTGRES_URL_EXISTS -ge 1 ] ; then
            docker secret rm postgres_url
        fi

        create_postgres_secrets

    else
        read -p "Postgres credentials and database exist. Replace credentials? [y/N] " -n 1 -r
        if [[ $REPLY =~ ^[Yy]$ ]] ; then
            docker secret rm postgres_user
            docker secret rm postgres_password
            docker secret rm postgres_url

            create_postgres_secrets
        fi
    fi

    docker stop danceschool_postgres_temp
    docker rm danceschool_postgres_temp

    echo "Finished check Postgres connection."

}

check_secret_key () {
    KEY_EXISTS=$(grep -c "django_secret_key" <<< $EXISTING_SECRET_LIST)

    # Generate a Django secret key
    if [ $KEY_EXISTS -ge 1 ] ; then
        read -p "Django secret key already exists. Replace it? [y/N] " -n 1 -r
        if [[ $REPLY =~ ^[Yy]$ ]] ; then
            docker secret rm django_secret_key
        else
            return
        fi
    else
        echo "Generating Django secret key."
    fi

    echo $(< /dev/urandom tr -dc A-Za-z0-9 | head -c${1:-32}) | docker secret create django_secret_key -

}

create_ssl_certs () {

    # Disable LetsEncrypt unless it is chosen.
    LETSENCRYPT_ENABLED=0

    # Require an SSL certificate either by having a file provided, or by generating one using OpenSSL
    echo -e 'Please select a source for an SSL certificate:\n'

    options=("Use built-in LetsEncrypt (recommended for production)" "Provide an SSL Certificate" "Generate Using OpenSSL (for testing only)" "Quit")
    select opt in "${options[@]}"
    do
        case $opt in
            "Use built-in LetsEncrypt (recommended for production)")

                echo -e "\nPLEASE NOTE: In order to use LetsEncrypt for an automatically-generated SSL "
                echo -e "certificate, you must edit the following items in the file env.web:"
                echo -e "\n - VIRTUAL_HOST\n - LETSENCRYPT_HOST\n - LETSENCRYPT_EMAIL.\n"
                echo -e "\nAdditionally, note that you MUST have a publicly accessible website hostname "
                echo -e "(e.g. yourdomain.com), or else LetsEncrypt will fail, and you will need to run "
                echo -e "this script again."

                LETSENCRYPT_ENABLED=1

                # Ready to break out of the loop
                break

                ;;

            "Provide an SSL Certificate")
                echo -e "\n"

                read -p "Enter location of SSL certificate (usually *.crt): " PROVIDED_CERT_PATH
                if [ ! -f $PROVIDED_CERT_PATH ]; then
                    echo "File not found!"
                    continue
                fi

                read -p "Enter location of SSL certificate key (usually *.key): " PROVIDED_CERT_KEY_PATH
                if [ ! -f $PROVIDED_CERT_KEY_PATH ]; then
                    echo "File not found!"
                    continue
                fi

                # Add provided SSL information into Docker volume
                docker cp $PROVIDED_CERT_KEY_PATH check_ssl:/certs/nginx-provided.key
                docker cp $PROVIDED_CERT_PATH check_ssl:/certs/nginx-provided.crt

                # Ready to break out of the loop
                break

                ;;
            "Generate Using OpenSSL (for testing only)")
                echo -e "\nGenerating Certificate using OpenSSL\n\n"
                mkdir ./openssl

                # This command will provide the usual prompts for information needed to generate the certificate
                openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout ./openssl/nginx-selfsigned.key -out ./openssl/nginx-selfsigned.crt

                # Copy the certificate
                docker cp ./openssl/nginx-selfsigned.key check_ssl:/certs/nginx-selfsigned.key
        		docker cp ./openssl/nginx-selfsigned.crt check_ssl:/certs/nginx-selfsigned.crt
                rm -r ./openssl

                # Ready to break out of the loop
                break

                ;;
            "Quit")
                echo -e "\nUnable to proceed with Docker setup."
                exit 1
                ;;
            *) echo invalid option;;
        esac
    done
}

check_ssl_certs () {
    # If the SSL certificates changed, then the Nginx image must be rebuilt.
    SSL_CHANGED=0

    # Begin a container that will be used to check for the existence of SSL certificates and
    # that will replace them if necessary.
    docker run --rm -d --name check_ssl -v danceschool_certs:/certs alpine top

    # Check if a provided certificate exists.
    SSL_CERT_EXISTS=$(docker exec check_ssl ls /certs | grep -c "nginx-(provided|selfsigned)\.crt")
    SSL_KEY_EXISTS=$(docker exec check_ssl ls /certs | grep -c "nginx-(provided|selfsigned)\.key")

    if [ $SSL_CERT_EXISTS -lt 1 ] || [ $SSL_KEY_EXISTS -lt 1 ] ; then
        if [ $SSL_CERT_EXISTS -ge 1 ] ; then
            docker exec check_ssl rm /certs/nginx-provided.crt
        fi

        if [ $SSL_KEY_EXISTS -ge 1 ] ; then
            docker exec check_ssl rm /certs/nginx-provided.key
        fi

        # TODO: Check if LetsEncrypt is currently being used here.

        echo -e 'Existing SSL credentials not found or are incomplete.\n'
        SSL_CHANGED=1
        create_ssl_certs

    else
        read -p "Existing provided SSL credentials found. Replace them? [y/N] " -n 1 -r
        if [[ $REPLY =~ ^[Yy]$ ]] ; then
            docker exec check_ssl rm /certs/nginx-provided.crt
            docker exec check_ssl rm /certs/nginx-provided.key
            SSL_CHANGED=1
            create_ssl_certs
            echo -e "\n"
        fi

    fi

    # Close the container that has been used to check and copy SSL certs
    docker stop check_ssl
}

build_nginx () {
    IMAGE_EXISTS=$(docker images | grep -c danceschool_nginx)

    if [ $IMAGE_EXISTS -ge 1 ] && [ $SSL_CHANGED -eq 0 ] ; then
        echo -e "\n"
        read -p "Nginx image exists. Rebuild it? [y/N] " -n 1 -r
        if [[ $REPLY =~ ^[Yy]$ ]] ; then
            echo 
        else
            echo 
            return
        fi
    fi

    echo "Preparing to build Nginx image."
    docker build --no-cache --build-arg LETSENCRYPT_ENABLED=$LETSENCRYPT_ENABLED -t danceschool_nginx ${BASH_SOURCE%/*}/nginx
    echo "Nginx image built successfully."
}

build_web () {
    IMAGE_EXISTS=$(docker images | grep -c danceschool_web)

    if [ $IMAGE_EXISTS -ge 1 ] ; then
        echo -e "\n"
        read -p "Django image exists. Rebuild it? [y/N] " -n 1 -r
        if [[ $REPLY =~ ^[Yy]$ ]] ; then
            echo 
        else
            echo 
            return
        fi
    fi

    echo "Preparing to build Django image. This may take a few minutes."
    docker build --no-cache -f ${BASH_SOURCE%/*}/web/Dockerfile -t danceschool_web .
    echo "Django image built successfully."
}


database_setup () {
    echo -e "Deploying a shell-only stack for initial setup of the database.\n"
    docker stack deploy -c ${BASH_SOURCE%/*}/docker-compose-shellonly.yml danceschool_shellonly
    sleep 3;

    # Get the name of the active web container so that we can run migrations if requested.
    CONTAINER_NAME=$(docker ps | grep "danceschool_shellonly_web\.1" | awk '{ print $1;}')

    read -p "Run database migrations? [Y/n] " -n 1 -r
    if [[ $REPLY =~ ^[Nn]$ ]] ; then
        echo 
    else
        echo -e "\nInitializing database migrations. This may take a minute."
        docker exec $CONTAINER_NAME python3 manage.py migrate
        echo
    fi

    read -p "Collect static files for Nginx to serve? [Y/n] " -n 1 -r
    if [[ $REPLY =~ ^[Nn]$ ]] ; then
        echo 
    else
        echo -e "\nCollecting static files. This may take a minute."
        docker exec $CONTAINER_NAME python3 manage.py collectstatic --no-input
        echo
    fi

    read -p "Create a new superuser account? [Y/n] " -n 1 -r
    if [[ $REPLY =~ ^[Nn]$ ]] ; then
        echo 
    else
        echo
        docker exec -it $CONTAINER_NAME python3 manage.py createsuperuser
        echo
    fi

    read -p "Run the setupschool script? [Y/n] " -n 1 -r
    if [[ $REPLY =~ ^[Nn]$ ]] ; then
        echo 
    else
        echo
        docker exec -it $CONTAINER_NAME python3 manage.py setupschool
        echo
    fi

    # Now that the database is setup, shut down the stack
    docker stack rm danceschool_shellonly

}


echo -e "Welcome to the Docker stack initialization script.\n\n"

# Fix UTF-8 issue on Macs
export LC_CTYPE=C

swarm_initialize
create_volumes
check_postgres_secrets
check_secret_key
check_ssl_certs
build_nginx
build_web
database_setup

echo -e "Setup complete!"
