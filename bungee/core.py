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
      p = Popen('kubectl --context '+cluster['context']+' --namespace '+cluster['namespace']+' apply -f -', stdin=PIPE, shell=True)
      p.communicate(manifest)
      p.wait()
  
  def kubeApplyFile(self, path):
    for cluster in self.env['clusters'] :
      os.system('kubectl --context '+cluster['context']+' --namespace '+cluster['namespace']+' apply -f '+path)

  def vaultSecret(self, path, secrettype):
    self.vaulter.getSecretB64(path, secrettype)
    return()
  
  def kubeApplyTemplate(self, path):
    # as result can contain secrets, store and apply from memory rather then on disk
    with open(path, 'r') as tplfile:
      jinjaEnv = Environment(loader = DictLoader({'kubetpl': tplfile.read()}))
      jinjaEnv.globals.update(vaultb64 = self.vaulter.getSecretB64)
      jinjaEnv.globals.update(vault = self.vaulter.getSecret)
      template = jinjaEnv.get_template('kubetpl')
      print(template.render(env=self.env['name']))
      self.kubeApplyString(template.render(env=self.env['name']))

  # Compile list of files to apply in alphabetic order and overloading
  def applyFolders(self, component, folders):
    catalog = {}
    for folder in folders:
      path = self.basepath+'/'+component+'/'+folder
      if os.path.isdir(path):
        for mfile in os.listdir(path):
          catalog[mfile] = path+'/'+mfile
    pprint(catalog)
    for itemkey in catalog:
      pprint(catalog[itemkey])
      if catalog[itemkey].endswith('.j2'):
        self.kubeApplyTemplate(catalog[itemkey])
      elif catalog[itemkey].endswith('.yml'):
        self.kubeApplyFile(catalog[itemkey])
      else:
        print('Unsupported file '+catalog[itemkey])
  
  def setup(self, component, env):
    # TODO: evaluate all templates first before applying any object
    # TODO: investigate possibility to validate manifests before applying
    print('Setup for component '+component+' started...')
    self.applyFolders(component, ['setup-common', 'setup-'+env])
  
  def deploy(self, component, env):
    # TODO: report in progress to deploy version log
    # TODO: report failure/success to deploy version log
    print('Deploy for component '+component+' started...')
    self.applyFolders(component, ['deploy', 'deploy-'+env])
  
  def main(self):
    env = sys.argv[1]
    stage = sys.argv[2]
    component = sys.argv[3]
    context = ''
  
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
    self.env['name'] = env

    if tmp['plugins']:
      if tmp['plugins']['vault']:
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
  
