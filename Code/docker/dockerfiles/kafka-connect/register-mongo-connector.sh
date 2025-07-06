LOG_FILE="/home/appuser/register_connectors.log"
CURL_OUTPUT="/home/appuser/curl_output"
CURL_ERROR="/home/appuser/curl_error.log"

echo "Iniciando registro de conectores..." > $LOG_FILE

echo "Esperando que Kafka Connect esté disponible..."
RETRY_COUNT=0

until curl -s http://localhost:8083/; do
  RETRY_COUNT=$((RETRY_COUNT + 1))
  
  echo "Intento $RETRY_COUNT: Kafka Connect no está disponible. Reintentando en 5 segundos..." | tee -a "$LOG_FILE"
  sleep 5
done

echo "Kafka Connect está disponible después de $RETRY_COUNT intentos. Registrando Conectores." | tee -a "$LOG_FILE"

sleep 20
RESPONSE=$(curl -s -o $CURL_OUTPUT -w "%{http_code}" -X POST -H "Content-Type: application/json" --data @/tmp/mongo-source.json http://localhost:8083/connectors 2>$CURL_ERROR)

if [ "$RESPONSE" -ne 201 ]; then
  echo "Error al registrar el conector. Código de respuesta HTTP: $RESPONSE" | tee -a $LOG_FILE >&2
  echo "Respuesta del servidor:" >> $LOG_FILE
  if [ -f $CURL_OUTPUT ]; then
    cat $CURL_OUTPUT >> $LOG_FILE
  else
    echo "No se generó una respuesta válida del servidor." >> $LOG_FILE
  fi
  echo "Errores de CURL:" >> $LOG_FILE
  if [ -f $CURL_ERROR ]; then
    cat $CURL_ERROR >> $LOG_FILE
  fi
else
  echo "Conector registrado exitosamente." | tee -a $LOG_FILE
  echo "Respuesta del servidor:" >> $LOG_FILE
  cat $CURL_OUTPUT >> $LOG_FILE
fi

RESPONSE=$(curl -s -o $CURL_OUTPUT -w "%{http_code}" -X POST -H "Content-Type: application/json" --data @/tmp/mongo-source.json http://localhost:8083/connectors 2>$CURL_ERROR)

if [ "$RESPONSE" -ne 201 ]; then
  echo "Error al registrar el conector. Código de respuesta HTTP: $RESPONSE" | tee -a $LOG_FILE >&2
  echo "Respuesta del servidor:" >> $LOG_FILE
  if [ -f $CURL_OUTPUT ]; then
    cat $CURL_OUTPUT >> $LOG_FILE
  else
    echo "No se generó una respuesta válida del servidor." >> $LOG_FILE
  fi
  echo "Errores de CURL:" >> $LOG_FILE
  if [ -f $CURL_ERROR ]; then
    cat $CURL_ERROR >> $LOG_FILE
  fi
else
  echo "Conector registrado exitosamente." | tee -a $LOG_FILE
  echo "Respuesta del servidor:" >> $LOG_FILE
  cat $CURL_OUTPUT >> $LOG_FILE
fi

echo "Proceso completado. Los resultados se han registrado en $LOG_FILE."