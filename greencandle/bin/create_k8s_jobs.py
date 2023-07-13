#!/usr/bin/env python
#pylint: disable=consider-using-with,cell-var-from-loop

"""
Create k8s job files using template file and given substitution variables
"""

import os
import re
import argparse

def main():
    """
    Take substitution vars from agruments and create one output file per job
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--year', type=str, required=True)
    parser.add_argument('-n', '--name', type=str, required=True)
    parser.add_argument('-c', '--configenv', type=str, required=True)
    parser.add_argument('-i', '--interval', type=str, required=True)
    args = parser.parse_args()

    contents = open('test-job.yml', 'r').read()
    pairs = open('good_pairs.txt', 'r').read().splitlines()
    os.mkdir(args.name.lower())

    for pair in pairs:


        rep = {"$ENV": args.configenv, "$ITEM": pair.strip().lower(),
               "$STRATEGY": args.name.lower(), "$YEAR": args.year, "$INTERVAL": args.interval}

        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        text = pattern.sub(lambda m: rep[re.escape(m.group(0))], contents)

        with open(f'{args.name.lower()}/job-{pair}.yaml', 'w') as handle:
            handle.write(text)

if __name__ == '__main__':
    main()
