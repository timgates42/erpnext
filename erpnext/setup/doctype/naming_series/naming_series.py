# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.utils import cstr
from frappe import msgprint, throw, _
import frappe.model.doctype

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def get_transactions(self, arg=None):
		return {
			"transactions": "\n".join([''] + sorted(list(set(
				frappe.db.sql_list("""select parent
					from `tabDocField` where fieldname='naming_series'""") 
				+ frappe.db.sql_list("""select dt from `tabCustom Field` 
					where fieldname='naming_series'""")
				)))),
			"prefixes": "\n".join([''] + [i[0] for i in 
				frappe.db.sql("""select name from tabSeries order by name""")])
		}

	def scrub_options_list(self, ol):
		options = filter(lambda x: x, [cstr(n.upper()).strip() for n in ol])
		return options

	def update_series(self, arg=None):
		"""update series list"""
		self.check_duplicate()
		series_list = self.doc.set_options.split("\n")

		# set in doctype
		self.set_series_for(self.doc.select_doc_for_series, series_list)

		# create series
		map(self.insert_series, [d.split('.')[0] for d in series_list])

		msgprint(_("Series Updated"))

		return self.get_transactions()

	def set_series_for(self, doctype, ol):
		options = self.scrub_options_list(ol)

		# validate names
		for i in options: self.validate_series_name(i)

		if self.doc.user_must_always_select:
			options = [''] + options
			default = ''
		else:
			default = options[0]

		# update in property setter
		from frappe.model.doc import Document
		prop_dict = {'options': "\n".join(options), 'default': default}
		for prop in prop_dict:
			ps_exists = frappe.db.sql("""SELECT name FROM `tabProperty Setter`
					WHERE doc_type = %s AND field_name = 'naming_series'
					AND property = %s""", (doctype, prop))
			if ps_exists:
				ps = Document('Property Setter', ps_exists[0][0])
				ps.value = prop_dict[prop]
				ps.save()
			else:
				ps = Document('Property Setter', fielddata = {
					'doctype_or_field': 'DocField',
					'doc_type': doctype,
					'field_name': 'naming_series',
					'property': prop,
					'value': prop_dict[prop],
					'property_type': 'Select',
				})
				ps.save(1)

		self.doc.set_options = "\n".join(options)

		frappe.clear_cache(doctype=doctype)

	def check_duplicate(self):
		from frappe.core.doctype.doctype.doctype import DocType
		dt = DocType()

		parent = list(set(
			frappe.db.sql_list("""select dt.name 
				from `tabDocField` df, `tabDocType` dt 
				where dt.name = df.parent and df.fieldname='naming_series' and dt.name != %s""",
				self.doc.select_doc_for_series)
			+ frappe.db.sql_list("""select dt.name 
				from `tabCustom Field` df, `tabDocType` dt 
				where dt.name = df.dt and df.fieldname='naming_series' and dt.name != %s""",
				self.doc.select_doc_for_series)
			))
		sr = [[frappe.model.doctype.get_property(p, 'options', 'naming_series'), p] 
			for p in parent]
		options = self.scrub_options_list(self.doc.set_options.split("\n"))
		for series in options:
			dt.validate_series(series, self.doc.select_doc_for_series)
			for i in sr:
				if i[0]:
					existing_series = [d.split('.')[0] for d in i[0].split("\n")]
					if series.split(".")[0] in existing_series:
						throw("{oops}! {sr} {series} {msg} {existing_series}. {select}".format(**{
							"oops": _("Oops"),
							"sr": _("Series Name"),
							"series": series,
							"msg": _("is already in use in"),
							"existing_series": i[1],
							"select": _("Please select a new one")
						}))

	def validate_series_name(self, n):
		import re
		if not re.match("^[a-zA-Z0-9-/.#]*$", n):
			throw('Special Characters except "-" and "/" not allowed in naming series')

	def get_options(self, arg=''):
		sr = frappe.model.doctype.get_property(self.doc.select_doc_for_series, 
			'options', 'naming_series')
		return sr

	def get_current(self, arg=None):
		"""get series current"""
		if self.doc.prefix:
			self.doc.current_value = frappe.db.get_value("Series", 
				self.doc.prefix.split('.')[0], "current")

	def insert_series(self, series):
		"""insert series if missing"""
		if not frappe.db.exists('Series', series):
			frappe.db.sql("insert into tabSeries (name, current) values (%s, 0)", (series))

	def update_series_start(self):
		if self.doc.prefix:
			prefix = self.doc.prefix.split('.')[0]
			self.insert_series(prefix)
			frappe.db.sql("update `tabSeries` set current = %s where name = %s", 
				(self.doc.current_value, prefix))
			msgprint(_("Series Updated Successfully"))
		else:
			msgprint(_("Please select prefix first"))

def set_by_naming_series(doctype, fieldname, naming_series, hide_name_field=True):
	from frappe.core.doctype.property_setter.property_setter import make_property_setter
	if naming_series:
		make_property_setter(doctype, "naming_series", "hidden", 0, "Check")
		make_property_setter(doctype, "naming_series", "reqd", 1, "Check")

		# set values for mandatory
		frappe.db.sql("""update `tab{doctype}` set naming_series={s} where 
			ifnull(naming_series, '')=''""".format(doctype=doctype, s="%s"), 
			get_default_naming_series(doctype))

		if hide_name_field:
			make_property_setter(doctype, fieldname, "reqd", 0, "Check")
			make_property_setter(doctype, fieldname, "hidden", 1, "Check")
	else:
		make_property_setter(doctype, "naming_series", "reqd", 0, "Check")
		make_property_setter(doctype, "naming_series", "hidden", 1, "Check")

		if hide_name_field:
			make_property_setter(doctype, fieldname, "hidden", 0, "Check")
			make_property_setter(doctype, fieldname, "reqd", 1, "Check")

			# set values for mandatory
			frappe.db.sql("""update `tab{doctype}` set `{fieldname}`=`name` where 
				ifnull({fieldname}, '')=''""".format(doctype=doctype, fieldname=fieldname))

def get_default_naming_series(doctype):
	from frappe.model.doctype import get_property
	naming_series = get_property(doctype, "options", "naming_series")
	naming_series = naming_series.split("\n")
	return naming_series[0] or naming_series[1]