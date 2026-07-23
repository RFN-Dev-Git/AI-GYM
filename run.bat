@echo off
REM AI-GYM Exercise Runner for Windows
REM Usage: run.bat exercise_name [video_file] [s] [c]
REM   s = save output video
REM   c = use webcam

set EXERCISE=%1
set VIDEO=%2
set FLAGS=%3 %4

cd backend
python -m src.main %EXERCISE% %VIDEO% %FLAGS%
cd ..
