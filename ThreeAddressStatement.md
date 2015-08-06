# Three Address Statement #

A type of intermediate code made up of three operands and one operator.  The general form is `A = B op C`.  For example, the source statement: `A = B + C * D` would be broken down into the following three address statements as intermediate code (here `T1` is a temporary variable created by the compiler):

  * `T1 = C * D`
  * `A = B + T1`

Several other forms of three address statements are also used:

  * `A = op B`
  * `A = B`
  * `A =[] B C`
    * since the `[]` are to the right of the =, this is interpreted as: `A = B[C]`.
  * `A []= B C`
    * since the `[]` are to the left of the =, this is interpreted as: `A[B] = C`.
  * `if B op C goto label`

Compare to DirectedAcyclicGraph