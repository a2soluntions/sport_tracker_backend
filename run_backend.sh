#!/bin/bash
# Ativar o ambiente virtual
source venv/bin/activate

# Loop infinito
while true; do
  echo "============================================="
  echo "Buscando novas atualizacoes do Git..."
  git pull
  echo "Iniciando ciclo de varredura: $(date)"
  echo "============================================="
  python3 main.py
  echo "---------------------------------------------"
  echo "Ciclo finalizado. Aguardando 5 minutos..."
  echo "---------------------------------------------"
  sleep 300
done
