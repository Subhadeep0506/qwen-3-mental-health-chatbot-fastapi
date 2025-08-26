echo '[INFO] Creating "monitoring" network'
docker network create monitoring

echo '[INFO] Starting docker containers'
docker compose -f docker-compose-grafana.yml up -d --build