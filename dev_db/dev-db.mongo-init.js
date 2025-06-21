db.createUser({
  user: "admin",
  pwd: "admin",
  roles: [
    {
      role: "readWrite",
      db: "central-v2",
    },
  ],
});

db = db.getSiblingDB("central-v2");

db.createCollection("users");
db.createCollection("activities");
db.createCollection("start_settings");
db.createCollection("shortcuts");
db.createCollection("notes");
db.createCollection("personal_data");
db.createCollection("flights");
db.createCollection("visits");
db.createCollection("strava_activities");
db.createCollection("strava_sync_metadata");
db.createCollection("reddit");
