# !/usr/bin/python
# -*- coding: utf-8 -*-
import zlib

from pylatex import Document, Command, UnsafeCommand, LineBreak, NewLine, NewPage  # Latex stuff
from pylatex.utils import NoEscape  # More Latex Stuff
import time
import settings

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
    def __init__(self, company=None, name=None, street=None, postcode=None, city=None, country=None, additional=None,
                 phone=None, email=None, fee=None, country_code=None, membership_type=None
                 , firstname=None, lastname=None):
        self.company = company
        self.name = name
        self.street = street
        self.additional = additional
        self.postcode = postcode
        self.city = city
        self.country = country
        self.country_code = country_code
        self.phone = phone
        self.email = email
        self.fee = fee
        self.membership_type = membership_type
        self.firstname = firstname
        self.lastname = lastname

    def getaddress(self):
        if self.membership_type != "IM":
            output = self.company + '\n' + self.name + '\n' + self.street + '\n' + self.postcode + ' ' + self.city
        elif self.membership_type == "IM":
            output = f"{self.firstname} {self.lastname}" + '\n' + self.street + '\n' + self.postcode + ' ' + self.city
        else:
            raise ValueError("Membership type not set")
        return output


class Item:
    def __init__(self, financial_year=None, price=None):
        self.qt = 1
        self.desc = f'IAPS Membership Fee {financial_year}'
        self.price = price


class Invoice:
    def __init__(self, id=None, financial_year=None, client=None, seller=None, items=None):
        self.id = id
        self.subject = f"Your IAPS Membership Fee {financial_year}/{str(int(financial_year)+1)} --- Invoice"
        self.client = client  # Kundendaten
        self.me = seller  # Verkäufer
        self.discount = 0  # Rabatt
        self.items = items if items is not None else []
        self.filename = self.id
        self.documentclass = None
        self.docoptions = 'DIN,pagenumber=true,parskip=half,fromalign=right,fromphone=false,fromurl=true,fromfax=false,fromrule=false,fromlogo=True,fontsize=12pt'
        self.doc = None
        self.category = ['Invoice', 'Invoice Number']
        self.statictext = {
            'tdef': '\\begin{spreadtab}{{tabularx}{\linewidth}{lXrr}}',
            'thead': '@ Units & @ Item & @ Price per Unit  & @ Total \\\\ \\hline',
            'temptyrow': '@ & @ & @ & @ \\\\',
            'tsep': '\\\\ \\hline \\hline \\\\',
            'tsum': ' & & @ Sub-total & :={sum(d2:[0,-3])} \\euro \\\\',
            'tvat': ' & & @ VAT 0\% & :={[0,-1]*0.19+0.00} \\euro \\\\',
            'ttotal': ' & & @ Total & :={sum([0,-2]:[0,-1])} \\euro \\\\'
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
        # Falls man Kundennummer implementieren möchte.
        # %\setkomavar{yourref}[Ihre Kundennummer]{263}

    def generate(self):
        self.setuplatex()  # Latex konfigurieren.
        self.discount = 5
        self.discount = 0 if self.discount == '' else int(self.discount)
        multi = round(1 - self.discount / 100, 2)
        self.statictext['tdiscount'] = NoEscape(
            ' & & @ Discount ' + str(self.discount) + '\% & :={[0,-1]*' + str(multi) + '+0.00} \\euro \\\\')
        self.fill_document()  # Latex füllen.
        self.doc.generate_pdf(settings.latex['output_folder'] + self.filename, compiler=pdflatex, silent=latex_silent)
        if latex_output:
            self.doc.generate_tex(settings.latex['output_folder'] + self.filename)

    def additems(self):
        for item in self.items:
            tail = '\\euro 	& :={[-3,0]*[-1,0]} \\euro \\\\'
            self.doc.append(
                NoEscape(str(item.qt) + ' & @ ' + item.desc + ' & :={' + str(item.price) + '} ' + tail))

    def fill_document(self):
        self.doc.append(Command('begin', arguments='letter', extra_arguments=self.client.getaddress()))
        self.doc.append(Command('opening', ' '))
        self.doc.append(UnsafeCommand('vspace', '-1.0cm'))
        self.doc.append(Command('STautoround*', '2'))  # Round 2 decimals
        self.doc.append(Command('STsetdecimalsep', ','))  # Decimal separator sign
        self.doc.append(NoEscape(self.statictext['tdef']))  # Table definition
        self.doc.append(NoEscape(self.statictext['thead']))  # Table head
        self.doc.append(NoEscape(self.statictext['temptyrow']))  # Empty row
        self.additems()  # All the items
        self.doc.append(NoEscape(self.statictext['tsep']))  # Seperator row
        self.doc.append(NoEscape(self.statictext['tsum']))  # Sum of all items
        if self.discount != 0:
            self.doc.append(NoEscape(self.statictext['tdiscount']))
        # self.doc.append(NoEscape(self.statictext['tvat']))  # VAT
        self.doc.append(NoEscape(self.statictext['ttotal']))  # Total = VAT + sum
        self.doc.append(Command('end', 'spreadtab'))  # End of table
        self.doc.append(
            'Please settle the invoice within 14 days after receipt. '
            'Please use a wire transfer to pay the invoice in a single transaction, otherwise Paypal '
            '(IAPS Regulations Article 3.4.5). ')
        self.doc.append(NewPage())
        self.doc.append(
            'Remarks: If you wish to apply for a reduction of your membership fee '
            'in the event of national severe economic downturn due to a global catastrophe '
            '(IAPS Regulations Article 3.4.4.d), this must be done within 14 days of receipt of this invoice '
            '(IAPS EC Resolution EC/2022-23/XX). '
            'Failure to pay the invoice by June 1 will result in the irrevocable loss of voting rights '
            'at the Annual General Meeting for the current financial year (IAPS Charter Article 8.3) and may '
            'lead to membership termination through expulsion (IAPS Charter Article 9.1.4).')

        self.doc.append(NewLine())
        self.doc.append(NewLine())
        self.doc.append('Your membership fee explained (IAPS Regulations Article 8.4):')

        self.doc.append(Command('end', 'letter'))  # End of document


me = Member(settings.me['company'], settings.me['name'], settings.me['street'], settings.me['postcode'],
            settings.me['city'])


def get_invoice_id(financial_year, client):
    membership_type = client.membership_type
    if membership_type == 'NC':  # National Committee
        descriptor = 'XXX'
    elif membership_type == 'LC':  # Local Committee
        descriptor = client.city[:3].upper()
    elif membership_type == 'IM':  # Individual Member
        descriptor = client.lastname.upper() + client.firstname.upper()
    else:
        raise ValueError('Unknown membership type')
    return f'INV-{financial_year}-{membership_type}-{client.country_code}-{descriptor}'


def makeinvoice(client):
    financial_year = '2022'
    item = Item(financial_year, client.fee)
    this_id = get_invoice_id(financial_year, client)
    invoice = Invoice(client=client, items=[item], id=this_id, financial_year=financial_year)  # Rechnungsdokument erstellen
    invoice.generate()


test_client_nc = {"company": "NC Antarctica", "name": "P. Enguin", "street": "South Pole 1", "postcode": "96420",
               "city": "Ice City", "country": "Antarctica", "additional": "Cold District", "phone": "+99 17287 7832",
               "email": "nc-antarctica@iaps.info", "fee": 123.45,
               "country_code": "ATA", "membership_type": "NC"}

test_client_lc = {"company": "NC Antarctica", "name": "P. Enguin", "street": "South Pole 1", "postcode": "96420",
               "city": "Ice City", "country": "Antarctica", "additional": "Cold District", "phone": "+99 17287 7832",
               "email": "nc-antarctica@iaps.info", "fee": 123.45,
               "country_code": "ATA", "membership_type": "LC"}

test_client_im = {"firstname": "Paul", "lastname": "Enguin", "street": "South Pole 1", "postcode": "96420",
               "city": "Ice City", "country": "Antarctica", "additional": "Cold District", "phone": "+99 17287 7832",
               "email": "nc-antarctica@iaps.info", "fee": 123.45,
               "country_code": "ATA", "membership_type": "IM"}


def main():
    client = Member(**test_client_im)
    makeinvoice(client=client)


if __name__ == '__main__':
    main()
