import simplejson
import numpy as np

from encoder import IdentityEncoder,JSONEncoder,ShittyNumpyEncoder,TextEncoder
from decoder import JSONDecoder,Decoder,GreedyDecoder,DecoderExtractor
from dependency_injection import dependency
from data import DataWriter,DataReader,StringIODataWriter

class Feature(object):
    
    def __init__(\
            self,
            extractor,
            needs = None,
            store = False, 
            encoder = None, 
            decoder = None,
            key = None,
            data_writer = None,
            **extractor_args):
        
        super(Feature,self).__init__()
        self.key = key
        self.extractor = extractor
        self.store = store
        self.encoder = encoder or IdentityEncoder
        
        if needs is None:
            self.needs = []
        elif isinstance(needs,list):
            self.needs = needs
        else:
            self.needs = [needs]
        
        self.decoder = decoder or Decoder()
        self.extractor_args = extractor_args

        if data_writer:
            self._data_writer = data_writer

    def copy(self,extractor = None,needs = None,store = None,data_writer = None,extractor_args = None):
        return Feature(\
            extractor or self.extractor,
            needs = needs,
            store = self.store if store is None else store,
            encoder = self.encoder,
            decoder = self.decoder,
            key = self.key,
            data_writer = data_writer,
            **(extractor_args or self.extractor_args))

    def add_dependency(self,feature):
        self.needs.append(feature)

    @property
    def is_root(self):
        return not self.needs      
    
    @property
    def content_type(self):
        return self.encoder.content_type
    
    @dependency(DataWriter)
    def _data_writer(self,needs = None, _id = None, feature_name = None):
        pass

    @dependency(DataReader)
    def reader(self,_id,key):
        pass

    def _can_compute(self):
        if self.store:
            return True

        if self.is_root:
            return False

        return all([n._can_compute() for n in self.needs])

    def _partial(self,_id,features = None):

        if self.store and features is None:
            raise Exception('There is no need to build a partial graph for a stored feature')

        nf = self.copy(\
            extractor = DecoderExtractor if self.store else self.extractor,
            store = not self.store,
            needs = None,
            data_writer = StringIODataWriter if features is None else None,
            extractor_args = dict(decodifier = self.decoder) if self.store else self.extractor_args)

        if features is None:
            features = dict()

        features[self.key] = nf

        for n in self.needs:
            n._partial(_id,features = features)
            nf.add_dependency(features[n.key])

        return features

    def _depends_on(self,_id,extractors):
        needs = []
        for f in self.needs:
            if extractors[f.key]:
                needs.append(extractors[f.key])
                continue
            e = f._build_extractor(_id,extractors)
            needs.append(e)
        return needs

    def _build_extractor(\
            self,
            _id,
            extractors = None):
        if extractors[self.key]:
            return extractors[self.key]
        needs = self._depends_on(_id,extractors)
        e = self.extractor(needs = needs,**self.extractor_args)
        extractors[self.key] = e
        if not self.store: return e
        encoder = self.encoder(needs = e)
        # TODO: Here the DataWriter is monolithic.  What if the data writer 
        # varies by feature, e.g., some values are written to a database, while
        # others are published to a work queue?
        self._data_writer(needs = encoder, _id = _id, feature_name = self.key)
        return e

class JSONFeature(Feature):
    
    def __init__(self,extractor,needs = None,store = False,key = None,**extractor_args):
        super(JSONFeature,self).__init__(\
            extractor,
            needs = needs,
            store = store,
            encoder = JSONEncoder,
            decoder = JSONDecoder(),
            key = key,
            **extractor_args)

class NumpyFeature(Feature):
    
    def __init__(self,extractor,needs = None,store = False,key = None,**extractor_args):
        super(NumpyFeature,self).__init__(\
            extractor,
            needs = needs,
            store = store,
            encoder = ShittyNumpyEncoder,
            decoder = lambda x : np.fromstring(x.read(),dtype = np.float32),
            key = key,
            **extractor_args)

class TextFeature(Feature):
    
    def __init__(self,extractor,needs = None,store = False,key = None,**extractor_args):
        super(TextFeature,self).__init__(\
            extractor,
            needs = needs,
            store = store,
            encoder = TextEncoder,
            decoder = GreedyDecoder(),
            key = key,
            **extractor_args)

