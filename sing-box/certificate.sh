#!/bin/bash

# Generate the self-signed certificate if it doesn't exist
if [ ! -f ./server.key ] || [ ! -f ./server.crt ]; then
    openssl req -x509 -nodes -newkey ec:<(openssl ecparam -name prime256v1) \
        -keyout ./server.key \
        -out ./server.crt \
        -subj "/CN=www.mihoyo.com" -days 36500
fi
