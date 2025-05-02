
import pandas as pd
import streamlit as st
import re

st.title("Linkt Invoice Cost Centre Allocator (CSV Only - Fixed Mapping)")

rego_to_centre = {'1UG4PJEOS53F': 'Shepp', '1HBW345': 'WA', 'S442CRR': 'SA', 'AWC839': 'NSW', 'CBZ256': 'VIC', 'EUB59K': 'VIC', 'S942BSE': 'Shepp', '244XOU': 'Qld', 'DYK56N': 'NSW', 'CAS730': 'MIL', '1CW2GS': 'WA', '1WP9VR': 'VIC', '1QM2TF': 'Qld', 'DE04ZL': 'NSW-Wagga', 'CV84HX': 'SA', '1HKT378': 'WA', 'XS45AS': 'NSW', '1IM5WQ': 'SA', 'DBK94R': 'NSW', 'XV22JZ': 'VIC', 'DYB65N': 'NSW', '1NO1SJ': 'VIC', '817XRK': 'Qld', 'XZK390': 'WA', 'EWH67J': 'NSW', 'TL85AC': 'NSW', '1SV5PY': 'Shepp', 'CK18EK': 'NSW', '1QR3RG': 'VIC', 'S424BYC': 'NSW', 'BKF488': 'VIC', '1FS2WW': 'VIC', '(YCE89S)\n1SS9RU': 'VIC', '1WY5HC': 'NSW', 'S405BNW': 'SA', '1LT7LB': 'VIC', '1LT7LD': 'VIC', '1LT7LE': 'WA', '1LT7LF': 'VIC', '1LT7LG': 'VIC', '1LT7LJ': 'VIC', 'XV95PN': 'Shepp', '1IU9EM': 'VIC', 'CVI571': 'MIL', 'ELF87F': 'VIC', 'ELF96M': 'NSW', '535WSY': 'Qld', '1MD8YJ': 'VIC', '1MD8YK': 'VIC', '2AU7YU1QY4FI': 'Shepp', '1QY4FJ': 'VIC', '1JH1FU': 'VIC', '1MH5VB': 'VIC', '168ZJF': 'NSW', '1TJ6HS': 'Shepp', '424XCR': 'Qld', 'CGW232': 'Shepp', '1GYW882': 'WA', '1TJ6IZ': 'Shepp', 'ENE57U': 'Tas', 'Z38137': 'SA', 'ESA90L': 'VIC', '1BL6GN': 'VIC', '1EZY566': 'WA', '1GTN676': 'WA', 'XV28ZD': 'Shepp', 'EAI98G': 'NSW', 'EYN77N': 'NSW', 'EHT70S': 'NSW', 'Z37992': 'Shepp', 'S155CVJ': 'SA', '1IKH693': 'WA', '361ROZ': 'Qld', '2BK7CA': 'VIC', '1PN5DO': 'Shepp', 'CGK67D\n1GIB879': 'VIC', 'EIT66Q': 'NSW', 'DBN979': 'VIC', '1JB9BR': 'NSW', 'ECP30U': 'VIC', '1SD7XR': 'NSW', '1HPZ673': 'Qld', 'S272CBA': 'SA', 'CY21JL': 'NSW', 'AYX222': 'VIC', 'DGN310': 'MIL', 'TN62PQ': 'NSW', 'M63FZ': 'TAS', 'CJ91LQ': 'NSW', 'XP58CT': 'Shepp', 'FLB80M': 'NSW', 'CWG232': 'Shepp'}

invoice_file = st.file_uploader("Upload Linkt Invoice (CSV only)", type=["csv"])
total_invoice_amount = st.number_input("Total Charged for Invoice Period (incl. GST)", min_value=0.0, format="%.2f")

if invoice_file and total_invoice_amount > 0:
    try:
        invoice_df = pd.read_csv(invoice_file, skiprows=17, on_bad_lines='skip')
        invoice_df = invoice_df[invoice_df['GST'] != 'GST']
        invoice_df['GST'] = invoice_df['GST'].replace('[\$,]', '', regex=True).astype(float)
        invoice_df['Net Amount'] = invoice_df['Net Amount'].replace('[\$,]', '', regex=True).astype(float)
        invoice_df['Total Amount'] = invoice_df['GST'] + invoice_df['Net Amount']
        invoice_df['Current LPN'] = invoice_df['Current LPN'].str.split().str[0]

        rego_summary = invoice_df.groupby('Current LPN')['Total Amount'].sum().reset_index()
        rego_summary['Cost Centre'] = rego_summary['Current LPN'].map(rego_to_centre)
        mapped_df = rego_summary.dropna(subset=['Cost Centre'])

        cost_centre_summary = mapped_df.groupby('Cost Centre')['Total Amount'].sum().reset_index()
        total_raw = cost_centre_summary['Total Amount'].sum()

        cost_centre_summary['Adjusted Total'] = (cost_centre_summary['Total Amount'] * total_invoice_amount / total_raw).round(2)

        st.success("Calculation completed successfully.")
        st.dataframe(cost_centre_summary[['Cost Centre', 'Adjusted Total']])
    except Exception as e:
        st.error(f"Failed to process invoice file: {e}")
