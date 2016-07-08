# InvoiceGenerator
Generate nice PDF invoice with LaTeX and python

# Motivations
I needed a clean and fast way to generate invoices for my small business. I started with Word and LibreOffice but was not happy with it because it took too much time and can't be connected to an API or used for mass/automated invoice generation.

# What does it do?
This generator creates PDF-Documents with LaTeX. You can use it for any business but it is optimized for 3D-printing invoices: you can set a price per volume or weight an prices will be calculated based on the the data you enter.

The created invoices comply in many points (but not all) with DIN 5008. They have the folding marks, the address at the right place so you can use envelopes with a windows, contact information in the footer...

# What should it do in the future?
I'm currently connecting it to the WooCommerce Wordpress API. You just need to enter an order ID and after a few seconds you'll have an perfect PDF invoice.
