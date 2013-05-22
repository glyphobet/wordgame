#!/usr/bin/env python
import os
import sys
import argparse
import subprocess

DICTIONARY = 'scrabble'
ACK = 'ack-5.12'


def _fib(n):
    if n <= 1:
        return 1
    return _fib(n-1) + _fib(n-2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()  # prog="%s %s" % (__package__, help.__name__), description=help.__doc__)
    parser.add_argument('-i',       '--include', dest='include', type=set, nargs='?', action='store',  default=set(), help="")
    parser.add_argument('-e', '-x', '--exclude', dest='exclude', type=set, nargs='?', action='store',  default=set(), help="")
    parser.add_argument('-p',       '--prefer',  dest='prefer',  type=str, nargs='?', action='store',  default=str(), help="")
    parser.add_argument('-m',       '--match',   dest='match',   type=str, nargs='+', action='append', default=None,  help="")
    here = os.path.split(os.path.realpath(__file__))[0]
    parser.add_argument(
        '-d', '--dictionary', dest='dictionary', type=str, nargs='?',
        action='store', default=os.path.join(here, DICTIONARY),
        help="",
    )
    args = parser.parse_args(sys.argv[1:])
    if args.include & args.exclude:
        sys.exit("Can't include and exclude '{}'".format(''.join(args.include & args.exclude)))
    if set(args.prefer) & args.exclude:
        sys.exit("Can't prefer and exclude '{}'".format(''.join(set(args.prefer) & args.exclude)))

    freqpath = args.dictionary + '.frequency'
    if not os.access(freqpath, os.R_OK):
        freqdict = {}
        with open(args.dictionary, 'r') as dictionary:
            for line in dictionary:
                for char in line.lower().strip():
                    freqdict[char] = freqdict.get(char, 0) + 1
        frequency = ''.join(reversed(sorted(freqdict.keys(), key=lambda c: freqdict[c])))
        try:
            with open(freqpath, 'w') as freqfile:
                freqfile.write(frequency)
        except IOError as exc:
            print exc
    else:
        frequency = open(freqpath, 'r').read().strip()

    fib = [_fib(n) for n in range(len(frequency)+1)]

    commands = []

    for mm in args.match or []:
        for m in mm:
            commands.append((ACK, "{}".format(m)))

    # this baby here is a "Schwartzian Transform", look it up:
    for (c, p) in sorted(
        [(i, 26-frequency.index(i)) for i in args.include] +
        [(e,    frequency.index(e)) for e in args.exclude],
        key=lambda pair: pair[1]
    ):
        if c in args.include:
            commands.append((ACK, '{}'.format(c)))
        elif c in args.exclude:
            commands.append((ACK, '-v', '{}'.format(c)))

    newcmd = subprocess.Popen(('cat', args.dictionary), stdout=subprocess.PIPE)

    while commands:
        oldcmd, newcmd = newcmd, subprocess.Popen(commands.pop(0), stdin=newcmd.stdout, stdout=subprocess.PIPE)
        oldcmd.stdout.close()

    # remove duplicates from prefer list but keep it sorted
    args.prefer = ''.join(sorted(list(set(args.prefer)), key=lambda c: args.prefer.index(c)))

    def score(word):
        s = 0
        for i, c in enumerate(args.prefer):
            s += fib[len(args.prefer)-i] * word.count(c)
        return s

    words = newcmd.communicate()[0][:-1].split('\n')
    words.sort(key=score)
    for w in words:
        print(w)
