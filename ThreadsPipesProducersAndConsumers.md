DontYouLikeTheseCamelCaseTitlesThatAreSoUnlikeRest?

# Producers and Consumers #

Generally producers (like generators and iterators in Python) are functions that are [not stack based](FunctionActivationRecord#Where_do_we_put_these_things%3F.md), while consumers may or may not be stack based.

Calling a producer loads the arguments passed (but not the caller's FAR/PC) into the FunctionActivationRecord (FAR) and returns it.

This producer FAR can be passed to a consumer function that calls **start** on it passing a [Pipe](#Pipe.md) primed with the PC of the for\_body.  The **start** doesn't return until the producer returns.  (This is how the end of data is indicated).

So, the **for** statement in the consumer:

```
    for x in producer_far:
        do stuff with x
```

Translates into (for information about **with**, see [ExceptionHandling](ExceptionHandling#Finalization.md)):

```
    with pipe(for_body) as p:
        start(producer_far, p)   # Doesn't return until the producer is out of values.
        jmp for_done

        label for_body           # The first _switch_ by the producer comes here.
        pop x                    # Store return value from pipe in x.
        do stuff with x
        switch p                 # Bounces back to the producer (see below).
        jmp for_body

        label for_done
        pop_with                 # Disables the with clause.

    # A _break_ jmps here, which activates the with clause, terminating the producer.
    label for_end
    ...
```

(Note that this means that the return PC must be stored in the called FAR, not the caller's FAR; because the caller's FAR has multiple return PCs -- the return PC for **start**, and the return PC in the for\_body).

The goal is to allow both the producer and the consumer to pass the pipe object to subordinate functions that can then use it in their place.

## Pipe ##

The pipe (do we need a better name for this?) is just a place to store a return FAR and PC.  When the producer is running, the consumer's FAR and PC are stored in the pipe.  When the consumer is running, the producer's FAR and PC are stored in the pipe.  The **switch** function is used to toggle back and forth between executing the producer and executing the consumer.  It stores the caller's FAR and PC in the pipe and jumps to the FAR/PC that was just overwritten.

### start ###

The **start** function stores the caller's FAR/PC in the producer\_far (as the return FAR/PC), stores the pipe as if another argument had been passed to the producer\_far, and then starts the producer\_far.

The _done_ function registered in the **with** statement when the pipe is created finalizes the return FAR stored in the pipe (which would be the producer's FAR).

### switch ###

The **switch** function returns the value passed to the FAR/PC stored in the pipe, while setting the pipe up so that the next **switch** on the pipe will return from this one.

```
    def switch(pipe, value):
        target = pipe.FAR_PC

        # to return back to caller later (bypassing this call to switch)
        pipe.FAR_PC = caller FAR_PC

        push value                  # or however values are returned to functions...
        jump to target              # Also popping the FAR for switch itself off the stack.
```

# Example #

Consider the following example where a **Caller** wants to send the output of **produce(0, 10)** to **consume**:

![http://groups.google.com/group/tampa-bay-python-avr/web/threads1.png](http://groups.google.com/group/tampa-bay-python-avr/web/threads1.png)

The sequence of execution is:

  1. **Caller**, line 2, calls **produce(0, 10)**, which initializes the (static) **produce\_FAR** (lower left of dotted box) and sets the **a** and **b** parameters (but not **ret\_FAR** and **ret\_PC**).  Rather than executing **produce**, the FAR is simply returned.
  1. **Caller**, line 2, passes the returned FAR to **consume**, which initializes the (static) **consume\_FAR** (lower right of dotted box), setting **prod** to the FAR returned in step 1 and **ret\_FAR** and **ret\_PC** to return to the **Caller**, line 3.  Execution then goes to the **consume** function.
  1. **consume**, line 2, creates a pipe object (shown at the bottom of the diagram), passing a PC of line 5 (the location of the **for\_body** label).  The pipe's FAR and PC are set to the **consumer\_FAR**, at line 5.
  1. **consume**, line 3, calls **start** on the **produce\_FAR**, passing the pipe.  This sets **p** in the **produce\_FAR** to the pipe passed, and **ret\_FAR**/**ret\_PC** in the **produce\_FAR** to **consume\_FAR**, line 4 (the line after the **start** call).  Execution then goes to the **produce** function (for the first time).

At this point, all of the data values are as they are shown in the diagram above.

Following the sequence of execution further:

  1. **produce**, line 1, sets x to 0.
  1. **produce**, line 3, checks x against b.  This check fails, so line 4 is skipped.
  1. **produce**, line 5, calls **switch** on the pipe, passing 0.  **Switch** remembers the **ret\_FAR**/**ret\_PC** stored in the pipe (**consume\_FAR**/line 5), stores its caller's FAR/PC into the pipe's **ret\_FAR**/**ret\_PC**, and then jumps to **consume\_FAR**, line 5 passing 0.

Now all of the data values are as shown in the diagram below.

![http://groups.google.com/group/tampa-bay-python-avr/web/threads2.png](http://groups.google.com/group/tampa-bay-python-avr/web/threads2.png)

Taking this one more step:

  1. **consume**, line 6, pops 0 into x.
  1. **consume**, line 7, prints 0.
  1. **consume**, line 8, calls **switch** on the pipe.  **Switch** remembers the **ret\_FAR**/**ret\_PC** stored in the pipe (**produce\_FAR**/line 6), stores its caller's FAR/PC into the pipe's **ret\_FAR**/**ret\_PC**, and then jumps to **produce\_FAR**, line 6.

The final diagram below shows all of the data at this point.  The rest of the execution is left as an exercise for the reader.  Pay particular attention to what happens when **produce** is done and executes its **ret**, which jumps to the **ret\_FAR**/**ret\_PC** saved in **produce\_FAR**.

![http://groups.google.com/group/tampa-bay-python-avr/web/threads3.png](http://groups.google.com/group/tampa-bay-python-avr/web/threads3.png)


# Interrupt Handling #

## Output Interrupts ##

An output interrupt is generated by the hardware when it is ready to accept another byte for output to some hardware device.

The hardware device is coupled to a (non-stack based) producer through interrupts as follows:

The interrupt has an associated (non-stack based) put\_fun that accepts data from the producer through a pipe, and sends it to the hardware device.

The pseudo-code for the put\_fun is:

```
    def put_fun(p):
        value = switch p
        while I/O_reg & I/O_bit:       # hardware ready for another byte!
            label continue             # ISR picks up here (see below)
            send value to hardware
            value = switch p
        enable ready_for_data interrupt
        jump to dispatch
```

And the pseudo-code for the **ready\_for\_data** interrupt service routine is:

```
    def ready_for_data_ISR():
        disable ready_for_data interrupt
        schedule put_fn.continue
```

## Input Interrupts ##

An input interrupt is generated by the hardware when it has received another byte from some hardware device.

The hardware device can be coupled to a (non-stack based) consumer through interrupts as follows:

The interrupt has an associated (non-stack based) get\_fun that gets data from the hardware device and forwards it to the consumer through a pipe.

The pseudo-code for the get\_fun is:

```
    def get_fun(p):
        while I/O_reg & I/O_got_data_bit:       # hardware has another byte!
            value = data from hardware
            label continue                      # ISR picks up here (see below)
            switch p(value)
        enable got_data interrupt
        jump to dispatch
```

And the pseudo-code for the **got\_data** interrupt service routine is:

```
    def got_data_ISR():
        disable got_data interrupt
        value = data from hardware     # in case it takes awhile for get_fn to run...
        schedule get_fn.continue(value)
```

**Note**: Need to add code to check for a data overrun condition.

## Dispatch ##

The **dispatch** function keeps a queue of what functions are ready to run.  Each time it is called, it pops the next ready-to-run function (FAR/PC and value) from the queue, pushes the value, and jumps to the FAR/PC.  The **dispatch** function is unusual in that it does not save the caller's FAR/PC.

If the queue is empty, the **dispatch** function puts the processor to sleep.  The processor will be re-awakened when the next interrupt comes in.  The ISR for the interrupt returns to the **dispatch** function, which then checks the ready queue again.

### Schedule ###

The syntax for calling the **schedule** function looks like **schedule** _far.pc(value)_.  Thus, the **schedule** function has 3 parameters: a FAR, a PC, and an optional value.  This is what it does:

  1. Pushes the FAR, PC and value on the dispatch ready queue.
  1. Returns to its caller immediately without running the FAR/PC.