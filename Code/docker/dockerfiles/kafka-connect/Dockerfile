# Utiliza la imagen base de Kafka Connect
FROM cnfldemos/cp-server-connect-datagen:0.6.4-7.6.0

# Instala el conector HDFS Sink desde Confluent Hub
RUN confluent-hub install --no-prompt mongodb/kafka-connect-mongodb:1.9.1
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-spooldir:latest
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:latest


# Exponer los puertos necesarios (opcional)
EXPOSE 8083

# Registrar automáticamente el conector
COPY mongo-source.json /tmp/
COPY entrypoint.sh /usr/bin/
COPY register-mongo-connector.sh /usr/bin/




ENV CLASSPATH="/usr/share/confluent-hub-components/confluentinc-kafka-connect-jdbc/lib"
# CMD ["connect-distributed", "/etc/kafka/connect-distributed.properties"]
USER root
RUN chmod +x /usr/bin/entrypoint.sh /usr/bin/register-mongo-connector.sh /

USER appuser

ENTRYPOINT ["bash", "-c", "/usr/bin/entrypoint.sh"]