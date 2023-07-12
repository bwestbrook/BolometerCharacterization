
import pyvisa


class BoloPyVisa():


    def __init__(self, resource_index=0):
        '''
        '''
        self.dog = 'hi'
        self.rm = pyvisa.ResourceManager('')
        self.resources = self.rm.list_resources()
        if resource_index is not None:
            resource = self.resources[resource_index]
            self.bpv_open_resource(resource)

    def bpv_open_resource(self, resource):
        '''
        '''
        self.inst = self.rm.open_resource('{0}'.format(resource))
        self.inst.write("*CLS")

