# -*- coding: utf-8 -*-
#! /usr/bin/python3.6

# TP2 de Redes

import socket
import sys

# CONSTANTES DO PROGRAMA
# ======================
EXIBIR_LOG         = True
PORTA              = 55151
ARGS_INSUFICIENTES = "Erro com o comando {0}. Argumentos insuficientes."
CMD_NAOENCONTRADO  = "Comando não encontrado: {0}"
PROMPT             = "$ "

# VARIÁVEIS DO PROGRAMA
# =====================
parametros = {'periodo' : 0, 'ip': '127.0.0.1', 'topologia': ''}
#distancia = {'prox': '0.0.0.0', 'peso': 0}
distancias = {}

# FUNCOES DO PROGRAMA
# ===================
def log(msg):
  if EXIBIR_LOG:
    print(msg) 

# -----------------------------------------
# Lê os argumentos do programa
# arg1 = ip
# arg2 = período de repetição da msg
# arg3 = opcional, arq. topologia inicial da rede
def args_processar(parametros):
  parametros['ip'] = sys.argv[1]
  parametros['periodo'] = int(sys.argv[2])
  if len(sys.argv) > 3:
    parametros['topologia'] = sys.argv[3]

# -----------------------------------------  
def entrada_carregar(nomearquivo):
  arquivo = open(nomearquivo, "r")
  linhas = arquivo.read().splitlines()
  for linha in linhas:
    yield linha

# -----------------------------------------
def distancias_adicionar(ip, distancia):
  distancias[ip] = distancia
  
def distancias_remover(ip):
  del distancias[ip]
  
def distancias_obterpeso(ip):
  return distancias[ip]['peso']

def distancias_obterprox(ip):
  return distancias[ip]['prox']

# -----------------------------------------
def cmd_add(args):
  if len(args) > 2:
    distancia = {'prox': args[1], 'peso': args[2]}
    distancias_adicionar(args[1], distancia)
  else:
    print(ARGS_INSUFICIENTES.format(args[0]))

def cmd_del(args):
  if len(args) > 1:
    distancias_remover(args[1])
  else:
    print(ARGS_INSUFICIENTES.format(args[0]))

def cmd_quit(args):
  sys.exit()
  
def cmd_links(args):
  print("IP        PESO     PROXIMO")
  print("==========================")
  for ip in distancias.keys():
    print(ip, distancias_obterpeso(ip), "     ", distancias_obterprox(ip))
  
cmds_disponiveis = {
  "add": cmd_add,
  "del": cmd_del,
  "quit": cmd_quit,
  "links": cmd_links
}

# -----------------------------------------
def cmdline_batch(cmds):
  for cmd in cmds:
    print(PROMPT + cmd)
    cmdline_executar(cmd)

def cmdline_executar(cmd):
  cmd_args = cmd.split(' ')
  if cmd_args[0] in cmds_disponiveis.keys():
    cmds_disponiveis[cmd_args[0]](cmd_args)
  else:
    print(CMD_NAOENCONTRADO.format(cmd_args[0]))

def cmdline_obter():
  s = ''
  while len(s) == 0:
    try:
      s = input(PROMPT)
    except:
      sys.exit()
  
  return ' '.join(s.split())

def cmdline_manipular():
  while (True):
    cmd = cmdline_obter()
    cmdline_executar(cmd)

# CORPO DO PROGRAMA
# =================
if len(sys.argv) > 2:
  args_processar(parametros)
  if len(parametros['topologia']) > 0:
    comandos = entrada_carregar(parametros['topologia'])
    cmdline_batch(comandos)
  cmd = cmdline_manipular()
