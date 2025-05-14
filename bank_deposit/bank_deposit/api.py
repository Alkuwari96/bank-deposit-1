import frappe
from bank_deposit.bank_deposit.utils import create_journal_entry_from_deposit

@frappe.whitelist()
def create_journal_entry_from_deposit(docname):
    doc = frappe.get_doc("Bank Deposit", docname)
    return create_journal_entry_from_deposit(doc)