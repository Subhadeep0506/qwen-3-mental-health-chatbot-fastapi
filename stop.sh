echo '[INFO] Stopping all container'
docker compose -f docker-compose-grafana.yml down

echo 'Cleaning docker cache'
docker system prune --all -f