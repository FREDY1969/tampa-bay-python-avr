  1. Each [Package](Package.md) has one **database** called _package.db_ located in the package directory.
    * This allows us to reference the database from multiple programs using the same [Package](Package.md).
    * But the table keys must be done in a way to make it easy to load multiple databases from several Packages without producing conflicting keys.
  1. The database is not used to store user (programmer) entered data.
    * These data will be stored directly into merge-able text files (source files and XML files).
    * This is the only data that is downloaded to use somebody else's library.
  1. The database will be used to store the SymbolTable and IntermediateCode generated by the [Parser](ParsingAndCompiling#Parsing.md).
    * This data is local to each user's workstation and not shared.
    * This database can be created from scratch based solely on the information in step 2.
    * This data is also used by the GUI/IDE to provide cross-reference information about the code.
  1. A database may or may not be used (don't know yet) for some or all of the data generated by the back-end [Compiling](ParsingAndCompiling#Compiling.md) phase.
    * At this time, I expect this data to be short lived.  If the database is useful, we can use it, but I don't think the GUI needs to look at this stuff except for function run times and memory sizes.