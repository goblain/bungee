#!/usr/bin/python

import sys, yaml, os, boto.ec2.elb, boto.cloudformation, boto.exception, json
from pprint import pprint
from jinja2 import Environment, DictLoader
from urllib2 import urlopen
from base64 import b64encode
import hvac
import ConfigParser
import getopt
import types
import collections
import re
from vault import Vault 
from subprocess import Popen, PIPE, STDOUT

# TODO: checksum setup files to apply only changed ones
# TODO: --reapply to reapply regardless of checksum
# TODO: verify if kubectl works
# TODO: verify if kubectl can access cluster
# TODO: verify if namespace exists

class Core:

  def kubeApplyString(self, manifest):
    for cluster in self.env['clusters'] :
#      p = Popen(['/opt/bin/kubectl', '--context', cluster['context'], '--namespace', cluster['namespace'], 'apply', '-f', '-'], stdin=PIPE, shell=True)
      p = Popen('kubectl --context '+cluster['context']+' --namespace '+cluster['namespace']+' apply -f -', stdin=PIPE, shell=True)
      p.communicate(manifest)
      p.wait()
#      os.system('kubectl --context '+cluster['context']+' --namespace '+cluster['namespace']+' apply -f '+path)
  
  def kubeApplyFile(self, path):
    for cluster in self.env['clusters'] :
      os.system('kubectl --context '+cluster['context']+' --namespace '+cluster['namespace']+' apply -f '+path)

  def vaultSecret(self, path, secrettype):
    self.vaulter.getSecretB64(path, secrettype)
    return()
  
  def kubeApplyTemplate(self, path):
    # TODO: result can contain secrets, store and apply from memory rather then on disk
    print("JINJA template "+path)
    with open(path, 'r') as tplfile:
      jinjaEnv = Environment(loader = DictLoader({'kubetpl': tplfile.read()}))
      jinjaEnv.globals.update(vault = self.vaulter.getSecret)
      template = jinjaEnv.get_template('kubetpl')
      print(template.render())
      self.kubeApplyString(template.render())
  
  def setup(self, component, env):
    # TODO: evaluate all templates first before applying any object
    # TODO: investigate possibility to validate manifests before applying
    print('Setup for component '+component+' started...')
    for folder in ('setup-common', 'setup-'+env) :
      path = self.basepath+'/'+component+'/'+folder
      if os.path.isdir(path):
        r = re.compile('.*\.yml$')
        for file in filter(r.match, os.listdir(path)):
          self.kubeApplyFile(path+'/'+file)
        r = re.compile('.*\.yml\.j2$')
        for file in filter(r.match, os.listdir(path)):
          self.kubeApplyTemplate(path+'/'+file)
  
  def deploy(self, component, env):
    # TODO: report in progress to deploy version log
    # TODO: report failure/success to deploy version log
    path = self.basepath+'/'+component+'/deploy'
    if os.path.isdir(path):
      r = re.compile('.*\.yml$')
      for file in filter(r.match, os.listdir(path)):
        self.kubeApplyFile(path+'/'+file)
      r = re.compile('.*\.yml\.j2$')
      for file in filter(r.match, os.listdir(path)):
        self.kubeApplyTemplate(path+'/'+file)
  
  def main(self):
    env = sys.argv[1]
    stage = sys.argv[2]
    component = sys.argv[3]
    context = ''
  
#    self.conf = Config()
    self.vaulter = Vault()
  
    configfile = "Bungeefile"
    while not os.path.isfile(configfile):
      configfile = "../"+configfile
      if os.path.abspath(configfile) == '/Bungeefile' :
        raise ValueError("No Bungeefile found")
    self.basepath = os.path.dirname(os.path.abspath(configfile))
  
    stream = open(configfile,'r')
    tmp = yaml.safe_load(stream)
    
    envs = tmp['envs']
    self.env = envs[env]

    self.vaulter.envpath = tmp['plugins']['vault']['path']+'/'+env
    self.vaulter.component = component
    self.vaulter.server = tmp['plugins']['vault']['server']
    
    if stage not in ('setup', 'deploy'):
      pprint("Stage '"+stage+"' not recognised")
      os.exit(1)
    
    if stage == 'setup' :
      self.setup(component, env)
    elif stage == 'deploy' :
      self.deploy(component, env)
    else :
      pprint("Unrecognised stage, usage : bungee <env> <stage> <component>")
  
