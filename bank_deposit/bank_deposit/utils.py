from datetime import date
import frappe

def create_journal_entry_from_deposit(doc):
    if not doc.deposit_details:
        frappe.throw("No deposit entries found.")

    journal_entry = frappe.new_doc("Journal Entry")
    journal_entry.posting_date = doc.deposit_date or date.today()
    journal_entry.voucher_type = "Bank Entry"
    journal_entry.remark = f"Bank Deposit from Undeposited Funds via {doc.name}"
    journal_entry.company = frappe.defaults.get_global_default("company")

    total_amount = 0
    customer_invoice_summary = []

    journal_entry.append("accounts", {
        "account": doc.bank_account,
        "debit_in_account_currency": 0,
        "reference_type": "",
        "reference_name": ""
    })

    for row in doc.deposit_details:
        payment = frappe.get_doc("Payment Entry", row.payment_entry)
        if payment.docstatus != 1:
            frappe.throw(f"Payment Entry {payment.name} is not submitted.")

        invoice_refs = frappe.get_all("Payment Entry Reference", 
                                      filters={"parent": payment.name},
                                      fields=["reference_name"])

        for inv in invoice_refs:
            journal_entry.append("accounts", {
                "account": payment.paid_to,
                "credit_in_account_currency": payment.paid_amount,
                "reference_type": "Sales Invoice",
                "reference_name": inv.reference_name,
                "party_type": "Customer",
                "party": payment.party
            })
            customer_invoice_summary.append(f"{payment.party} - {inv.reference_name}")
            total_amount += payment.paid_amount

        payment.db_set("custom_is_deposited", 1)

    journal_entry.accounts[0].debit_in_account_currency = total_amount
    journal_entry.save()
    journal_entry.submit()

    doc.db_set("journal_entry", journal_entry.name)

    if customer_invoice_summary:
        summary = "Included Invoices:\n" + "\n".join(customer_invoice_summary)
        doc.add_comment("Info", summary)

    return journal_entry.name