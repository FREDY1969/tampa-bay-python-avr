An _abstract syntax tree_ (AST) is just a way to represent the syntactic structure of a program.

An AST is generally what is produced by the compiler front-end (the scanner and parser) and feeds the IntermediateCode generation.

This tree structure may be represented as nested tuples, objects, or any number of other data structures.

For this compiler, the AST is stored in a relational table format in the [Database](Database.md).  In this case, each node in the tree is coded as a row in the database and given a unique id.  Each row includes the line and column numbers defining where this node is textually located within the source file.  (This would be necessary for later error reporting from the compiler back-end, as well as cross-referencing in the IDE).

## Example ##

Using Python syntax, the input to the parser might look like:

```
   def fact(n):
      if n == 0: return 1     # this also works for 1, because it becomes 1 * 1.
      return n * fact(n - 1)
```

And, if the AST is represented as tuples, the output might look like:

```
   (def fact (arglist (positional_args (n)) (optional_args ()) (rest_arg None))
       (docstring None)
       (series
           ((if (== n 0) (return 1))
            (return (* n (fact (- n 1))))
           )))
```

As rows in an AST\_node table, it would look something like:

| id | name            | line\_no | column\_no | parent\_node\_id | parent\_position |
|:---|:----------------|:---------|:-----------|:-----------------|:-----------------|
| 1  | def             |       1  |         1  |           NULL   |            NULL  |
| 2  | fact            |       1  |         5  |              1   |               1  |
| 3  | arglist         |       1  |         9  |              1   |               2  |
| 4  | positional\_args |       1  |         9  |              3   |               1  |
| 5  | n               |       1  |        10  |              4   |               1  |
| 6  | optional\_args   |       1  |        10  |              3   |               2  |
| 7  | rest\_arg        |       1  |        10  |              3   |               3  |
| 8  | docstring       |       2  |         4  |              1   |               3  |
| 9  | series          |       2  |         4  |              1   |               4  |
| 10 | if              |       2  |         4  |              9   |               1  |
| 11 | ==              |       2  |         9  |             10   |               1  |
| 12 | n               |       2  |         7  |             11   |               1  |
| 13 | 0               |       2  |        12  |             11   |               2  |
| 14 | return          |       2  |        15  |             10   |               2  |
| 15 | 1               |       2  |        22  |             14   |               1  |
| 16 | return          |       3  |         4  |              9   |               2  |
| 17 | `*`             |       3  |        13  |             16   |               1  |
| 18 | n               |       3  |        11  |             17   |               1  |
| 19 | fact            |       3  |        15  |             17   |               2  |
| 20 | -               |       3  |        22  |             19   |               1  |
| 21 | n               |       3  |        20  |             20   |               1  |
| 22 | 1               |       3  |        24  |             20   |               2  |

It is a little more complicated than this because it is necessary to distinguish between several kinds of nodes.  These different kinds of nodes share the following database columns:

  * kind
  * label
  * symbol\_id
  * int1
  * int2
  * str1
  * str2 (not used, but leaving it here for the moment)

as follows:

| kind   | label | symbol\_id |  int1  |  int2  | str1 | str2 | Notes |
|:-------|:------|:-----------|:-------|:-------|:-----|:-----|:------|
| approx | -     | -          | number as int | binary\_pt | -    | -    | actual number is int1 `*` 2<sup>int2</sup> |
| int    |   -   |     -      | integer |  -     |  -   |  -   |       |
| ratio  |   -   |     -      | numerator | denominator | -    | -    |       |
| string |   -   |     -      |   -    |   -    | string | -    |       |
| call   |   -   |     -      |   -    | -      | -    | -    | fn in first arg |
| word   | word label | id in symbol\_table | -      | -      | -    |  -   |       |
| ioreg  | ioreg name (e.g., 'io.portb') | -          | -      | -      | -    | -    |       |
| ioreg-bit | ioreg name (e.g., 'io.portb') | -          | bit#   | -      | -    | -    |       |
| no-op  |   -   |     -      |   -    |   -    |  -   |  -   |       |
| label  | label |     -      |   -    |   -    |  -   |  -   |       |
| jump   | target |     -      |   -    |   -    |  -   |  -   |       |
| if-true | jump-true label | -          | -      |   -    |  -   |  -   | first arg is condition |
| if-false | jump-false label | -          | -      |   -    |  -   |  -   | first arg is condition |
| series |   -   |     -      |   -    | -      | -    | -    | args are statements to splice in |
| None   |   -   |     -      | -      | -      | -    | -    | line, column info not set |