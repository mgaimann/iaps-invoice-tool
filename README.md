# IAPS invoice tool
[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/mu-gaimann/iaps-invoice-tool/)

Generate nice PDF invoices for IAPS, with LaTeX and Python

Based on previous work by @loelkes

## Motivation
The [International Association of Physics Students (IAPS)](https://www.iaps.info/) is an organization for the global physics students community with over 90,000 members. 
It is organized in individual, local and national memberships and run by volunteers like me.
IAPS collects membership fees which are computed according to a membership formula, specified in its Charter and Regulations.

Previously, these invoices were tediously written by hand, using Word documents, and sent out manually by email.

The tool seeks to 
- automate the invoice creation process 
- create beautiful invoices typeset in LaTeX
- create legally correct invoices for the jurisdiction of IAPS (Alsace-Moselle, France)
- automate the invoice email sending process


## What does it do?
This generator creates PDF-Documents with LaTeX.

1) It reads information from the IAPS membership fee spreadsheet and enriches it with additional information (invoice number etc.)
2) It automatically creates a LaTeX invoice document.
3) It processes the TeX code to PDF files using pdfTeX.
4) It reads email information from the IAPS membership fee spreadsheet and automatically sends out the invoices.

The created invoices comply in many points (but not all) with DIN 5008.

## Installation
- Install [Mamba](https://github.com/mamba-org/mamba) (or any other conda-oid package manager) by following these [Instructions](https://github.com/conda-forge/miniforge#install), or by executing:
- `wget "https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh"
bash Mambaforge-$(uname)-$(uname -m).sh`
- Create a mamba environment with `mamba env create -f environment.yaml`
- Activate the environment with `mamba activate iaps-invoice-tool`
