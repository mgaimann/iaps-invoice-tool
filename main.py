import pandas as pd
import numpy as np

invoice_id = "NC-Germany"

# read csv and determine identifiers
df = pd.read_csv("data/membership-fees.csv", skiprows=3, header='infer', delimiter=',')
membership_type, country_or_city = invoice_id.split("-")


# find pandas row
if membership_type == "NC":
    cond = np.logical_and(df["NC/LC"] == "NC", df["Country"] == country_or_city)
elif membership_type == "LC":
    cond = np.logical_and(df["NC/LC"] == "LC", df["City"] == country_or_city)
else:
    raise ValueError("Invalid membership type.")


a = df[cond]

print("Exit Code 0")
