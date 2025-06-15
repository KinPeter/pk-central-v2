db.createUser({
  user: "admin",
  pwd: "admin",
  roles: [
    {
      role: "readWrite",
      db: "central",
    },
  ],
});

db = db.getSiblingDB("central");

db.createCollection("users");
db.createCollection("sync_metadata");
db.createCollection("activities");
