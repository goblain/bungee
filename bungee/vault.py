#!/usr/bin/python

import sys, os, hvac, string, random, tty, termios
from pprint import pprint
from base64 import b64encode

class Vault:
  client = False
  envpath = ''
  component = ''
  server = ''

  def generateSecret(self, secrettype):
    if secrettype == 'rand20' :
      length = 20
      chars = string.ascii_letters + string.digits + '!@#$%^&*()'
      random.seed = (os.urandom(1024))
      secret = ''.join(random.choice(chars) for i in range(length))
      return secret
    raise ValueError('Unknown secret type '+secrettype)

  def getSecretB64(self, path, secrettype='rand20'):
    return b64encode(self.getSecret(path, secrettype))

  def getChar(self):
    fd = sys.stdin.fileno()
    oldSettings = termios.tcgetattr(fd)
    try:
      tty.setraw(fd)
      answer = sys.stdin.read(1)
    finally:
      termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)
    return answer

  def getSecret(self, path, secrettype='rand20'):
    fullpath = self.envpath+'/'+self.component+'/'+path
    self.clientInit()
    secret = self.client.read(fullpath)
    # TODO: if missing prompt for creation or copying secret from another env
    # if no secret fetched use selected type and generate new secret using that type
    # returning the new value 
    if secret == None :
      print('Secret '+fullpath+' empty.')
      print(' 1) provide manually')
      print(' 2) generate automatically with '+secrettype+' profile')
      print(' q) quit')
      while True:
        mode = self.getChar()
        if mode == '1' :
          newsecret = raw_input('Enter your secret :')
          break
        elif mode == '2' :
          newsecret = self.generateSecret(secrettype)
          break
        elif mode == 'q' :
          sys.exit()
      print('Storing new secret '+fullpath)
      self.client.write(fullpath, value=newsecret)
      return(newsecret)
    return(secret['data']['value'])

  def clientInit(self):
    if not self.client:
      self.client = hvac.Client(url=self.server, token=os.environ['VAULT_TOKEN'])
      print("Vault client init")

#    print(os.environ['VAULT_TOKEN'])
#    self.client = hvac.Client(url='https://vault.nwt.stpdev.io')

