@echo off
title Sports EV Tracker - Backend Scraper
:: Configura o terminal para UTF-8 para exibir acentos corretamente
chcp 65001 > nul

echo ============================================================
echo   INICIANDO MOTOR BACKEND (SCRAPER + POISSON + RESOLVER)
echo ============================================================
echo.

:loop
echo [%date% %time%] [INFO] Iniciando ciclo de varredura e resolucao de resultados...
venv\Scripts\python.exe main.py
echo.
echo [%date% %time%] [SUCCESS] Ciclo concluído com sucesso.
echo [%date% %time%] [WAIT] Aguardando 5 minutos (300 segundos) para a próxima varredura...
ping 127.0.0.1 -n 301 > nul
echo.
goto loop
