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
            echo
            docker secret rm django_secret_key
        else
            echo
            return
        fi
    else
        echo "Generating Django secret key."
    fi

    echo $(< /dev/urandom tr -dc A-Za-z0-9 | head -c${1:-32}) | docker secret create django_secret_key -

}

create_ssl_secrets () {

    # Require an SSL certificate either by having a file provided, or by generating one using OpenSSL
    echo -e 'Please select a source for an SSL certificate:\n'

    options=("Provide an SSL Certificate" "Generate Using OpenSSL (for testing only)" "Quit")
    select opt in "${options[@]}"
    do
        case $opt in
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
                exit 1
                ;;
            *) echo invalid option;;
        esac
    done
}

check_ssl_secrets () {
    # Get the list of existing secrets to see if new ones need to be created/updated
    EXISTING_SECRET_LIST="$(docker secret ls)"

    # These need to be checked individually first in case some are specified and others are not.
    SSL_CERT_EXISTS=$(grep -c "site\.crt" <<< $EXISTING_SECRET_LIST)
    SSL_KEY_EXISTS=$(grep -c "site\.key" <<< $EXISTING_SECRET_LIST)

    if [ $SSL_CERT_EXISTS -lt 1 ] || [ $SSL_KEY_EXISTS -lt 1 ] ; then
        if [ $SSL_CERT_EXISTS -ge 1 ] ; then
            docker secret rm site.crt
        fi

        if [ $SSL_KEY_EXISTS -ge 1 ] ; then
            docker secret rm site.key
        fi

        echo -e 'Existing SSL credentials not found or are incomplete.\n'
        create_ssl_secrets

    else
        read -p "Existing SSL credentials found. Replace them? [y/N] " -n 1 -r
        if [[ $REPLY =~ ^[Yy]$ ]] ; then
            docker secret rm site.crt
            docker secret rm site.key
            create_ssl_secrets
            echo -e "\n"
        fi

    fi
}

build_nginx () {
    IMAGE_EXISTS=$(docker images | grep -c danceschool_nginx)

    if [ $IMAGE_EXISTS -ge 1 ] ; then
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
    docker build --no-cache -t danceschool_nginx ${BASH_SOURCE%/*}/nginx
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

swarm_initialize
create_volumes
check_postgres_secrets
check_secret_key
check_ssl_secrets
build_nginx
build_web
database_setup

echo -e "Setup complete!"
