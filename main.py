#!/usr/bin/env python
import readline
import sys

from microml import compiler, exceptions

def repl():
    c = compiler.Compiler()

    while True:
        try:
            line = input('> ')
        except (EOFError, KeyboardInterrupt):
            print('\nMoriturus te saluto!')
            return

        if not line:
            continue

        if line in [':q', 'quit']:
            print('Moriturus te saluto!')
            return

        if line in [':i', 'interpret']:
            try:
                c.interpret()
            except exceptions.MLException as e:
                print('{}: {}'.format(e.module, e))
            continue

        if line in [':e', 'execute']:
            try:
                c.execute()
            except exceptions.MLException as e:
                print('{}: {}'.format(e.module, e))
            continue

        try:
            c.compile(line)
        except exceptions.MLException as e:
            print('{}: {}'.format(e.module, e))


def main():
    if len(sys.argv) == 1:
        return repl()
    c = compiler.Compiler(interactive=False)
    with open(sys.argv[1]) as f:
        contents = f.read()
    while contents:
        stop = c.compile(contents)
        if not stop:
            break
        contents = contents[stop:]
    c.execute()


if __name__ == '__main__':
    try:
        main()
    except exceptions.MLException as e:
        print('{}: {}'.format(e.module, e))
