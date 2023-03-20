import pandas as pd
import numpy as np

from generate import Member, makeinvoice

# read csv and determine identifiers
df = pd.read_csv("data/membership-form.csv", skiprows=0, header='infer', delimiter=',')

gni_df = pd.read_csv("data/gni_data.csv", skiprows=3, header='infer', delimiter=',')
wesp_df = pd.read_csv("data/wesp_data.csv", skiprows=3, header='infer', delimiter=',')


# collect gni data
df['country'] = None
df['country_code'] = None
df['gni_atlas_method'] = None
df['development_factor'] = None
df['discount_econ_downturn'] = None
df['discount_first_year'] = None
df['discount_lc'] = None
df['discount_probationary'] = None
df['fee'] = None
df['fee_excl_discount'] = None

for index, row in df.iterrows():
    df.at[index, 'country'] = row.iloc[7].strip()
    country_code = gni_df[gni_df['Country Name'] == df.at[index, 'country']]['Country Code']
    try:
        df.at[index, 'country_code'] = country_code.values[0]
    except IndexError:
        df.at[index, 'country_code'] = None


for index, row in df.iterrows():
    client = Member(
        society=row.iloc[5],
        careof=row.iloc[22],
        firstname=row.iloc[32],
        lastname=row.iloc[33],
        street=row.iloc[23],
        additional=row.iloc[24],
        postcode=row.iloc[25],
        city=row.iloc[26],
        district=row.iloc[27],
        country=row['country'],
        phone=None,
        email=None,
        country_code=row['country_code'],
        membership_type=row.iloc[3],
        fee=df['fee'],
        fee_excl_discount=df['fee_excl_discount'],
        discount_lc=row['discount_lc'],
        discount_first_year=row['discount_first_year'],
        discount_probationary=row['discount_probationary'],
        discount_econ_downturn=row['discount_econ_downturn'],
        development_factor=row['development_factor'],
        gni_atlas_method=df['gni_atlas_method'],
    )
    makeinvoice(client=client)

print("Exit Code 0")
