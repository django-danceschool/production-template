#!/bin/env bash
psql -U postgres -c "CREATE USER $(cat /run/secret/postgres_user) PASSWORD '$(cat /run/secret/postgres_password)'"
psql -U postgres -c "CREATE DATABASE $DB_NAME OWNER $(cat /run/secret/postgres_user)"

