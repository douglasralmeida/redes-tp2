# -*- coding: utf-8 -*-
#! /usr/bin/python3.6

# TP2 de Redes

import socket
import sys 
import threading

# CONSTANTES DO PROGRAMA
# ======================
EXIBIR_LOG         = True
PORTA              = 55151
ARGS_INSUFICIENTES = "Erro com o comando {0}. Argumentos insuficientes."
CMD_NAOENCONTRADO  = "Comando não encontrado: {0}"
CONEX_NAOREALIZADA = "A conexão com o endereço {0} não foi realizada."
PROMPT             = "$ "

# VARIÁVEIS DO PROGRAMA
# =====================
parametros = {'periodo' : 0, 'ip': '127.0.0.1', 'topologia': '', 'porta': 0, 'timeout': 7}
#distancia = {'prox': '0.0.0.0', 'peso': 0}
distancias = {}
enlaces = []
threads = []
redethread = 0

# CLASSES DO PROGRAMA
# ===================
# Gerencia um enlace
class EnlaceThread(threading.Thread):
  def __init__(self, soquete, ip):
    threading.Thread.__init__(self)
    self.soquete = soquete
    self.ip = ip
    enlaces.append(ip)
    log("[+] Nova thread para o enlance ao endereço " + ip + ".")

  # manipular o self.soquete para receber dados do enlace
  def run(self):
    while(True):
      try:
        dados = self.soquete.recv()
      except socket.timeout:
        continue
      if not dados:
        break
      if dados == '':
        break
      
      # recebeu uma mensagen
      self.onrecv(client, dados)
   
    # removendo cliente da listas de enlaces
    enlaces.remove(ip)
    log("[-] Encerrando thread do enlance ao endereço " + ip + ".")
    
    # desconectando...
    sel.soquete.close()
    
    # encerrando thread
    thread.exit()
    threads.remove(self)
    
  def onrecv(self):
    pass

# Cria enlaces com a rede passivamente
class RedeThread(threading.Thread):
  def __init__(self, soquete):
    threading.Thread.__init__(self)
    self.escutarrede = True
    self.soquete = soquete
    self.soquete.listen(4)
    self.soquete.settimeout(1)

  # manipular o soquete para formar enlaces
  def run(self):
    log("[O] Aguardando por novas conexões...")
    while self.escutarrede:
      try:
        (cliente, (ip, porta)) = self.soquete.accept()
      except socket.timeout:
        continue
      if not self.escutarrede:
        break
      enlacethread = EnlaceThread(cliente, ip)
      enlacethread.start()
      threads.append(enlacethread)
    log("[O] Encerrando escuta por novas conexões...")
      
  def desligar(self):
    self.escutarrede = False

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
  parametros['porta'] = PORTA

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
    ip = args[1]
    distancia = {'prox': ip, 'peso': args[2]}
    soquete = rede_conectar((ip, parametros['porta']))
    if soquete is None:
      print(CONEX_NAOREALIZADA.format(ip))
      return
    enlacethread = EnlaceThread(soquete, ip)
    enlacethread.start()
    threads.append(enlacethread)    
    distancias_adicionar(ip, distancia)
  else:
    print(ARGS_INSUFICIENTES.format(args[0]))

def cmd_del(args):
  if len(args) > 1:
    distancias_remover(args[1])
  else:
    print(ARGS_INSUFICIENTES.format(args[0]))

def cmd_quit(args):
  app_sair()
  
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
      app_sair()
  
  return ' '.join(s.split())

def cmdline_manipular():
  while (True):
    cmd = cmdline_obter()
    cmdline_executar(cmd)

# -----------------------------------------
def app_sair():
  for t in threads:
    t.join()
  redethread.desligar()
  redethread.join()
  sys.exit()
  
# -----------------------------------------
def rede_iniciar(param):
  global redethread
  
  # Cria um soquete para comunicação externa
  soquete = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  # Para evitar a exceção "address already in use",
  # desligar esse comportamento com uma opção da API de soquetes:
  soquete.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  soquete.bind(param)

  # Inicia a thread que irá escutar por novas conexões
  redethread = RedeThread(soquete)
  redethread.start()

def rede_conectar(param):
  log("[O] Conectando ativamente com {0}...".format(param[0]))
  try:
    soquete = socket.create_connection(param, parametros['timeout'])
  except:
    soquete = None
  
  return soquete

# CORPO DO PROGRAMA
# =================
if len(sys.argv) > 2:
  args_processar(parametros)
  rede_iniciar((parametros['ip'], parametros['porta']))
  if len(parametros['topologia']) > 0:
    comandos = entrada_carregar(parametros['topologia'])
    cmdline_batch(comandos)
  cmd = cmdline_manipular()
  app_sair()
