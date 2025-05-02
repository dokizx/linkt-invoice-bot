
import pandas as pd
import streamlit as st
import re

st.title("Linkt Invoice Cost Centre Allocator (CSV Only - Fixed Vehicle Mapping)")

# Fixed vehicle-to-cost centre map
rego_to_centre = {
    "168ZJF": "QLD",
    "535WSY": "QLD",
    "XV22JZ": "NSW",
    "S405BNW": "MIL",
    "424XCR": "QLD",
    "817XRK": "QLD",
    "CAS730": "MIL",
    "DGN310": "MIL",
    "361ROZ": "QLD",
    "1HPZ673": "QLD",
    "FLB80M": "NSW",
    "EAI98G": "NSW",
    # Add more regos here...
}

invoice_file = st.file_uploader("Upload Linkt Invoice (CSV only)", type=["csv"])
total_invoice_amount = st.number_input("Total Charged for Invoice Period (incl. GST)", min_value=0.0, format="%.2f")

if invoice_file and total_invoice_amount > 0:
    try:
        # Load CSV and clean values
        invoice_df = pd.read_csv(invoice_file, skiprows=17, on_bad_lines='skip')
        invoice_df = invoice_df[invoice_df['GST'] != 'GST']
        invoice_df['GST'] = invoice_df['GST'].replace('[\$,]', '', regex=True).astype(float)
        invoice_df['Net Amount'] = invoice_df['Net Amount'].replace('[\$,]', '', regex=True).astype(float)
        invoice_df['Total Amount'] = invoice_df['GST'] + invoice_df['Net Amount']
        invoice_df['Current LPN'] = invoice_df['Current LPN'].str.split().str[0]

        # Sum by rego
        rego_summary = invoice_df.groupby('Current LPN')['Total Amount'].sum().reset_index()

        # Map rego to cost centre
        rego_summary['Cost Centre'] = rego_summary['Current LPN'].map(rego_to_centre)

        # Drop rows with no match
        mapped_df = rego_summary.dropna(subset=['Cost Centre'])

        # Group by cost centre
        cost_centre_summary = mapped_df.groupby('Cost Centre')['Total Amount'].sum().reset_index()
        total_raw = cost_centre_summary['Total Amount'].sum()

        cost_centre_summary['Adjusted Total'] = (cost_centre_summary['Total Amount'] * total_invoice_amount / total_raw).round(2)

        st.success("Calculation completed successfully.")
        st.dataframe(cost_centre_summary[['Cost Centre', 'Adjusted Total']])
    except Exception as e:
        st.error(f"Failed to process invoice file: {e}")
