#!/usr/bin/env python
"""Die Klasse Package"""
class Package:
	"""Das Package besteht aus einem Namen, einer Version und der URL"""
	def __init__(self, name, version, url):
		"""Erzeugt ein neues Package.
			
		:param name: der Name des Packages
		:param version: die Version des Packages
		:param url: Die URL des Packages
		"""
		self.name = name
		self.version = version
		self.url = url
