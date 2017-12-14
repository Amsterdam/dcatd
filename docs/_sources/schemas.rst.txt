.. _schemas:

JSON Schemas and OpenAPI definitions
====================================

JSON Schema Validation v04 has the following built-in formats for strings:


- ``"date-time"``: Date representation, as defined by :rfc:`3339`, section 5.6.

- ``"email"``: Internet email address, see :rfc:`5322`, section 3.4.1.

- ``"hostname"``: Internet host name, see :rfc:`1034`, section 3.1.

- ``"ipv4"``: IPv4 address, according to dotted-quad ABNF syntax as
  defined in :rfc:`2673`, section 3.2.

- ``"ipv6"``: IPv6 address, as defined in :rfc:`2373`, section 2.2.

- ``"uri"``: A universal resource identifier (URI), according to :rfc:`3986`.


Additionally, we use the following format identifiers:

- ``"line"``: A single line of text, ie. not including any new-line characters.

- ``"rst"``: reStructuredText
