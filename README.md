# microml

A compiler from a simple ML-like language to C, and also a tree-walking
interpreter. This was made as an illustration of how to turn the code from
Eli Bendersky’s [blog post on type inference](https://eli.thegreenplace.net/2018/type-inference/)
into a simple compiler, with less than a few hundred lines added.

## Usage

You can open a REPL by typing `python main.py` at the top of this repository,
or execute a file by writing `python main.py <myfile>`.

The language looks roughly like this:

```ml
x y z = if y < z then y + z else y / z

(* we need a main function; no global expressions :( *)
main = lambda -> print(x(1,2))
```

And it will compile to C. It’s super small and minimal, but it shows you how to
turn the typed AST into C, and how to write an object-oriented tree-walking
interpreter.

If you’re in the REPL and want to find out what your current program would
evaluate to, type `:i`—for interpretation—or `:e`—for proper, compiled
execution.

<hr/>

Have fun!
