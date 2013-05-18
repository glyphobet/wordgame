#!/usr/bin/env python
import os
import sys
import argparse
import subprocess

DICTIONARY = './dictionary'
ACK = 'ack-5.12'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()  # prog="%s %s" % (__package__, help.__name__), description=help.__doc__)
    parser.add_argument('-i', '--include', dest='include', type=set, nargs='?', action='store', default=set(), help="")
    parser.add_argument('-e', '--exclude', dest='exclude', type=set, nargs='?', action='store', default=set(), help="")
    parser.add_argument('-p', '--prefer',  dest='prefer',  type=str, nargs='?', action='store', default=str(), help="")
    parser.add_argument('-m', '--match',   dest='match',   type=str, nargs='?', action='store', default=None,  help="")
    args = parser.parse_args(sys.argv[1:])
    if args.include & args.exclude:
        sys.exit("Can't include and exclude '{}'".format(''.join(args.include & args.exclude)))
    if set(args.prefer) & args.exclude:
        sys.exit("Can't prefer and exclude '{}'".format(''.join(set(args.prefer) & args.exclude)))

    freqpath = DICTIONARY + '.frequency'
    if not os.access(freqpath, os.R_OK):
        freqdict = {}
        with open(DICTIONARY, 'r') as dictionary:
            for line in dictionary:
                for char in line.strip():
                    freqdict[char] = freqdict.get(char, 0) + 1
        frequency = ''.join(reversed(sorted(freqdict.keys(), key=lambda c: freqdict[c])))
        with open(freqpath, 'w') as freqfile:
            freqfile.write(frequency)
    else:
        frequency = open(freqpath, 'r').read().strip()

    commands = []

    if args.match is not None:
        commands.append((ACK, "{}".format(args.match)))

    for (c, p) in sorted(
        [(i, 26-frequency.index(i)) for i in args.include] +
        [(e,    frequency.index(e)) for e in args.exclude],
        key=lambda pair: pair[1]
    ):
        if c in args.include:
            commands.append((ACK, '{}'.format(c)))
        elif c in args.exclude:
            commands.append((ACK, '-v', '{}'.format(c)))

    cmd = subprocess.Popen(('cat', DICTIONARY), stdout=subprocess.PIPE)

    while commands:
        cmd = subprocess.Popen(commands.pop(0), stdin=cmd.stdout, stdout=subprocess.PIPE)
    print cmd.communicate()[0]
