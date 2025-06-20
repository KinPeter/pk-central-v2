db.createUser({
  user: "admin",
  pwd: "admin",
  roles: [
    {
      role: "readWrite",
      db: "testdb",
    },
  ],
});

db = db.getSiblingDB("testdb");
