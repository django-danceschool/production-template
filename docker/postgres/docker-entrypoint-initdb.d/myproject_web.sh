#!/bin/env bash
psql -U postgres -c "CREATE USER $(cat /run/secrets/postgres_user) PASSWORD '$(cat /run/secrets/postgres_password)'"
psql -U postgres -c "CREATE DATABASE $DB_NAME OWNER $(cat /run/secrets/postgres_user)"

