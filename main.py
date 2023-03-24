import pandas as pd
import numpy as np

from generate import Member, makeinvoice

# read csv and determine identifiers
df = pd.read_csv("data/membership-form.csv", skiprows=0, header='infer', delimiter=',')
gni_df = pd.read_csv("data/gni_data.csv", skiprows=3, header='infer', delimiter=',')
wesp_df = pd.read_csv("data/wesp_data.csv", skiprows=4, header='infer', delimiter=',')

# fix a typo
df.iloc[:, 3].replace(['National Commitee (NC)'],  ['National Committee (NC)'], inplace=True)

# collect gni data
df['country'] = None
df['country_code'] = None
df['gni_atlas_method'] = 0.0
df['development_factor'] = 1.0
df['discount_econ_downturn'] = 1.0
df['discount_first_year'] = 1.0
df['discount_lc'] = 1.0
df['discount_probationary'] = 1.0
df['discount_total'] = 1.0
df['fee'] = 9999.99
df['fee_excl_discount'] = 9999.99

# compute quantities for each association
for index, row in df.iterrows():
    df.at[index, 'country'] = row.iloc[7].strip()

    # country code
    country_code = gni_df[gni_df['Country Name'] == df.at[index, 'country']]['Country Code']
    try:
        df.at[index, 'country_code'] = country_code.values[0]
    except IndexError:
        df.at[index, 'country_code'] = 'XXX'

    # gni atlas method
    gni = gni_df[gni_df['Country Name'] == df.at[index, 'country']]['LATEST DATA']
    try:
        df.at[index, 'gni_atlas_method'] = gni.values[0] / 10 ** 6
    except IndexError:
        df.at[index, 'gni_atlas_method'] = 0.0

    # development factor
    country_is_in_wesp_list = wesp_df[wesp_df['Table A'] == df.at[index, 'country']]['Table A']
    if country_is_in_wesp_list.empty:
        df.at[index, 'development_factor'] = 0.5
    else:
        df.at[index, 'development_factor'] = 1.0

    # discount_econ_downturn
    df.at[index, 'discount_econ_downturn'] = 1.0

    # financial year of joining
    financial_year_of_joining_answer = df.iloc[index, 54]
    if financial_year_of_joining_answer == 'did not join as full member so far, my LC/NC joined or applies to join as provisional member in the financial year 2022 (i.e. between September 1, 2022 and August 31, 2023)':
        financial_year_of_joining = 'this_year'
    elif financial_year_of_joining_answer == 'in the last financial year, 2021 (i.e. between September 1, 2021 and August 31, 2022)':
        financial_year_of_joining = 'last_year'
    elif financial_year_of_joining_answer == 'before the financial year of 2021 (i.e. before September 1, 2021)':
        financial_year_of_joining = 'before_last_year'
    else:
        financial_year_of_joining = None

    # first year and probatory discount
    if financial_year_of_joining == 'this_year':
        df.at[index, 'discount_probationary'] = 0.5
    elif financial_year_of_joining == 'last_year':
        df.at[index, 'discount_first_year'] = 0.75

    # lc discount
    if df.iloc[index, 3] == 'Local Committee (LC)':
        df.at[index, 'discount_lc'] = 1.0/3.0

    # compute total discount
    df.at[index, 'discount_total'] = df.at[index, 'discount_econ_downturn'] * \
                                     df.at[index, 'discount_first_year'] * df.at[index, 'discount_probationary'] * \
                                     df.at[index, 'discount_lc']

    # membership fees
    if df.iloc[index, 3] != 'Individual Member (IM)':
        df.at[index, 'fee_excl_discount'] = \
            np.min([400, df.at[index, 'development_factor'] * (
                    75 + 2 * (df.at[index, 'gni_atlas_method']) ** (1 / 3))])

        df.at[index, 'fee'] = df.at[index, 'discount_total'] * df.at[index, 'fee_excl_discount']

    else:
        df.at[index, 'fee_excl_discount'] = 10.0
        df.at[index, 'fee'] = 10.0

# generate invoices
for index, row in df.iterrows():
    print(f"Creating invoice number {index}...")
    client = Member(
        society=row.iloc[5],
        careof=row.iloc[22],
        firstname=row.iloc[34],
        lastname=row.iloc[35],
        street=row.iloc[23],
        additional=row.iloc[24],
        postcode=row.iloc[25],
        city=row.iloc[26],
        district=row.iloc[27],
        country=row['country'],
        phone=None,
        email=None,
        country_code=row['country_code'],
        lc_city=row.iloc[53],
        membership_type=row.iloc[3],
        fee=row['fee'],
        fee_excl_discount=row['fee_excl_discount'],
        discount_total=row['discount_total'],
        discount_lc=row['discount_lc'],
        discount_first_year=row['discount_first_year'],
        discount_probationary=row['discount_probationary'],
        discount_econ_downturn=row['discount_econ_downturn'],
        development_factor=row['development_factor'],
        gni_atlas_method=row['gni_atlas_method'],
    )
    makeinvoice(client=client)

print("Exit Code 0")
