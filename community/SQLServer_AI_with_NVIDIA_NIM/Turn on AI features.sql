EXEC sp_configure 'external rest endpoint enabled', 1;
RECONFIGURE WITH OVERRIDE;



USE AdventureWorks;
GRANT EXECUTE ANY EXTERNAL ENDPOINT TO [JWU-WINDOW11-AL\josephw];
