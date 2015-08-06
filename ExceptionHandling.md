The language will initially support simple forms of exception handling and finalization.

## Exception Handling ##

Rather than using classes to represent the exceptions, simple integers will be used, and probably without any additional arguments.

Also, there will be no provision to trap individual exceptions.  It will be up to the user code to figure out whether the exception caught is interesting or not.

Rather than a **try**/**except** construct, exception logic is placed in individual statements with an **on error** clause, something like:

```
    some statement on error:
        error code here
```

or

```
    some statement
    on error:
        error code here
```

Doing this on a **for** statement catches errors from the iterator:

```
    for x in iterator:
        do stuff with x
    on error:
        handle error from iterator
```

## Finalization ##

Finalization will be handled by a **with** statement:

```
    with x as expr:
        do stuff with x
```

When the **with** clause is exited, the "done" function for the expression is run (which "done" function to run is determined at compile time -- e.g., close for I/O ports, unlock for locks, etc).