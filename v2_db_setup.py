#!/usr/bin/env python2
# Version 2. 12-11-18.
# Database setup for project_catalogue

import sys
import os

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

##############
### Tables

class FoodCategory(Base):
	# Name 
	__tablename__ = 'foodcategory'

	# Columns
	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = False)

	@property
	def serialize(self):
		"""Return object data in easily serializeable format"""
		return {
		'id' 		: self.id,
		'name'		: self.name
	}	

class FoodItem(Base):
	# name
	__tablename__ = 'fooditem'

	# columns
	id = Column(Integer, primary_key = True)
	name = Column(String(100), nullable = False)
	description = Column(String(250))
	price = Column(String(8))

	# foreign keys	
	foodcategory_id = Column(Integer, ForeignKey('foodcategory.id'))
	foodcategory = relationship(FoodCategory)

	@property
	def serialize(self):
		return {
		'id': self.id,
		'name': self.name,
		'description': self.description,
		'price': self.price,
		}
	
engine = create_engine('sqlite:///grocer.db')   
Base.metadata.create_all(engine)  