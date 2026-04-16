Installation
============

Install from PyPI:

.. code-block:: bash

   pip install mchplnet

Or install from source:

.. code-block:: bash

   git clone https://github.com/X2Cscope/mchplnet.git
   cd mchplnet
   pip install -e .

Requirements
------------

* Python 3.10 to 3.14
* pyserial (for UART communication)
* python-can (for CAN communication)

Development
-----------

To contribute to mchplnet development:

.. code-block:: bash

   # Install development dependencies
   pip install -e ".[dev,docs,build]"

   # Run tests
   pytest tests/

   # Run linting
   ruff check .

   # Build documentation
   sphinx-build -M html doc build -Wan --keep-going

   # Install pre-commit hooks
   pre-commit install

Release Publishing
------------------

Package releases are handled by GitHub Actions as part of the maintainer release workflow.
