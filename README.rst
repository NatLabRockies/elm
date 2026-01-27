***************************
Energy Language Model (ELM)
***************************

.. image:: https://github.com/NatLabRockies/elm/workflows/Documentation/badge.svg
    :target: https://natlabrockies.github.io/elm/

.. image:: https://github.com/NatLabRockies/elm/workflows/pytests/badge.svg
    :target: https://github.com/NatLabRockies/elm/actions?query=workflow%3A%22pytests%22

.. image:: https://github.com/NatLabRockies/elm/workflows/Lint%20Code%20Base/badge.svg
    :target: https://github.com/NatLabRockies/elm/actions?query=workflow%3A%22Lint+Code+Base%22

.. image:: https://img.shields.io/pypi/pyversions/NLR-elm.svg
    :target: https://pypi.org/project/NLR-elm/

.. image:: https://badge.fury.io/py/NLR-elm.svg
    :target: https://badge.fury.io/py/NLR-elm

.. image:: https://zenodo.org/badge/690793778.svg
  :target: https://zenodo.org/doi/10.5281/zenodo.10070538

The Energy Language Model (ELM) software provides interfaces to apply Large Language Models (LLMs) like ChatGPT and GPT-4 to energy research. For example, you might be interested in:

- `Converting PDFs into a text database <https://natlabrockies.github.io/elm/_autosummary/elm.pdf.PDFtoTXT.html#elm.pdf.PDFtoTXT>`_
- `Chunking text documents and embedding into a vector database <https://nrenatlabrockiesl.github.io/elm/_autosummary/elm.embed.ChunkAndEmbed.html#elm.embed.ChunkAndEmbed>`_
- `Performing recursive document summarization <https://natlabrockies.github.io/elm/_autosummary/elm.summary.Summary.html#elm.summary.Summary>`_
- `Building an automated data extraction workflow using decision trees <https://natlabrockies.github.io/elm/_autosummary/elm.tree.DecisionTree.html#elm.tree.DecisionTree>`_
- `Building a chatbot app that interfaces with reports from OSTI <https://github.com/NatLabRockies/elm/tree/main/examples/energy_wizard>`_

Installing ELM
==============

.. inclusion-install

NOTE: If you are installing ELM to run ordinance scraping and extraction,
see the `ordinance-specific installation instructions <https://github.com/NatLabRockies/elm/blob/main/elm/ords/README.md>`_.

Option #1 (basic usage):

#. ``pip install NLR-elm``

Option #2 (developer install):

#. from home dir, ``git clone git@github.com:NatLabRockies/elm.git``
#. Create ``elm`` environment and install package
    a) Create a conda env: ``conda create -n elm``
    b) Run the command: ``conda activate elm``
    c) ``cd`` into the repo cloned in 1.
    d) Prior to running ``pip`` below, make sure the branch is correct (install
       from main!)
    e) Install ``elm`` and its dependencies by running:
       ``pip install .`` (or ``pip install -e .`` if running a dev branch
       or working on the source code)

.. inclusion-acknowledgements

Acknowledgments
===============

This work was authored by the National Laboratory of the Rockies, operated by Alliance for Energy Innovation, LLC, for the U.S. Department of Energy (DOE) under Contract No. DE-AC36-08GO28308. Funding provided by the DOE Wind Energy Technologies Office (WETO), the DOE Solar Energy Technologies Office (SETO), and internal research funds at the National Laboratory of the Rockies. The views expressed in the article do not necessarily represent the views of the DOE or the U.S. Government. The U.S. Government retains and the publisher, by accepting the article for publication, acknowledges that the U.S. Government retains a nonexclusive, paid-up, irrevocable, worldwide license to publish or reproduce the published form of this work, or allow others to do so, for U.S. Government purposes.
