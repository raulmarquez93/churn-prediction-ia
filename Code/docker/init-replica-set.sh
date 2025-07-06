#!/bin/bash

# Esperar a que MongoDB esté disponible
until /usr/bin/mongosh --host mongodb:27017 -u root -p root --authenticationDatabase admin --eval 'print("Waiting for MongoDB to start")'; do
    sleep 2;
done;

# Inicializar el Replica Set con autenticación
/usr/bin/mongosh --host mongodb:27017 -u root -p root --authenticationDatabase admin --eval '
  rs.initiate();
'
