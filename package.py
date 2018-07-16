#!/usr/bin/env python
"""Die Klasse Package
Wird fuer Server und Client benutzt."""
class Package:
	"""Das Package besteht aus einem Namen, einer Version und der URL"""
	def __init__(self, name, version, url):
		"""Erzeugt ein neues Package.
			
		:name: der Name des Packages
		:version: die Version des Packages
		:url: Die URL des Packages
		"""
		self.name = name
		self.version = version
		self.url = url
