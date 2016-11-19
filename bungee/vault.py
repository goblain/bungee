#!/usr/bin/python

import sys, os, hvac, string, random
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

  def getSecret(self, path, secrettype='rand20'):
    fullpath = self.envpath+'/'+self.component+'/'+path
    self.clientInit()
    secret = self.client.read(fullpath)
    # TODO: if missing prompt for creation or copying secret from another env
    # if no secret fetched use selected type and generate new secret using that type
    # returning the new value 
    if secret == None :
      newsecret = self.generateSecret(secrettype)
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

