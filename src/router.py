# -*- coding: utf-8 -*-
#! /usr/bin/python3.6

# TP2 de Redes

import json
import queue
import random
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
ARGS_INSUFICIENTES = "Erro com o comando {0}: Argumentos insuficientes."
CMD_NAOENCONTRADO  = "Comando não encontrado: {0}"
ROTA_NAOCONHECIDA  = "Erro: Uma rota para {0} não é conhecida."
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
# Armazena uma rota conhecida com o seu peso
class Rota():
  # Construtor da classe
  def __init__ (self, prox, peso, tdv):
    self.peso = peso
    self.prox = prox
    self.tempovida = tdv

  # Testes de igualdade
  def __eq__(self, outro):
    return  isinstance(outro, Rota) and self.prox == outro.prox

  def __hash__(self):
    return hash(self.prox)

  # representação em string
  def __repr__(self):
    return repr((self.prox, self.peso))

  # formata em string para exibição
  def __str__(self):
    return "{0: <5} {1}  {2}".format(self.peso, self.prox, self.tempovida)

# Gerencia todas as rotas conhecidas para um nó
# na rede, ordenando-as a partir da menor
class Rotas():
  # Construtor da classe
  def __init__(self):
    self.index = 0
    self.lista = list()

  # Interador sobre a lista de rotas
  def __iter__(self):
    return self

  def __len__(self):
    return len(self.lista)

  def __next__(self):
    if self.index >= len(self.lista):
      raise StopIteration
    self.index = self.index + 1
    
    return self.lista[self.index - 1]

  # representação em string
  def __repr__(self):
    return repr(self.lista)

  # formata em string para exibição
  def __str__(self):
    primeiro = self.lista[0]
    return str(primeiro)

  # Adiciona uma rota conhecida na lista
  def adicionar(self, rota):
    i = 0
    for r in self.lista:
      if r.peso < rota.peso:
        i = i + 1
      else:
        break
    self.lista.insert(i, rota)

  # Atualiza uma rota conhecida na lista
  def atualizar(self, rota):
    for r in self.lista:
      if r == rota and r.peso != rota.peso:
        self.lista.remove(r)
        self.adicionar(rota)
        break

  def obtermelhoresrotas(self):
    menorpeso = self.lista[0].peso
    melhoresrotas = list()
    for r in self.lista:
      if r.peso == menorpeso:
        melhoresrotas.append(r)
      else:
        break

    return melhoresrotas

  def reduzirtempovida(self):
    for r in self.lista:
      r.tempovida = r.tempovida - 1
      if r.tempovida < 0:
        self.lista.remove(r)

  # Remove todas as rotas conhecidas
  # na lista onde o proximo é o ip
  # especificado
  def remover(self, prox):
    for r in self.lista:
      if r.prox == prox:
        self.lista.remove(r)

# Todas as rotas conhecidas na rede
class Distancias():
  # Construtor da classe
  def __init__(self, tdv):
    self.rotas = {}
    self.tempovida = tdv

  # adiciona uma rota à lista de rotas conhecidas
  def adicionar(self, ip, proximo, peso):
    rota = Rota(proximo, peso, self.tempovida)
    if not ip in self.rotas:
      rotas = Rotas()
      self.rotas[ip] = rotas
      self.rotas[ip].adicionar(rota)
    else:
      if rota in self.rotas[ip]:
        self.rotas[ip].atualizar(rota)
      else:
        self.rotas[ip].adicionar(rota)

  def checartempovida(self):
    for c in list(self.rotas.keys()):
      rotas = self.rotas[c]
      rotas.reduzirtempovida()
      if len(rotas) == 0:
        del self.rotas[c]

  def exibir(self):
    for (c, rotas) in self.rotas.items():
      print("{0: <15} {1}".format(c, rotas))

  # elimina da lista de rotas aquelas onde o destino
  # é o proximo da rota ou é a origem de onde
  #  a rota foi aprendida
  def obterpesos(self, ip):
    #ip: peso
    pesos = {}
    for c in list(self.rotas.keys()):
      rotas = self.rotas[c]
      if ip == c:
        continue
      rota = rotas.obtermelhoresrotas()[0]
      if ip == rota.prox:
        continue
      pesos[c] = rota.peso

    #adicionar a rota para ele mesmo
    pesos[parametros["ip"]] = 0

    return pesos

  # retorna quem é o próximo da rota para o 
  # ip especificado usando balanceamento de carga
  def obterproximo(self, ip):
    if ip in self.rotas.keys():
      rotas = self.rotas[ip].obtermelhoresrotas()
      quant = len(rotas)
      i = random.randrange(quant)
      return rotas[i].prox
    else:
      return None
  
  def removerproximo(self, ip):
    for c in list(self.rotas.keys()):
      rotas = self.rotas[c]
      rotas.remover(ip)
      if len(rotas) == 0:
        del self.rotas[c]

# Gerencia os enlaces na rede
class Enlaces():
  # Construtor da classe
  def __init__(self):
    self.lista = {}
    
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

# Thread para Enviar dados
class EnviaDadosThread(threading.Thread):
  def __init__(self, soquete):
    threading.Thread.__init__(self)
    msg = Mensagens(parametros['ip'])
    self.msgsproc = [msg.gerarAtualizacao, msg.gerarDados, msg.gerarRastreio, msg.gerarTabela]
    self.soquete = soquete
    self.fila = queue.Queue()
    self.ativa = True

  def desligar(self):
    self.ativa = False

  # Converte e envia
  def enviar(self, destino, tipo, conteudo):
    ip = distancias.obterproximo(destino)
    if ip != None:
      msg = self.msgsproc[tipo](destino, conteudo)
      pac = {'destino': ip, 'conteudo': msg}
      self.fila.put_nowait(pac)
      return True
    else:
      if destino == parametros["ip"]:
        msg = self.msgsproc[tipo](destino, conteudo)
        processathread.processar(msg)
        return True
      else:
        return False

  def repassar(self, destino, mensagem):
    ip = distancias.obterproximo(destino)
    if ip != None:
      pac = {'destino': ip, 'conteudo': json.dumps(mensagem).encode()}
      self.fila.put_nowait(pac)
      return True
    else:
      return False

  # enviar dados para o detino especificado
  def run(self):
    while(self.ativa):
      try:
        pac = self.fila.get(True, 1)
      except queue.Empty:
        continue
      endereco = (pac["destino"], parametros["porta"])
      try:
        self.soquete.sendto(pac['conteudo'], endereco)
        self.fila.task_done()
      except socket.timeout:
        continue
   
    # desconectando...
    self.soquete.close()        

# Gera e processa mensagens no formato JSON
class Mensagens:
  def __init__(self, ip):
    self.anaproc = {"update": self.analisarAtualizacao,
                    "data": self.analisarDados,
                    "trace": self.analisarRastro,
                    "table": 0}
    self.origem = ip

  def analisar(self, mensagem):
    dest = mensagem["destination"]
    tipo = mensagem["type"]
    analisarproc = self.anaproc[tipo]
    if dest == parametros["ip"] or tipo == "trace":
      analisarproc(mensagem)
    else:
      if not enviathread.repassar(dest, mensagem):
        origem = mensagem["source"]
        tipo = mensagem["type"]
        if tipo == "trace" or tipo == "table":
          enviathread.enviar(origem, MSG_DADOS, ROTA_NAOCONHECIDA.format(dest))

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

  def analisarRastro(self, mensagem):
    destino = mensagem["destination"]
    origem =  mensagem["source"]
    if destino != origem:
      mensagem["hops"].append(parametros["ip"])
    if destino == parametros["ip"]:
      enviathread.enviar(origem, MSG_DADOS, mensagem["hops"])
    else:
      enviathread.repassar(destino, mensagem)

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
    
  def gerarAtualizacao(self, destino, dists):
    msg = self.gerar(destino)
    msg["type"] = "update"
    msg["distances"] = dists
    
    return json.dumps(msg).encode()

  def gerarDados(self, destino, dados):
    msg = self.gerar(destino)
    msg["type"] = "data"
    msg["payload"] = dados

    return json.dumps(msg).encode()

  def gerarRastreio(self, destino, rastro):
    msg = self.gerar(destino)
    msg["type"] = "trace"
    rastro.append(parametros["ip"])
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
      distancias.checartempovida()
      dests = enlaces.obtertudo()
      for d in dests:
        dist = distancias.obterpesos(d)
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
    distancias.adicionar(ip, ip, peso)
    enlaces.adicionar(ip)
  else:
    print(ARGS_INSUFICIENTES.format(args[0]))

def cmd_del(args):
  if len(args) > 1:
    enlaces.remover(args[1])
    distancias.removerproximo(args[1])
  else:
    print(ARGS_INSUFICIENTES.format(args[0]))

def cmd_quit(args):
  app_sair()

def cmd_ip(args):
  print("\nConfiguração de IP:\n")
  print("    Endereço: . . . . : {0}".format(parametros['ip']))
  
def cmd_distances(args):
  print("IP              PESO  PROXIMO    TTL")
  print("====================================")
  distancias.exibir()

def cmd_links(args):
  print("\nEnlaces:\n")
  print("IP")
  print("==========================")
  enlaces.exibir()

def cmd_trace(args):
  if len(args) > 1:
    destino = args[1]
    if not enviathread.enviar(destino, MSG_RASTREIO, []):
      print(ROTA_NAOCONHECIDA.format(destino))
  else:
    print(ARGS_INSUFICIENTES.format(args[0]))

cmds_disponiveis = {
  "add": cmd_add,
  "del": cmd_del,
  "quit": cmd_quit,
  "trace": cmd_trace,
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
  distancias = Distancias(4 * parametros['periodo'])
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
