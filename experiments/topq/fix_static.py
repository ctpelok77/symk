#! /usr/bin/env python
# -*- coding: utf-8 -*-


import glob, os, sys
import json




if __name__ == "__main__":
    ret = {}
    for f in glob.glob(os.path.join(sys.argv[1],"runs-*", "*")):
        # get static-properties
        prop = {}
        with open(os.path.join(f,"static-properties"), 'r') as p:
            prop = json.load(p)
            q = prop['q']
            prop['id'].append(str(q))
            prop['algorithm'] = 'sym-' + prop['algorithm']

        with open(os.path.join(f, "static-properties2"), "w") as wf:
            json.dump(prop, wf,  indent = 4)
