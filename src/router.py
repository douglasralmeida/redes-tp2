# -*- coding: utf-8 -*-
#! /usr/bin/python3.6

# TP2 de Redes

import socket
import sys

# CONSTANTES DO PROGRAMA
# ======================
EXIBIR_LOG         = True
PORTA              = 55151

# VARIÁVEIS DO PROGRAMA
# =====================
parametros = {'periodo' : 0, 'ip': '127.0.0.1', 'partida': ''}


# FUNCOES DO PROGRAMA
# ===================

def log(msg):
  if EXIBIR_LOG:
    print(msg) 

# Lê os argumentos do programa
# arg1 = ip
# arg2 = período de repetição da msg
# arg3 = opcional, arq. topologia inicial da rede
def args_processar(parametros):
  parametros['ip'] = sys.argv[1]
  parametros['periodo'] = int(sys.argv[2])
  if len(sys.argv) > 3:
    parametros['topologia'] = sys.argv[3]

# CORPO DO PROGRAMA
# =================
if len(sys.argv) > 2:
  args_processar(parametros)
