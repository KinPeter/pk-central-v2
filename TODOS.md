# TODOs

## Flights/Visits/Trips

- add new airports on every new and updated flight (util function call before handler function in router?)

- add POST /flights/query endpoint for advanced flight queries
- add POST /visits/query endpoint for advanced visit queries

- add get_trips year filtering
- add get_trips map and chart data logic
- add get_trips unit and acceptance test coverage

## Database backup (dump) cron job

- create a script to dump the database and can run natively on the VPS
- add a cron job to run the script regularly (e.g., daily)
- figure out where to upload and store the dumps (e.g., FTP, Drive, OneDrive)

## Strava

- add Strava API integration for syncing activities
- sync full activity data, all sport types
- sync lat/lon streams for activities in separate table
- return activity data and route streams with date range filtering
