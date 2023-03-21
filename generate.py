# !/usr/bin/python
# -*- coding: utf-8 -*-
import copy

from pylatex import Document, Command, UnsafeCommand, LineBreak, NewLine, NewPage, Math  # Latex stuff
from pylatex.utils import NoEscape  # More Latex Stuff
import time
import settings
import numpy as np
import random

latex_preamble = 'preamble.tex'
pdflatex = '/usr/bin/pdflatex'
latex_silent = True  # Set false for debugging
latex_output = True  # Set True to get .tex files.


# This can be usefull for editing invoices if there was an error without having to generate a new latex file.

# Todo: Get the client informations from Wordpress API
# Todo: Get the order form Wordpress API
# Todo: Non-WP-Mode: better menue, able to jump between things, corrects etc.
# Todo: Multipage invoices
# Todo: Multilingual
# Todo: store Order config in JSON First line of Latex (in comment) to reload the file an edit it.
# Todo: Taxation in config file (?)
# Todo: Find solution fro preamble.tex so i can be generated from config.py?
# Todo: Add notifications / text to the end of the invoice, like payment deadline or additional information
# Todo: Add a folder and scan all the STL-Files into the invoice
# Todo: Filename in the description if automated price calc.


def _(s):
    return s


class Member:
    def __init__(self, society=None, careof=None, street=None, postcode=None, city=None, district=None, country=None, additional=None,
                 phone=None, email=None, fee=None, country_code=None, membership_type=None
                 , firstname=None, lastname=None,
                 fee_excl_discount=None, discount=None, discount_total=None, discount_lc=1.0, discount_first_year=1.0,
                 discount_probationary=1.0, discount_econ_downturn=1.0, development_factor=1.0,
                 gni_atlas_method=None):
        self.society = society
        self.careof = careof
        self.street = street
        self.additional = additional
        self.postcode = postcode
        self.city = city
        self.district = district
        self.country = country
        self.country_code = country_code
        self.phone = phone
        self.email = email
        self.fee = fee
        self.fee_excl_discount = fee_excl_discount
        self.discount = discount
        self.membership_type = membership_type
        self.firstname = firstname
        self.lastname = lastname
        self.discount_lc = discount_lc
        self.discount_first_year = discount_first_year
        self.discount_probationary = discount_probationary
        self.discount_econ_downturn = discount_econ_downturn
        self.discount_total = discount_total
        self.development_factor = development_factor
        self.gni_atlas_method = gni_atlas_method

    def getaddress(self):
        output = ''
        if self.membership_type != "Individual Member (IM)":
            if self.careof is not np.nan:
                output += str(self.careof) + '\n'
            else:
                output += str(self.society) + '\n'
        elif self.membership_type == "Individual Member (IM)":
            output += f"{self.lastname}, {self.firstname}" + '\n'
        else:
            raise ValueError("Membership type not set")
        output += str(self.street) + '\n'
        if self.additional is not np.nan:
            output += str(self.additional) + '\n'
        if self.postcode is not np.nan:
            output += str(self.postcode) + '  '
        output += str(self.city) + '\n'
        if self.district is not np.nan:
            output += str(self.district) + '\n'
        output += str(self.country)
        return output


class Item:
    def __init__(self, financial_year=None, price=None, member_name=None):
        self.qt = 1.00
        self.desc = f'IAPS Membership Fee {financial_year}/{financial_year + 1} for the {member_name} *'
        self.price = price


class Invoice:
    def __init__(self, id=None, financial_year=None, client=None, seller=None, items=None):
        self.id = id
        self.subject = f"Your IAPS Membership Fee {financial_year}/{str(int(financial_year) + 1)} --- Invoice"
        self.client = client
        self.me = seller
        self.discount = client.discount
        self.items = items if items is not None else []
        self.filename = self.id
        self.documentclass = None
        self.docoptions = 'DIN,pagenumber=true,parskip=half,fromalign=right,fromphone=false,' \
                          'fromurl=true,fromfax=false,fromrule=false,fromlogo=True,fontsize=12pt'
        self.doc = None
        self.category = ['Invoice', 'Invoice Number']
        self.statictext = {
            'tdef': '\\begin{spreadtab}{{tabularx}{\linewidth}{lXrr}}',
            'thead': '@ Units & @ Item & @ Price per Unit  & @ Total \\\\ \\hline',
            'temptyrow': '@ & @ & @ & @ \\\\',
            'tsep': '\\\\ \\hline \\hline \\\\',
            'tsum': f' & & @ Sub-total & @ {self.client.fee_excl_discount:.2f} EUR \\\\',
            'tvat': ' & & @ VAT 0\% & @ 0.00 EUR  \\\\',
            'ttotal': ' & & @ \\textbf{Total} & @ \\textbf{'
                      f'{self.client.fee:.2f}'
                      ' EUR} \\\\'
        }

    def setuplatex(self):
        self.filename = self.id
        self.documentclass = Command('documentclass', arguments='scrlttr2', options=self.docoptions)
        self.doc = Document(self.filename, documentclass=self.documentclass, fontenc='T1', inputenc='utf8')
        self.doc.preamble.append(Command('input', latex_preamble))
        self.doc.preamble.append(Command('LoadLetterOption', 'template'))
        self.doc.preamble.append(Command('setkomavar', arguments='subject', extra_arguments=self.subject))
        self.doc.preamble.append(
            Command('setkomavar', arguments='yourmail', options=self.category[1], extra_arguments=self.filename))
        # %\setkomavar{yourref}[Ihre Kundennummer]{263}

    def generate(self):
        self.setuplatex()
        self.discount = self.client.fee_excl_discount - self.client.fee
        self.discount = 0 if self.discount == '' else int(self.discount)
        discount_percentage = round(100 - self.client.discount_total * 100, 4)
        self.statictext['tdiscount'] = NoEscape(
            ' & & @ \\textdaggerdbl~Discount ' + f'{discount_percentage:.2f}\,\% & '
                                 f' @{self.discount:.2f} EUR \\\\')
        self.fill_document()
        self.doc.generate_pdf(settings.latex['output_folder'] + self.filename, compiler=pdflatex, silent=latex_silent)
        if latex_output:
            self.doc.generate_tex(settings.latex['output_folder'] + self.filename)

    def additems(self):
        for item in self.items:
            self.doc.append(
                NoEscape(f'{item.qt:.2f} & @ {item.desc} & @ {item.price:.2f} & @ {item.price:.2f} EUR'))

    def fill_document(self):
        self.doc.append(Command('begin', arguments='letter', extra_arguments=self.client.getaddress()))
        self.doc.append(Command('opening', ' '))
        self.doc.append(UnsafeCommand('vspace', '-.5cm'))
        self.doc.append(Command('STautoround*', '2'))  # Round 2 decimals
        self.doc.append(Command('STsetdecimalsep', '.'))  # Decimal separator sign
        self.doc.append(NoEscape(self.statictext['tdef']))  # Table definition
        self.doc.append(NoEscape(self.statictext['thead']))  # Table head
        self.doc.append(NoEscape(self.statictext['temptyrow']))  # Empty row
        self.additems()  # All the items
        self.doc.append(NoEscape(self.statictext['tsep']))  # Seperator row
        self.doc.append(NoEscape(self.statictext['tsum']))  # Sum of all items
        self.doc.append(NoEscape(self.statictext['tdiscount']))
        # self.doc.append(NoEscape(self.statictext['tvat']))  # VAT
        self.doc.append(NoEscape(self.statictext['ttotal']))  # Total = VAT + sum
        self.doc.append(Command('end', 'spreadtab'))  # End of table
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NewPage())
        self.doc.append(Command('begin', 'small'))
        self.doc.append(NoEscape(
            'Please settle the invoice within 14 days after receipt, \\textbf{using the invoice number as reference}. '
            'Please use a wire transfer to pay the invoice in a single transaction, otherwise Paypal '
            '(IAPS Regulations Article 3.4.5). VAT is not applicable (for membership fees and per Article~293 b of '
            'the French general tax code (\\textit{TVA non applicable, art.~293 B du CGI})).'))
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(
            'Remarks: If you wish to apply for a reduction of your membership fee '
            'in the event of national severe economic downturn due to a global catastrophe '
            '(IAPS Regulations Article 3.4.4.d), this must be done within 14 days of receipt of this invoice '
            '(IAPS EC Resolution EC/2022-23/122). '
            'Failure to pay the invoice by June 1 may result in the loss of voting rights '
            'at the Annual General Meeting for the current financial year (IAPS Charter Article 8.3) and may '
            'lead to membership termination through expulsion (IAPS Charter Article 9.1.4). '
            'This document is electronically printed and valid without stamp and signature.')

        self.doc.append(NewLine())
        self.doc.append(Command('end', 'small'))
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append('* Your membership fee explained (IAPS Regulations Article 3.4.1):')
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(Command('begin', 'footnotesize'))
        self.doc.append(NoEscape('\\begin{tabular}{lll}'))
        self.doc.append(NoEscape('Membership Type & IAPS Reg.~Art. & Calculation Method \\\\'))
        self.doc.append(NoEscape('\\hline'))
        self.doc.append(NoEscape('&& \\\\'))
        self.doc.append(NoEscape('LC/NC & 3.4.3.ab & Formula, in EUR \\\\'))
        self.doc.append(NoEscape(' & & $\\min (d \\cdot (75 + 2 \\cdot \\sqrt[3]{G}, 400))$ \\\\'))
        self.doc.append(NoEscape('IM & 3.4.3.c & Fixed Amount, EUR 10.00 \\\\'))
        self.doc.append(NoEscape('&& \\\\'))
        self.doc.append(NoEscape('&& \\\\'))
        # min(d · (75 + 2 ∗ 3
        # p(G), 400))

        self.doc.append(NoEscape('Variable & IAPS Reg.~Art. & Value \\\\'))
        self.doc.append(NoEscape('\\hline'))
        self.doc.append(NoEscape('&& \\\\'))
        self.doc.append(NoEscape(f'Membership Type&3.4.3 & {self.client.membership_type} \\\\'))
        self.doc.append(NoEscape(
            f'GNI Atl.~Mtd.\\textsuperscript{1}, $10^6$ USD (G)&3.4.2.c & {self.client.gni_atlas_method} \\\\'))
        self.doc.append(
            NoEscape(f'Development Factor\\textsuperscript{2} (d)&3.4.4.d & {self.client.development_factor} \\\\'))
        self.doc.append(NoEscape('&& \\\\'))
        self.doc.append(NoEscape('&& \\\\'))

        self.doc.append(NoEscape('Discount &IAPS Reg.~Art. & Factor \\\\'))
        self.doc.append(NoEscape('\\hline'))
        self.doc.append(NoEscape('&& \\\\'))
        self.doc.append(NoEscape(f'LC &3.4.3.b& {self.client.discount_lc} \\\\'))
        self.doc.append(NoEscape(f'First Year &3.4.4.b& {self.client.discount_first_year} \\\\'))
        self.doc.append(NoEscape(f'Probationary &3.4.4.a& {self.client.discount_probationary} \\\\'))
        self.doc.append(NoEscape(f'Economic Downturn &3.4.4.d& {self.client.discount_econ_downturn} \\\\'))
        self.doc.append(NoEscape(f'\\textdaggerdbl~Total (multiplicative)  & 3.4 & {self.client.discount_total} \\\\'))
        self.doc.append(NoEscape('\\end{tabular} \\\\'))
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(Command('end', 'footnotesize'))
        # self.doc.append("For the IAPS Executive Committee sincerely,")
        # self.doc.append(NewLine())
        # self.doc.append(NewLine())
        # self.doc.append(NewLine())
        # self.doc.append(NoEscape('\\begin{tabular}{c@{\hskip 3cm}c}'))
        # self.doc.append(NoEscape("Mario Gaimann & Max Peters \\\\"))
        # self.doc.append(NoEscape("IAPS Treasurer 2022/23 & Membership Fees Officer 2022/23 \\\\"))
        # self.doc.append(NoEscape('\\end{tabular}'))
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(Command('scriptsize'))
        self.sources = {'gni': 'https://api.worldbank.org/v2/en/indicator/NY.GNP.ATLS.CD?downloadformat=csv',
                        'wesp_annex': 'https://www.un.org/development/desa/dpad/wp-content/uploads/sites/45/WESP2022\\_ANNEX.pdf'}

        self.doc.append(
            NoEscape('\\textsuperscript{1} Gross National Income of your country(s), Atlas Method (current USD). Source: \\href{'
                     f'{self.sources["gni"]}'
                     '}{The World Bank, \\\\'
                     f'{self.sources["gni"]}'
                     '}'))
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NoEscape('\\textsuperscript{2} Source: \\href{'
                                 f'{self.sources["wesp_annex"]}'
                                 '}{United Nations,  Dept.~of Economic and Social Affairs, World Economic Situation and Prospects 2022,\\\\'
                                 f'{self.sources["wesp_annex"]}'
                                 '}'))
        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append(NoEscape(
            'Generated with the open-source IAPS Invoice Generator based on Python and \\LaTeX, available under \\\\'
            '\\href{https://github.com/mu-gaimann/iaps-invoice-tool}{https://github.com/mu-gaimann/iaps-invoice-tool}. '
            'Interested in contributing? Found a typo or a bug? Feedback or suggestions? Open an issue on GitHub or contact \\href{mailto:membership-fees@iaps.info}{membership-fees@iaps.info}.'))
        self.doc.append(Command('end', 'letter'))  # End of document


me = Member(settings.me['company'], settings.me['name'], settings.me['street'], settings.me['postcode'],
            settings.me['city'])


def get_invoice_id(financial_year, client):
    membership_type = client.membership_type
    if membership_type == 'National Committee (NC)':
        short_membership_type = 'NC'
        descriptor = '0000'
    elif membership_type == 'Local Committee (LC)':  # Local Committee
        short_membership_type = 'LC'
        descriptor = ''.join(filter(str.isalpha, client.city))  # allow only letters
        descriptor = descriptor[:4].upper()
    elif membership_type == 'Individual Member (IM)':  # Individual Member
        short_membership_type = 'IM'
        try:
            descriptor = client.lastname.upper()[:3] + client.firstname.upper()[:3]
        except AttributeError:
            descriptor = 'INVALID-DESCRIPTOR'
    else:
        raise ValueError('Unknown membership type')
    return f'INV-{financial_year}-{short_membership_type}-{client.country_code}-{descriptor}'


def makeinvoice(client):
    financial_year = 2022
    if client.membership_type != 'Individual Member (IM)':
        member_name = client.society
    else:
        member_name = f"IM {client.lastname}, {client.firstname}"
    item = Item(financial_year, client.fee_excl_discount, member_name=member_name)
    this_id = get_invoice_id(financial_year, client)
    invoice = Invoice(client=client, items=[item], id=this_id,
                      financial_year=financial_year)  # Rechnungsdokument erstellen
    invoice.generate()


test_client_nc = {"company": "NC Antarctica", "name": "P. Enguin", "street": "South Pole 1", "postcode": "96420",
                  "city": "St. Ice", "country": "Antarctica", "additional": "Cold District", "phone": "+99 17287 7832",
                  "email": "nc-antarctica@iaps.info", "fee": 93.50,
                  "country_code": "ATA", "membership_type": "NC", "fee_excl_discount": 187.00,
                  "discount_lc": 1.00,
                  "discount_first_year": 1.00, "discount_probationary": 0.50, "discount_econ_downturn": 1.00,
                  "development_factor": 0.50, "gni_atlas_method": 52341987.02}

test_client_lc = copy.deepcopy(test_client_nc)
test_client_lc["membership_type"] = "LC"
test_client_lc["discount_lc"] = 0.33

test_client_im = copy.deepcopy(test_client_nc)
test_client_im.update({"firstname": "Paul", "lastname": "Enguin", "membership_type": "IM", "fee": 10.0})


def main():
    client = Member(**test_client_im)
    makeinvoice(client=client)


if __name__ == '__main__':
    main()
