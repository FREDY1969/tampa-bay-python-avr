# gen\_assembler #

This is the call graph for [gen\_assembler](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/codegen.py#11).

This function translates the IntermediateCode into assembler.

  * [update\_use\_counts](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/codegen.py#51)
  * [order\_triples.order\_children](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#132)
    * [update\_order\_constraints](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#10)
      * [propogate\_links](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#16)
      * [delete\_extranious\_links](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#52)
      * [add\_transitive\_links](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#113)
    * [calc\_reg\_est\_for\_triples](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#168)
    * [calc\_reg\_est\_for\_blocks](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#211)
    * [calc\_reg\_est\_for\_functions](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#238)
    * [update\_triple\_parameter\_orders](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#269)
    * [update\_top\_level\_triple\_orders](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#351)
    * [calc\_master\_order](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#425)
      * [calc\_tree\_sizes](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#433)
      * [calc\_abs\_offsets](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#458)
      * [mark\_ghost\_links](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#502)
      * [calc\_abs\_order\_in\_block](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#518)
      * [calc\_parent\_seq\_num](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/order_triples.py#540)
  * [reg\_alloc.alloc\_regs](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/reg_alloc.py#10)