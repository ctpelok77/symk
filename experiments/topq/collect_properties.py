#! /usr/bin/env python
# -*- coding: utf-8 -*-


import glob, os, sys
import json




if __name__ == "__main__":
    ret = {}
    for f in glob.glob(os.path.join(sys.argv[1],"runs-*", "*")):
        # get properties and static-properties
        with open(os.path.join(f,"properties"), 'r') as p:
            prop = json.load(p)
            with open(os.path.join(f,"static-properties"), 'r') as sp:
                sprop = json.load(sp)
                for k in sprop:
                    prop[k] = sprop[k]
            ret[f] = prop

    with open("properties", "w") as wf:
        json.dump(ret, wf,  indent = 4)
