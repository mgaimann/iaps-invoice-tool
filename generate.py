# !/usr/bin/python
# -*- coding: utf-8 -*-

from pylatex import Document, Command, UnsafeCommand        # Latex stuff
from pylatex.utils import NoEscape                          # More Latex Stuff
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


class Person:
    def __init__(self, company=None, name=None, street=None, postcode=None, city=None, country=None, additional=None, phone=None, email=None):
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

    def cli_input(self):
        print(_('Bitte Rechnungsadresse eingeben:'))
        self.name = input(_('Name:   '))
        self.company = input(_('Firma:  '))
        self.street = input(_('Straße: '))
        self.postcode = input(_('PLZ:    '))
        self.city = input(_('Stadt:  '))
        print(_('Kontrollansicht:'))
        print(self.getaddress())


class Invoice:
    def __init__(self, id=None, subject=None, client=None, seller=None, items=None, offer=False):
        self.id = str(id)
        self.subject = subject      # Rechnungsbeschriebung
        self.client = client        # Kundendaten
        self.me = seller            # Verkäufer
        self.discount = 0           # Rabatt
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
        self.doc.preamble.append(Command('setkomavar', arguments='yourmail', options=self.categroy[1], extra_arguments=self.filename))
        # Falls man Kundennummer implementieren möchte.
        # %\setkomavar{yourref}[Ihre Kundennummer]{263}

    def generate(self):
        self.cli_input_details()    # Details in Dokument eintragen
        self.setuplatex()           # Latex konfigurieren.
        self.cli_input_items()      # Items abfragen
        self.discount = input(_('Ermäßigung in %: [0%] '))
        self.discount = 0 if self.discount == '' else int(self.discount)
        multi = round(1-self.discount/100, 2)
        self.statictext['tdiscount'] = NoEscape(' & & @ Ermäßigung ' + str(self.discount) + '\% & :={[0,-1]*' + str(multi) + '+0.00} \\euro \\\\')
        self.fill_document()        # Latex füllen.
        self.doc.generate_pdf(settings.latex['output_folder'] + self.filename, compiler=pdflatex, silent=latex_silent)
        if latex_output:
            self.doc.generate_tex(self.filename)

    def cli_input_details(self):
        print(_('Bitte Rechnungsdetails angeben: '))
        self.id = input(self.categroy[1] + ': ')
        self.subject = input(_('Betreff: '))

    def cli_input_items(self):
        i = input(_('Anzahl an Positionen? '))
        for i in range(0, int(i)):
            separator()

    def additems(self):
        for item in self.items:
            tail = '\\euro 	& :={[-3,0]*[-1,0]} \\euro \\\\'
            self.doc.append(NoEscape(str(item.qt) + ' & @ ' + item.desc + item.desc2 + ' & :={' + str(item.price) + '} ' + tail))

    def fill_document(self):
        self.doc.append(Command('begin', arguments='letter', extra_arguments=self.client.getaddress()))
        self.doc.append(Command('opening', ' '))
        self.doc.append(UnsafeCommand('vspace', '-1.0cm'))
        self.doc.append(Command('STautoround*', '2'))               # Round 2 decimals
        self.doc.append(Command('STsetdecimalsep', ','))            # Decimal separator sign
        self.doc.append(NoEscape(self.statictext['tdef']))          # Table definition
        self.doc.append(NoEscape(self.statictext['thead']))         # Table head
        self.doc.append(NoEscape(self.statictext['temptyrow']))     # Empty row
        self.additems()                                             # All the items
        self.doc.append(NoEscape(self.statictext['tsep']))          # Seperator row
        self.doc.append(NoEscape(self.statictext['tsum']))          # Sum of all items
        if self.discount != 0:
            self.doc.append(NoEscape(self.statictext['tdiscount']))
        self.doc.append(NoEscape(self.statictext['tvat']))          # VAT
        self.doc.append(NoEscape(self.statictext['ttotal']))        # Total = VAT + sum
        self.doc.append(Command('end', 'spreadtab'))                # End of table
        self.doc.append(Command('end', 'letter'))                   # End of document


me = Person(settings.me['company'], settings.me['name'], settings.me['street'], settings.me['postcode'], settings.me['city'])

main_menu = [
    {'tag': False, 'label': _('Rechnung')},
    {'tag': True, 'label': _('Angebot')}
    ]

# -- Start of obelix-tools
# Because these are useful functions they might be out-sourced in a separate python file one day.


def separator():
    print("\n======\n")


def menu(options):
    action = None
    # separator()
    while 1:
        for i, choice in enumerate(options):
            print("%i. %s" % (i, choice['label']))
        u = input('? [0]: ')
        try:
            u = u if u != '' else 0
            action = options[int(u)]
            break
        except IndexError:
            print(_('Error.'))
    # separator()
    return action['tag']


# This is untested yet
def defaultinput(text, default):
    i = input(text + ' [' + str(default) + ']')
    i = i if i != '' else default
    return i

# -- End of obelix-tools


def makeoffer(client):
    invoice = Invoice(client=client, offer=True)    # Rechnungsdokument erstellen
    invoice.generate()


def makeinvoice(client, offer=False):
    invoice = Invoice(client=client, offer=offer)    # Rechnungsdokument erstellen
    invoice.generate()


def main():

    # Hinweis: Reihenfolge ist nicht zufällig.

    print(_('Rechnungsgenerator'))
    separator()
    client = Person()
    client.cli_input()                  # Rechnungsadresse abfragen.
    offer = menu(main_menu)
    makeinvoice(client=client, offer=offer)

    # invoice.doc.dumps()  # The document as string in LaTeX syntax4

if __name__ == '__main__':
    main()
