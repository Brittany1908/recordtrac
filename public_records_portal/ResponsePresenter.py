from public_records_portal import models
from models import Record, Note
import prr

class ResponsePresenter:
	def __init__(self, record = None, note = None):
		if record:
			self.response = record
			self.update_url = "update_a_record_delete"
			if self.response.access:
				self.type = "offline"
			elif self.response.doc_id:
				self.type = "document"
			else:
				self.type = "link"
		if note:
			self.response = note
			self.update_url = "update_a_note_delete"
			self.type = "note"
			if "Request extended" in self.response.text:
				self.type = "extension"
		if self.type=="offline":
			self.icon = "icon-file-alt icon-2x"
		elif self.type=="note":
			self.icon = "icon-edit icon-2x"
		elif self.type=="link":
			self.icon = "icon-link icon-2x"
		elif self.type =="document":
			self.icon = "icon-file-alt icon-2x"
		elif self.type=="extension":
			self.icon = "icon-calendar icon-2x"

	
	def get_update_url(self):
		return self.update_url

	def get_id(self):
		return self.response.id

	def uid(self):
		return self.response.user_id
	
	def display_text(self):
		if self.type == "offline":
			return "%s can be accessed: %s" %(self.response.description, self.response.access)
		elif self.type == "document":
			download_url = self.response.download_url
			if not download_url:
				download_url = prr.get_scribd_download_url(doc_id = self.response.doc_id, record_id = self.response.id)
			return "<a href='%s' rel='tooltip' data-toggle='tooltip' data-placement='right' data-original-title='%s'>%s <i class='icon-external-link'></i></a><a href = '%s' rel='tooltip' data-toggle='tooltip' data-placement='right' data-original-title='%s'> Download file <i class='icon-cloud-download'></i></a>" % (self.response.url, self.response.url, self.response.description, download_url, download_url) 
		elif self.type == "note":
			return self.response.text
		elif self.type == "link":
			return "<a href='%s' rel='tooltip' data-toggle='tooltip' data-placement='right' data-original-title='%s'>%s <i class='icon-external-link'></i></a>" % (self.response.url, self.response.url, self.response.description)
		elif self.type == "extension":
			junk, text = self.response.text.split(":")
			return text

	def get_icon(self):
		return self.icon

	def set_icon(self, icon):
		self.icon = icon

	def date(self):
		return self.response.date_created



