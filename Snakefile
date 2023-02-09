
rule create_invoice:
    input:
        "membership-fees.csv"
    output:
        "invoice/{id}-invoice.pdf"