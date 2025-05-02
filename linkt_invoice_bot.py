
import pandas as pd
import streamlit as st
import pdfplumber
import re
from collections import defaultdict

st.title("Linkt Invoice Cost Centre Allocator")

invoice_file = st.file_uploader("Upload Linkt Invoice (CSV or PDF)", type=["csv", "pdf"])
vehicles_file = st.file_uploader("Upload Vehicle Rego to Cost Centre Excel file", type=["xlsx"])
total_invoice_amount = st.number_input("Total Charged for Invoice Period (incl. GST)", min_value=0.0, format="%.2f")

@st.cache_data
def extract_expenses_from_pdf(pdf_file):
    charges = defaultdict(float)
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            # Match trips without a tag (lines with Fleet ID, Licence plate, Trips, and Amount)
            matches = re.findall(r"\n\s*.+?\s+([A-Z0-9]{3,})\s+[A-Z]{2,3}\s+[A-Z]{2,3}\s+\d+\s+\$(\d+\.\d{2})", text)
            for rego, amount in matches:
                charges[rego] += float(amount)

            # Match video matching fees
            video_matches = re.findall(r"Video Matching Fee-([A-Z0-9]{3,}) .*?\$(\d+\.\d{2})", text)
            for rego, amount in video_matches:
                charges[rego] += float(amount)

    return pd.DataFrame(list(charges.items()), columns=['Current LPN', 'Total Amount'])

if invoice_file and vehicles_file and total_invoice_amount > 0:
    try:
        if invoice_file.name.endswith(".csv"):
            invoice_df = pd.read_csv(invoice_file, skiprows=17, on_bad_lines='skip')
            invoice_df = invoice_df[invoice_df['GST'] != 'GST']
            invoice_df['GST'] = invoice_df['GST'].replace('[\$,]', '', regex=True).astype(float)
            invoice_df['Net Amount'] = invoice_df['Net Amount'].replace('[\$,]', '', regex=True).astype(float)
            invoice_df['Total Amount'] = invoice_df['GST'] + invoice_df['Net Amount']
            invoice_df['Current LPN'] = invoice_df['Current LPN'].str.split().str[0]
            expense_summary = invoice_df.groupby('Current LPN')['Total Amount'].sum().reset_index()
        elif invoice_file.name.endswith(".pdf"):
            expense_summary = extract_expenses_from_pdf(invoice_file)
        else:
            st.error("Unsupported file format. Please upload CSV or PDF.")
            st.stop()
    except Exception as e:
        st.error(f"Failed to process invoice file: {e}")
        st.stop()

    try:
        vehicles_df = pd.read_excel(vehicles_file, sheet_name=0, header=None, names=['Rego', 'Cost Centre'])
        merged_df = pd.merge(expense_summary, vehicles_df, left_on='Current LPN', right_on='Rego', how='left')
        cost_centre_summary = merged_df.groupby('Cost Centre')['Total Amount'].sum().reset_index()
        total_raw = cost_centre_summary['Total Amount'].sum()
        cost_centre_summary['Adjusted Total'] = (cost_centre_summary['Total Amount'] * total_invoice_amount / total_raw).round(2)
        st.success("Calculation completed successfully.")
        st.dataframe(cost_centre_summary[['Cost Centre', 'Adjusted Total']])
    except Exception as e:
        st.error(f"Failed to process vehicle file: {e}")
