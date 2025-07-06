#!/bin/bash

# Iniciar el primer script en segundo plano
/etc/confluent/docker/run &

# Iniciar el segundo script
/usr/bin/register-mongo-connector.sh
/usr/bin/register-cassandra-connector.sh
/usr/bin/register-mysql-connector.sh
# Mantener el contenedor en ejecución
wait