@echo off
echo ==========================================
echo   CHAFF Ghost Engine - Dry Run Test
echo ==========================================
echo.
echo This will generate a ghost profile and
echo simulate one activity cycle WITHOUT
echo posting anything to Reddit.
echo.
python ghost_engine.py --dry-run --profiles-only
echo.
echo Press any key to run a simulated cycle...
pause > nul
python ghost_engine.py --dry-run --run-once
echo.
echo Done! Check output above for ghost profile.
pause
