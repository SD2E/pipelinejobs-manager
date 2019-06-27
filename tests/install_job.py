"""Install a pipelinejob used in testing"""
import argparse
import json
import os
import sys
import yaml

from pprint import pprint
from datacatalog.linkedstores.pipelinejob import PipelineJobStore
from tacconfig import config

from fixtures import credentials, agave

CWD = os.getcwd()
HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)

def main(filename):

    settings = config.read_config(namespace="_REACTOR")
    jobstore = PipelineJobStore(settings.mongodb)
    jobdef = json.load(open(filename, 'r'))
    resp = jobstore.create(jobdef)
    if resp is not None:
        print('Loaded job {}'.format(resp['uuid']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", help="File containing job definition")
    args = parser.parse_args()
    main(args.filename)
