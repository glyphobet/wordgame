#!/usr/bin/env python
import os
import sys
import argparse
import subprocess

DICTIONARY = 'scrabble'
GREPS = ['ack-5.12', 'ack', 'grep']


def _fib(n):
    if n <= 1:
        return 1
    return _fib(n-1) + _fib(n-2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()  # prog="%s %s" % (__package__, help.__name__), description=help.__doc__)
    parser.add_argument('-i',       '--include', dest='include', type=set, nargs='?', action='store',  default=set(), const=set(), help="One or more letters that must be included in the result words.")
    parser.add_argument('-e', '-x', '--exclude', dest='exclude', type=set, nargs='?', action='store',  default=set(), const=set(), help="One or more letters that must be excluded from the result words.")
    parser.add_argument('-p',       '--prefer',  dest='prefer',  type=str, nargs='?', action='store',  default=str(), const=set(), help="One or more letters that could be in the result words, in order of preference.")
    parser.add_argument('-r',       '--rank',    dest='rank',    type=str, nargs='?', action='store',  default='fib', const='fib', choices=['fib', 'lin'], help="The ranking algorithm to use to sort solutions based on --prefer.")
    parser.add_argument('-m',       '--match',   dest='match',   type=str, nargs='+', action='append', default=None,  help="One or more regular expression patterns that the result words must match.")
    parser.add_argument('-g',       '--grep',    dest='grep',    type=str, nargs='?', action='store',  default='',    help="Grep-like command to use. Tries to use ack, then falls back to grep.")
    here = os.path.split(os.path.realpath(__file__))[0]
    parser.add_argument(
        '-d', '--dictionary', dest='dictionary', type=str, nargs='?',
        action='store', default=os.path.join(here, DICTIONARY),
        help="The word list to use. Defaults to the Scrabble word list.",
    )
    args = parser.parse_args(sys.argv[1:])
    if args.include & args.exclude:
        sys.exit("Can't include and exclude '{}'".format(''.join(args.include & args.exclude)))
    if set(args.prefer) & args.exclude:
        sys.exit("Can't prefer and exclude '{}'".format(''.join(set(args.prefer) & args.exclude)))

    if args.grep:
        GREPS = [args.grep] + GREPS
    for g in GREPS:
        if subprocess.call(['which', g], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
            args.grep = g
            break

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
                freqfile.write(frequency + '\n')
        except IOError as exc:
            print exc
    else:
        frequency = open(freqpath, 'r').read().strip()

    commands = []

    for mm in args.match or []:
        for m in mm:
            commands.append((args.grep, "{}".format(m)))

    # this baby here is a "Schwartzian Transform", look it up:
    for (c, p) in sorted(
        [(i, 26-frequency.index(i)) for i in args.include] +
        [(e,    frequency.index(e)) for e in args.exclude],
        key=lambda pair: pair[1]
    ):
        if c in args.include:
            commands.append((args.grep, '{}'.format(c)))
        elif c in args.exclude:
            commands.append((args.grep, '-v', '{}'.format(c)))

    newcmd = subprocess.Popen(('cat', args.dictionary), stdout=subprocess.PIPE)

    while commands:
        oldcmd, newcmd = newcmd, subprocess.Popen(commands.pop(0), stdin=newcmd.stdout, stdout=subprocess.PIPE)
        oldcmd.stdout.close()

    # remove duplicates from prefer list but keep it sorted
    args.prefer = ''.join(sorted(list(set(args.prefer)), key=lambda c: args.prefer.index(c)))

    if args.rank == 'fib':
        fib = [_fib(n) for n in range(len(frequency)+1)]

    rank = {
        # linear scoring; treats each character equally
        'lin': lambda word: sum(word.count(c) for c in args.prefer),
        # fibbonacci scoring: ranks each character in descending
        # order. A word with character N has the same rank as a
        # word with characters N-1 and N-2.
        'fib': lambda word: sum(
            fib[len(args.prefer)-i] * word.count(c)
            for (i, c) in enumerate(args.prefer)
        ),
    }[args.rank]

    words = newcmd.communicate()[0][:-1].split('\n')
    words.sort(key=rank)
    for w in words:
        print(w)
