curl http://localhost:8000/
curl http://localhost:8000/items/42
curl http://localhost:8000/items/13
curl -X POST http://localhost:8000/orders  # custom spans + metrics
for i in $(seq 1 20); do curl -s -X POST http://localhost:8000/orders > /dev/null; done
