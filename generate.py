# !/usr/bin/python
# -*- coding: utf-8 -*-

from pylatex import Document, Command, UnsafeCommand  # Latex stuff
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
                 phone=None, email=None):
        self.company = company
        self.name = name
        self.street = street
        self.additional = additional
        self.postcode = postcode
        self.city = city
        self.country = country
        self.phone = phone
        self.email = email

    def getaddress(self):
        output = self.company + '\n' + self.name + '\n' + self.street + '\n' + self.postcode + ' ' + self.city
        return output


class Invoice:
    def __init__(self, id=None, subject=None, client=None, seller=None, items=None, offer=False):
        self.id = str(0)
        self.subject = "Your IAPS Membership Fee 2022/23 - Invoice"
        self.client = client  # Kundendaten
        self.me = seller  # Verkäufer
        self.discount = 0  # Rabatt
        self.items = items if items is not None else []
        self.filename = self.id + '-' + time.strftime('%Y')
        self.documentclass = None
        self.docoptions = 'DIN,pagenumber=false,parskip=half,fromalign=right,fromphone=true,fromfax=false,fromrule=false,fontsize=12pt'
        self.doc = None
        if offer is True:
            self.setoffer()
        else:
            self.categroy = ['Rechnung', 'Rechnungsnummer']
        self.statictext = {
            'tdef': '\\begin{spreadtab}{{tabularx}{\linewidth}{lXrr}}',
            'thead': '@ Anzahl & @ Beschreibung & @ Einzelpreis & @ Gesamtpreis \\\\ \\hline',
            'temptyrow': '@ & @ & @ & @ \\\\',
            'tsep': '\\\\ \\hline \\hline \\\\',
            'tsum': ' & & @ Nettobetrag Gesamt & :={sum(d2:[0,-3])} \\euro \\\\',
            'tvat': ' & & @ MwSt. 19\% & :={[0,-1]*0.19+0.00} \\euro \\\\',
            'ttotal': ' & & @ Bruttobetrag Gesamt & :={sum([0,-2]:[0,-1])} \\euro \\\\'
        }

    def setoffer(self):
        self.categroy = ['Angebot', 'Angebotsnummer']

    def setuplatex(self):
        self.filename = self.id + '-' + time.strftime('%Y')
        self.documentclass = Command('documentclass', arguments='scrlttr2', options=self.docoptions)
        self.doc = Document(self.filename, documentclass=self.documentclass, fontenc='T1', inputenc='utf8')
        self.doc.preamble.append(Command('input', latex_preamble))
        self.doc.preamble.append(Command('LoadLetterOption', 'template'))
        self.doc.preamble.append(Command('setkomavar', arguments='subject', extra_arguments=self.subject))
        self.doc.preamble.append(
            Command('setkomavar', arguments='yourmail', options=self.categroy[1], extra_arguments=self.filename))
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
            self.doc.generate_tex(self.filename)

    def additems(self):
        for item in self.items:
            tail = '\\euro 	& :={[-3,0]*[-1,0]} \\euro \\\\'
            self.doc.append(
                NoEscape(str(item.qt) + ' & @ ' + item.desc + item.desc2 + ' & :={' + str(item.price) + '} ' + tail))

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
        self.doc.append(NoEscape(self.statictext['tvat']))  # VAT
        self.doc.append(NoEscape(self.statictext['ttotal']))  # Total = VAT + sum
        self.doc.append(Command('end', 'spreadtab'))  # End of table
        self.doc.append(
            '\\  Remarks: Please settle the invoice within 14 days after receipt. '
            'Please use a wire transfer to pay the invoice in a single transaction, otherwise Paypal '
            '(IAPS Regulations Article 3.4.5). If you wish to apply for a reduction of your membership fee '
            'in the event of national severe economic downturn due to a global catastrophe '
            '(IAPS Regulations Article 3.4.4.d), this must be done within 14 days of receipt of this invoice '
            '(Resolution EC/2022-23/XX). '
            'Failure to pay the invoice by June 1 will result in the irrevocable loss of voting rights '
            'at the Annual General Meeting in the current financial year (IAPS Charter Article 8.3) and may '
            'lead to membership termination through expulsion (IAPS Charter Article 9.1.4).')
        self.doc.append(Command('end', 'letter'))  # End of document


me = Member(settings.me['company'], settings.me['name'], settings.me['street'], settings.me['postcode'],
            settings.me['city'])

main_menu = [
    {'tag': False, 'label': _('Rechnung')},
    {'tag': True, 'label': _('Angebot')}
]


def makeinvoice(client, offer=False):
    invoice = Invoice(client=client, offer=offer)  # Rechnungsdokument erstellen
    invoice.generate()


test_client = {"company": "NC Antarctica", "name": "P. Enguin", "street": "South Pole 1", "postcode": "96420",
               "city": "Ice City", "country": "Antarctica", "additional": "Cold District", "phone": "+99 17287 7832",
               "email": "nc-antarctica@iaps.info"}


def main():
    client = Member(**test_client)
    makeinvoice(client=client)


if __name__ == '__main__':
    main()
