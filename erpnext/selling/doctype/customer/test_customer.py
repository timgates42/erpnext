# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
import unittest

from frappe.test_runner import make_test_records


class TestCustomer(unittest.TestCase):
	def test_party_details(self):
		from erpnext.accounts.party import get_party_details
		
		to_check = {
			'address_display': '_Test Address Line 1\n_Test City\nIndia\nPhone: +91 0000000000', 
			'selling_price_list': None, 
			'customer_group': '_Test Customer Group', 
			'contact_designation': None, 
			'customer_address': '_Test Address-Office', 
			'contact_department': None, 
			'contact_email': 'test_contact_customer@example.com', 
			'contact_mobile': None, 
			'sales_team': [], 
			'contact_display': '_Test Contact For _Test Customer', 
			'contact_person': '_Test Contact For _Test Customer-_Test Customer', 
			'territory': u'_Test Territory', 
			'contact_phone': '+91 0000000000', 
			'customer_name': '_Test Customer'
		}
		
		make_test_records("Address")
		make_test_records("Contact")
						
		details = get_party_details("_Test Customer")
		
		for key, value in to_check.iteritems():
			self.assertEquals(value, details.get(key))
		
	def test_rename(self):
		frappe.rename_doc("Customer", "_Test Customer 1", "_Test Customer 1 Renamed")

		self.assertTrue(frappe.db.exists("Customer", "_Test Customer 1 Renamed"))
		self.assertFalse(frappe.db.exists("Customer", "_Test Customer 1"))
		
		frappe.rename_doc("Customer", "_Test Customer 1 Renamed", "_Test Customer 1")
		

test_ignore = ["Price List"]
			
test_records = [
	[{
		"doctype": "Customer",
		"customer_name": "_Test Customer",
		"customer_type": "Individual",
		"customer_group": "_Test Customer Group",
		"territory": "_Test Territory",
		"company": "_Test Company"
	}],
	[{
		"doctype": "Customer",
		"customer_name": "_Test Customer 1",
		"customer_type": "Individual",
		"customer_group": "_Test Customer Group",
		"territory": "_Test Territory",
		"company": "_Test Company"
	}],
	[{
		"doctype": "Customer",
		"customer_name": "_Test Customer 2",
		"customer_type": "Individual",
		"customer_group": "_Test Customer Group",
		"territory": "_Test Territory",
		"company": "_Test Company"
	}]
]