import numpy as np
from scipy.spatial import distance as dist
class CentroidTracker:
    def __init__(self,max_disappeared=20):
        self.next_object=0
        self.objects={}
        self.disappeared={}
        self.max_disappeared=max_disappeared

    def register(self,centroid):
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1
        return self.next_object_id - 1
    
    def deregister(self,object_id):
        del self.objects[object_id]
        del self.disappeared[object_id]
    
    def update(self,rects):
        
