# -*- coding: utf-8 -*-
#! /usr/bin/python3.6

# TP2 de Redes

import json
import queue
import socket
import sys 
import threading
import time

# CONSTANTES DO PROGRAMA
# ======================
EXIBIR_LOG         = True
MAX_PACOTE         = 65507
MSG_ATUALIZA       = 0
MSG_DADOS          = 1
MSG_RASTREIO       = 2
MSG_TABELA         = 3
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
processathread = None
recebethread = None
rotasthread = None

# CLASSES DO PROGRAMA
# ===================
# Gerencia as distâncias para os demais nós na rede
class Distancias():
  #modelo dicionario:
  #distancia = {'proximos': '[lista], 'peso': 0, 'proxid': 0}
  lista = {}

  def __init(self):
    pass

  # adiciona uma rota à lista de rotas conhecidas
  def adicionar(self, ip, proximo, peso):
    dist = {'proximos': [proximo], 'peso': peso, 'proxid': 0}
    if ip in self.lista.keys():
      if self.lista[ip]['peso'] > peso:
        self.lista[ip] = dist
      else if self.lista[ip]['peso'] == peso:
        self.lista[ip]['proximos'].append(proximo)
    else:
      self.lista[ip] = dist
    
  def exibir(self):
    for (c, dist) in self.lista.items():
      for prox in dist['proximos']:
        print(c, dist['peso'], "     ", prox)

  # elimina da lista de rotas aquelas onde o destino
  # é o proximo da rota ou é a origem de de onde
  #  a rota foi aprendida
  def obterotimizadas(self, ipeliminar):
    #ip: peso
    dist2 = {}
    for (c, dist) in self.lista.items():
      if ipeliminar == c:
        continue
      for prox in dist['proximos']:
        if ipeliminar == prox:
          continue
        dist2[c] = dist['peso']

    #adicionar a rota para ele mesmo
    dist2[parametros["ip"]] = 0

    return dist2

  # retorna quem é o próximo da rota para o 
  # ip especificado  usando balanceamento de carga
  def obterproximo(self, ip):
    for (c, dist) in self.lista.items():
      if ip == c:
        quant = len(dist['proximos'])
        i = randrange(quant)
        
        return dist['proximos'][i]

    return None;

  def remover(self, ip):
    for (c, dist) in self.lista.items():
      for prox in dist['proximos']:
        if ip == prox:
          del prox
          break
      if len(dist['proximos']) == 0:
        del dist
        recalcular(self, c)

  def removertudo(self):
    for dist in self.lista.values():
      del dist

# Thread para Enviar dados
class EnviaDadosThread(threading.Thread):
  msg = None

  def __init__(self, soquete):
    threading.Thread.__init__(self)
    msg = Mensagens(parametros['ip'])
    self.msgsproc = [msg.gerarAtualizacao, msg.gerarDados, msg.gerarRastreio, msg.gerarTabela]
    self.soquete = soquete
    self.fila = queue.Queue()
    self.ativa = True

  def desligar(self):
    self.ativa = False
    
  def enviar(self, destino, tipo, conteudo):
    pac = {'destino': destino, 'conteudo': self.msgsproc[tipo](destino, conteudo)}
    self.fila.put_nowait(pac)

  def repassar(self, destino, mensagem):
    prox = distancias.obterproximo(destino)
    if prox != None:
      pac = {'destino': prox, 'conteudo': mensagem}
      self.fila.put_nowait(pac)

  # enviar dados para o detino especificado
  def run(self):
    while(self.ativa):
      try:
        pac = self.fila.get(True, 2)
      except queue.Empty:
        continue
      endereco = (pac["destino"], parametros["porta"])
      try:
        self.soquete.sendto(pac['conteudo'], endereco)
        self.fila.task_done()
#        log("\n[>] Enviou dados: " + msg['conteudo'].decode())
      except socket.timeout:
        continue
   
    # desconectando...
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
    for c in self.lista.keys():
      print(c)

  def obtertudo(self):
    return self.lista.keys()

  def remover(self, ip):
    for (c, enlace) in self.lista.items():
      if c == ip:
        del enlace

  def removertudo(self):
    for enlace in self.lista.values():
      del enlace

# Gera e processa mensagens no formato JSON
class Mensagens:
  def __init__(self, ip):
    self.anaproc = {'update': self.analisarAtualizacao,
                    'data': self.analisarDados,
                    'trace': 0,
                    'table': 0}
    self.origem = ip
    
  def analisar(self, mensagem):
    dest = mensagem["destination"]
    if dest == parametros["ip"]:
      analisarproc = self.anaproc[mensagem["type"]]
      analisarproc(mensagem)
    else:
      enviathread.repassar(dest, json.dumps(mensagem).encode())

  def analisarAtualizacao(self, mensagem):
    #distancia = {'proximo': '0.0.0.0', 'peso': 0}
    prox = mensagem["source"]
    dists = mensagem["distances"]
    for (c, p) in dists.items():
      ip = c
      peso = int(p) + 1 
      distancias.adicionar(ip, prox, peso)
  
  def analisarDados(self, mensagem):
    dados = mensagem["payload"]
    print(dados)

  def converter(self, mensagem):
    msg = json.loads(mensagem.decode())

    return msg
  
  def gerar(self, destino):
    msg = {}
    msg["type"] = ""
    msg["source"] = self.origem
    msg["destination"] = destino
    
    return msg
    
  # define que gerar() é um método privado
  __gerar = gerar
    
  def gerarAtualizacao(self, destino, distancias):
    msg = self.gerar(destino)
    msg["type"] = "update"
    msg["distances"] = distancias
    
    return json.dumps(msg).encode()
  
  def gerarDados(self, destino, dados):
    msg = self.gerar(destino)
    msg["type"] = "data"
    msg["payload"] = dados

    return json.dumps(msg).encode()
  
  def gerarRastreio(self, destino, rastro):
    msg = self.gerar(destino)
    msg["type"] = "trace"
    msg["hops"] = rastro

    return json.dumps(msg).encode()
    
  def gerarTabela(self, destino, tabela):
    msg = self.gerar(destino)
    msg["type"] = "table"
    print("ops!")

    return json.dumps(msg).encode()
    
# Thread para Processar os dados recebidos
class ProcessaDadosThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.ativa = True
    self.fila = queue.Queue()
    self.msgs = Mensagens(parametros['ip'])

  def desligar(self):
    self.ativa = False

  def processar(self, mensagem):
    msg = self.msgs.converter(mensagem)
    self.fila.put_nowait(msg)

  def run(self):
    while self.ativa:
      try:
        msg = self.fila.get(True, 2)
      except (queue.Empty):
        continue
      self.msgs.analisar(msg)
      self.fila.task_done()
    
# Thread para Receber dados
class RecebeDadosThread(threading.Thread):
  def __init__(self, soquete):
    threading.Thread.__init__(self)
    self.ativa = True
    self.soquete = soquete
    self.soquete.settimeout(1)

  # manipular o soquete para receber dados e enviar para processamento
  def run(self):
    while self.ativa:
      try:
        cont, (ip, porta) = self.soquete.recvfrom(MAX_PACOTE)
      except (socket.timeout, OSError):
        continue
      if not cont:
        break
      if cont == '':
        break
      if not self.ativa:
        break
      self.onrecv(cont)
    self.soquete.close()

  def desligar(self):
    self.ativa = False
    
  def onrecv(self, msg):
    processathread.processar(msg)
#    log("\n[>] Recebeu dados: " + dados.decode())

# Thread para gerar rotas atualizadas
class RotasAtualizadasThread(threading.Thread):
  def __init__(self, intervalo):
    threading.Thread.__init__(self)
    self.intervalo = intervalo
    self.ativa = True    

  def desligar(self):
    self.ativa = False
    
  # gera a msg de rotas atualizadas a cada intevalo de tempo
  def run(self):
    while(self.ativa):
      dests = enlaces.obtertudo()
      for d in dests:
        dist = distancias.obterotimizadas(d)
        enviathread.enviar(d, MSG_ATUALIZA, dist)
      time.sleep(self.intervalo)
    # desligando...

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
#   parametros = dicionario onde serão gravados os argumentos
def args_processar(parametros):
  parametros['ip'] = sys.argv[1]
  parametros['periodo'] = int(sys.argv[2])
  if len(sys.argv) > 3:
    parametros['topologia'] = sys.argv[3]
  parametros['porta'] = PORTA

# -----------------------------------------
# Carrega um arquivo somente-texto e o quebra em linhas
#   nomearquivo = nome do arquivo a ser carregado
def entrada_carregar(nomearquivo):
  arq = open(nomearquivo, "r")
  lins = arq.read().splitlines()
  for l in lins:
    yield l

# -----------------------------------------
def cmd_add(args):
  if len(args) > 2:
    ip = args[1]
    peso = int(args[2])
    distancias.adicionar(ip, ip, peso, parametros['ip'])
    enlaces.adicionar(ip)
  else:
    print(ARGS_INSUFICIENTES.format(args[0]))

def cmd_del(args):
  if len(args) > 1:
    enlaces.remover(args[1])
    distancias.remover(args[1])
  else:
    print(ARGS_INSUFICIENTES.format(args[0]))

def cmd_quit(args):
  app_sair()

def cmd_ip(args):
  print("\nConfiguração de IP:\n")
  print("    Endereço: . . . . : {0}".format(parametros['ip'])) 
  
def cmd_distances(args):
  print("IP        PESO     PROXIMO      APRENDEU DE")
  print("===========================================")
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
  args = cmd.split(' ')
  if args[0] in cmds_disponiveis.keys():
    cmds_disponiveis[args[0]](args)
  else:
    print(CMD_NAOENCONTRADO.format(args[0]))

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
  rotasthread.desligar()
  rotasthread.join()
  processathread.desligar()
  processathread.join()
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
  soq = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  # Para evitar a exceção "address already in use",
  # desligar esse comportamento com uma opção da API de soquetes:
  soq.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  soq.bind(param)

  # Inicia a thread que irá receber dados
  recebethread = RecebeDadosThread(soq)
  recebethread.start()
  
  # Inicia a thread que irá enviar dados
  enviathread = EnviaDadosThread(soq)
  enviathread.start()

# CORPO DO PROGRAMA
# =================
if len(sys.argv) > 2:
  args_processar(parametros)
  distancias = Distancias()
  enlaces = Enlaces()
  processathread = ProcessaDadosThread()
  processathread.start()
  conexoes_iniciar((parametros['ip'], parametros['porta']))
  rotasthread = RotasAtualizadasThread(parametros['periodo'])
  rotasthread.start()
  if len(parametros['topologia']) > 0:
    coms = entrada_carregar(parametros['topologia'])
    cmdline_batch(coms)
  cmdline_manipular()
  app_sair()