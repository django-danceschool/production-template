#!/bin/env bash

if [ ! -f ./env.default ]; then
  echo -e "\nGenerating an env.default file"

  # Random Keys
  SECRET_KEY=$(bin/rake secret)
  DB_PASS=$(bin/rake secret)

  # Generate the file
  cat > ./env.default <<EOL

  DB_NAME=danceschool_web
  DB_USER=danceschool_web
  DB_PASS=${DB_PASS}
  DB_SERVICE=postgres
  DB_PORT=5432
  SECRET_KEY=${SECRET_KEY}
  DEBUG=False
  REDIS_URL=redis://redis:6379/0
EOL
fi