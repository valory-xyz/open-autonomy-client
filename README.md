<h1 align="center">
    <b>Autonomous Service Client SDK </b>
</h1>

<p align="center">
  <a href="https://pypi.org/project/open-autonomy-client-client/">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/open-autonomy-client">
  </a>
  <a href="https://pypi.org/project/open-autonomy-client/">
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/open-autonomy-client">
  </a>
  <a>
    <img alt="PyPI - Wheel" src="https://img.shields.io/pypi/wheel/open-autonomy-client">
  </a>
  <a href="https://github.com/valory-xyz/open-autonomy-client/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/pypi/l/open-autonomy-client">
  </a>
  <a href="https://pypi.org/project/open-autonomy-client/">
    <img alt="Downloads" src="https://img.shields.io/pypi/dm/open-autonomy-client">
  </a>
</p>
<p align="center">
  <a href="https://github.com/valory-xyz/open-autonomy-client/actions/workflows/main_workflow.yml">
    <img alt="Sanity checks and tests" src="https://github.com/valory-xyz/open-autonomy-client/workflows/main_workflow/badge.svg?branch=main">
  </a>
  <a href="">
    <img alt="Codecov" src="https://img.shields.io/codecov/c/github/valory-xyz/open-autonomy-client">
  </a>
  <a href="https://img.shields.io/badge/lint-flake8-blueviolet">
    <img alt="flake8" src="https://img.shields.io/badge/lint-flake8-yellow" >
  </a>
  <a href="https://github.com/python/mypy">
    <img alt="mypy" src="https://img.shields.io/badge/static%20check-mypy-blue">
  </a>
  <a href="https://github.com/psf/black">
    <img alt="Black" src="https://img.shields.io/badge/code%20style-black-black">
  </a>
  <a href="https://github.com/PyCQA/bandit">
    <img alt="mypy" src="https://img.shields.io/badge/security-bandit-lightgrey">
  </a>
</p>

**Open Autonomy Client SDK** is a library that helps to query multi-agent systems built with the 
[open-autonomy](https://github.com/valory-xyz/open-autonomy) framework. It allows one to simply perform a request
to a service as if it were a single endpoint. The SDK in the background requests the information from multiple agents 
in order to return a result for which it is safe to assume that the agents have reached consensus on.

## For developers contributing to the SDK: install from source

- Ensure your machine satisfies the following requirements:

    - Python `>= 3.10`
    - [Pip](https://pip.pypa.io/en/stable/installation/)
    - [Poetry](https://python-poetry.org/docs/#installation) `>=1.4.0`
    - [Gitleaks](https://github.com/zricethezav/gitleaks/releases/latest)

- Clone the repository:

      git clone git@github.com:valory-xyz/open-autonomy-client.git

- Create and launch a virtual environment. Also, run this during development,
every time you need to update the dependencies:

      poetry install

## Cite

If you are using our software in a publication, please
consider to cite it with the following BibTex entry:

```
@misc{open-autonomy-client,
  Author = {David Minarsch and Yuri Turchenkov and Adamantios Zaras},
  Title = {Open Autonomy Client SDK},
  Year = {2023},
}
```
