@echo off
cd C:\Users\hp\athena-scip\backend\event-ingestor
set SUPABASE_URL=https://catpprgdbvenutyyjqbx.supabase.co
set SUPABASE_SERVICE_ROLE_KEY=YOUR_ACTUAL_SERVICE_ROLE_KEY_HERE
py main.py
echo Ingestor run at %date% %time% >> ingestor-log.txt