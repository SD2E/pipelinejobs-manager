"""Install a pipeline used in testing"""
import argparse
import json
import os
import sys
import yaml

from pprint import pprint
from datacatalog.linkedstores.pipeline import PipelineStore
from tacconfig import config

from fixtures import credentials, agave

CWD = os.getcwd()
HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)

def main(filename):

    settings = config.read_config(namespace="_REACTOR")
    pipestore = PipelineStore(settings.mongodb)
    pipedef = json.load(open(filename, 'r'))
    resp = pipestore.add_update_document(pipedef)
    if resp is not None:
        print('Loaded pipeline {}'.format(resp['uuid']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", help="File containing pipeline definition")
    args = parser.parse_args()
    main(args.filename)
