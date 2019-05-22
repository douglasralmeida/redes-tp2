# -*- coding: utf-8 -*-
#! /usr/bin/python3.6

# TP2 de Redes

import socket
import sys 
import threading
import time

# CONSTANTES DO PROGRAMA
# ======================
EXIBIR_LOG         = True
MAX_PACOTE         = 65507
PORTA              = 55151
ARGS_INSUFICIENTES = "Erro com o comando {0}. Argumentos insuficientes."
CMD_NAOENCONTRADO  = "Comando não encontrado: {0}"
PROMPT             = "$ "

# VARIÁVEIS DO PROGRAMA
# =====================
parametros = {'periodo' : 0, 'ip': '127.0.0.1', 'topologia': '', 'porta': 0, 'timeout': 6}
distancias = None
enlaces = None
enviathread = None
recebethread = None

# CLASSES DO PROGRAMA
# ===================
# Gerencia as distâncias para os demais nós na rede
class Distancias():
  #modelo dicionario:
  #distancia = {'prox': '0.0.0.0', 'peso': 0}
  lista = {}

  def __init(self):
    pass
    
  def adicionar(self, ip, proximo, peso):
    distancia = {'proximo': proximo, 'peso': peso}
    self.lista[ip] = distancia
    
  def exibir(self):
    for (chave, distancia) in self.lista.items():
      print(chave, distancia['peso'], "     ", distancia['proximo'])

  def remover(self, ip):
    for (chave, distancia) in self.lista.items():
      if chave == ip:
        del distancia

  def removertudo(self):
    for distancia in self.lista.values():
      del distancia

# Thread para Enviar dados
class EnviaDadosThread(threading.Thread):
  def __init__(self, soquete, periodo):
    threading.Thread.__init__(self)
    self.periodo = periodo
    self.soquete = soquete
    self.enviardados = True    
    log("\n[+] Nova thread para o envio de dados.")

  def desligar(self):
    self.enviardados = False

  # enviar dados para todos os enlaces
  def run(self):
    while(self.enviardados):
      try:
        endereco = ("127.0.0.1", parametros["porta"])
        #self.soquete.sendto(dados, endereco)
        time.sleep(self.periodo)
      except socket.timeout:
        continue
   
    # desconectando...
    log("\n[-] Encerrando thread de envio de dados.")
    self.soquete.close()        

# Gerencia os enlaces na rede
class Enlaces():
  #modelo dicionario:
  #enlace = {'ip': '0.0.0.0'}
  lista = {}

  def __init(self):
    pass
    
  def adicionar(self, ip):
    enlace = {'valor': 1}
    self.lista[ip] = enlace
    
  def exibir(self):
    for chave in self.lista.keys():
      print(chave)

  def remover(self, ip):
    for (chave, enlace) in self.lista.items():
      if chave == ip:
        del enlace

  def removertudo(self):
    for enlace in self.lista.values():
      del enlace

# Thread para Receber dados
class RecebeDadosThread(threading.Thread):
  def __init__(self, soquete):
    threading.Thread.__init__(self)
    self.escutarrede = True
    self.soquete = soquete
    self.soquete.settimeout(1)

  # manipular o soquete para formar enlaces
  def run(self):
    log("[+] Nova thread para o recebimento de dados.")
    while self.escutarrede:
      try:
        dados, (ip, porta) = self.soquete.recvfrom(MAX_PACOTE)
      except (socket.timeout, OSError):
        continue
      if not dados:
        break
      if dados == '':
        break
      if not self.escutarrede:
        break
      onrecv(dados)
    log("[-] Encerrando thread de recebimento de dados.")
    self.soquete.close()

  def desligar(self):
    self.escutarrede = False
    
  def onrecv(self, dados):
    log("[>] Recebeu dados: " + dados)

# FUNCOES DO PROGRAMA
# ===================
def log(*args, **kwargs):
  if EXIBIR_LOG:
    print(*args, file=sys.stderr, **kwargs)
    
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
def cmd_add(args):
  if len(args) > 2:
    ip = args[1]
    distancias.adicionar(ip, ip, args[2])
    enlaces.adicionar(ip)
  else:
    print(ARGS_INSUFICIENTES.format(args[0]))

def cmd_del(args):
  if len(args) > 1:
    enlaces.remover(args[1])
    #comando para recalcular distancias onde o proximo é o ip removido
  else:
    print(ARGS_INSUFICIENTES.format(args[0]))

def cmd_quit(args):
  app_sair()

def cmd_ip(args):
  print("\nConfiguração de IP:\n")
  print("    Endereço: . . . . : {0}".format(parametros['ip'])) 
  
def cmd_distances(args):
  print("IP        PESO     PROXIMO")
  print("==========================")
  distancias.exibir()

def cmd_links(args):
  print("\nEnlaces:\n")
  print("IP")
  print("==========================")
  enlaces.exibir()

cmds_disponiveis = {
  "add": cmd_add,
  "del": cmd_del,
  "quit": cmd_quit,
  "ip": cmd_ip,
  "links": cmd_links,
  "distances": cmd_distances
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
  enlaces.removertudo()
  distancias.removertudo()
  recebethread.desligar()
  recebethread.join()
  enviathread.desligar()
  enviathread.join()
  sys.exit()
  
# -----------------------------------------
def conexoes_iniciar(param):
  global enviathread
  global recebethread
  
  # Cria um soquete para comunicação externa
  soquete = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  # Para evitar a exceção "address already in use",
  # desligar esse comportamento com uma opção da API de soquetes:
  soquete.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  soquete.bind(param)

  # Inicia a thread que irá receber dados
  recebethread = RecebeDadosThread(soquete)
  recebethread.start()
  
  # Inicia a thread que irá enviar dados
  enviathread = EnviaDadosThread(soquete, parametros['periodo'])
  enviathread.start()

# CORPO DO PROGRAMA
# =================
if len(sys.argv) > 2:
  args_processar(parametros)
  distancias = Distancias()
  enlaces = Enlaces()
  conexoes_iniciar((parametros['ip'], parametros['porta']))
  if len(parametros['topologia']) > 0:
    comandos = entrada_carregar(parametros['topologia'])
    cmdline_batch(comandos)
  cmd = cmdline_manipular()
  app_sair()
