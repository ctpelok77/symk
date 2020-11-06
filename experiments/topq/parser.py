#! /usr/bin/env python
# -*- coding: utf-8 -*-


"""
Plan length: 6 step(s).
Plan cost: 6
Actual search time: 0.0162667s [t=0.332438s]
Bytes per state: 4
Search time: 0.0192778s
Search-Wall time: 0.170252s
Total time: 0.332448s
Solutions found.
Peak memory: 434316 KB
Remove intermediate file output.sas
"""

import re
import glob, os, sys
import json
import itertools

from lab.parser import Parser

print("Parsing with custom parser")

_PLAN_INFO_REGEX = re.compile(r"; cost = (\d+) \((unit cost|general cost)\)\n")

def get_plan_cost(path):
    try:
        with open(path) as input_file:
            line = None
            for line in input_file:
                if line.strip().startswith(";"):
                    continue
            # line is now the last line
            match = _PLAN_INFO_REGEX.match(line)
            if match:
                return int(match.group(1))
            return None
    except:
        return None


def get_plan_costs(plans_folder):
    ret = []
    for counter in itertools.count(1):
        name = "sas_plan.%d" % counter
        plan_filename = os.path.join(plans_folder, name)
        if not os.path.exists(plan_filename):
            break
        cost = get_plan_cost(plan_filename)
        if cost is not None:
            ret.append(cost)
    return ret

def plans(content, props):
    costs = get_plan_costs('found_plans')
    props["plan_costs"] = costs
    props["num_plans"] = len(costs)

def get_k(props):
    return 10000
    #return props["k"]


def coverage(content, props):
    finished = 'total_time' in props
    k_bound_reached = props["num_plans"] >= get_k(props)
    props["coverage"] = int(finished and not k_bound_reached)



parser = Parser()

parser.add_function(plans)
parser.add_pattern('search_time', r'Search time: (.+)s', required=False, type=float)
parser.add_pattern('total_time', r'Total time: (.+)s', required=False, type=float)
parser.add_pattern('raw_memory', r'Peak memory: (\d+) KB', required=False, type=int)
parser.add_function(coverage)




parser.parse()
