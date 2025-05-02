import pandas as pd
import streamlit as st
import re

st.title("Linkt Invoice Cost Centre Allocator (CSV Only)")

invoice_file = st.file_uploader("Upload Linkt Invoice (CSV only)", type=["csv"])
vehicles_file = st.file_uploader("Upload Vehicle Rego to Cost Centre Excel file", type=["xlsx"])
total_invoice_amount = st.number_input("Total Charged for Invoice Period (incl. GST)", min_value=0.0, format="%.2f")

if invoice_file and vehicles_file and total_invoice_amount > 0:
    try:
        # Load CSV and clean money columns
        invoice_df = pd.read_csv(invoice_file, skiprows=17, on_bad_lines='skip')
        invoice_df = invoice_df[invoice_df['GST'] != 'GST']  # Remove embedded header rows
        invoice_df['GST'] = invoice_df['GST'].replace('[\$,]', '', regex=True).astype(float)
        invoice_df['Net Amount'] = invoice_df['Net Amount'].replace('[\$,]', '', regex=True).astype(float)
        invoice_df['Total Amount'] = invoice_df['GST'] + invoice_df['Net Amount']
        invoice_df['Current LPN'] = invoice_df['Current LPN'].str.split().str[0]

        # Sum per vehicle
        expense_summary = invoice_df.groupby('Current LPN')['Total Amount'].sum().reset_index()
    except Exception as e:
        st.error(f"Failed to process invoice file: {e}")
        st.stop()

    try:
        # Load vehicle rego mapping
        vehicles_df = pd.read_excel(vehicles_file, sheet_name=0, header=None, names=['Rego', 'Cost Centre'])

        # Merge and calculate by cost centre
        merged_df = pd.merge(expense_summary, vehicles_df, left_on='Current LPN', right_on='Rego', how='left')
        cost_centre_summary = merged_df.groupby('Cost Centre')['Total Amount'].sum().reset_index()
        total_raw = cost_centre_summary['Total Amount'].sum()

        cost_centre_summary['Adjusted Total'] = (cost_centre_summary['Total Amount'] * total_invoice_amount / total_raw).round(2)
        st.success("Calculation completed successfully.")
        st.dataframe(cost_centre_summary[['Cost Centre', 'Adjusted Total']])
    except Exception as e:
        st.error(f"Failed to process vehicle file: {e}")
