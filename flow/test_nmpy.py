import unittest2

try:
	import numpy as np
	from nmpy import NumpyFeature,StreamingNumpyDecoder
except ImportError:
	np = None

from dependency_injection import Registry
from data import *
from model import BaseModel


class PassThrough(Node):

	def __init__(self,needs = None):
		super(PassThrough,self).__init__(needs = needs)

	def _process(self,data):
		yield data

class BaseNumpyTest(object):
	
	def setUp(self):
		if np is None: self.skipTest('numpy is not available')
		Registry.register(IdProvider,UuidProvider())
		Registry.register(KeyBuilder,StringDelimitedKeyBuilder())
		Registry.register(Database,InMemoryDatabase())
		Registry.register(DataWriter,DataWriter)
	
	def test_can_store_and_retrieve_empty_array(self):
		self._arrange((0,),np.uint8)

	def test_can_store_and_retrieve_1d_float32_array(self):
		self._arrange((33,),np.float32)

	def test_can_store_and_retreive_multidimensional_uint8_array(self):
		self._arrange((12,13),np.uint8)

	def test_can_store_and_retrieve_multidimensional_float32_array(self):
		self._arrange((5,10,11),np.float32)

class GreedyNumpyTest(BaseNumpyTest,unittest2.TestCase):
	
	def _arrange(self,shape,dtype):
		class Doc(BaseModel):
			feat = NumpyFeature(PassThrough,store = True)

		_id = Doc.process(feat = np.zeros(shape,dtype = dtype))
		doc = Doc(_id)
		arr = doc.feat
		self.assertTrue(isinstance(arr,np.ndarray))
		self.assertEqual(np.product(shape),arr.size)
		self.assertEqual(dtype,arr.dtype)

class StreamingNumpyTest(BaseNumpyTest,unittest2.TestCase):
	
	def _arrange(self,shape,dtype):
		class Doc(BaseModel):
			feat = NumpyFeature(\
				PassThrough,
				store = True, 
				decoder = StreamingNumpyDecoder(n_examples = 3))

		_id = Doc.process(feat = np.zeros(shape,dtype = dtype))
		doc = Doc(_id)
		iterator = doc.feat
		arr = np.concatenate(list(iterator))
		self.assertTrue(isinstance(arr,np.ndarray))
		self.assertEqual(np.product(shape),arr.size)
		self.assertEqual(dtype,arr.dtype)