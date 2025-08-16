@echo off
echo Sauvegarde automatique Git...
git add .
git commit -m "Sauvegarde automatique - %date% %time%"
git push
echo Sauvegarde terminee!
pause