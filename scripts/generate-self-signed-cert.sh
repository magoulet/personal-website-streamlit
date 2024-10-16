#!/bin/bash

# Define variables
CERT_DIR="/etc/nginx/ssl"
DOMAIN="magoulet.com"
DAYS_VALID=365
RSA_KEY_SIZE=2048

# Create the certificates directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Generate the self-signed certificate
openssl req -x509 -nodes -days $DAYS_VALID -newkey rsa:$RSA_KEY_SIZE \
  -keyout "$CERT_DIR/privkey.pem" -out "$CERT_DIR/fullchain.pem" \
  -subj "/CN=$DOMAIN"

# Print completion message
echo "Self-signed certificate generated and stored in $CERT_DIR"
