#!/bin/bash
# Wait for MongoDB to be ready
until mongosh --host localhost -u admin -p admin --authenticationDatabase admin --eval "db.adminCommand('ping')" > /dev/null 2>&1; do
  echo "Waiting for MongoDB to start..."
  sleep 2
done

# Import aircrafts.json into the aircrafts collection
mongoimport --host localhost -u admin -p admin --authenticationDatabase admin \
  --db testdb --collection aircrafts \
  --file /app/static_data/aircrafts.json --jsonArray

echo "Aircrafts data seeded."

# Import airlines.json into the airlines collection
mongoimport --host localhost -u admin -p admin --authenticationDatabase admin \
  --db testdb --collection airlines \
  --file /app/static_data/airlines.json --jsonArray

echo "Airlines data seeded."
