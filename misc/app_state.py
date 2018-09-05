from misc.singleton import SingletonMetaClass
import torch


class AppState(metaclass=SingletonMetaClass):
    def __init__(self):
        self.visualize = False
        self.convert_non_cuda_types()
        self.set_dtype('float')
        self.set_itype('int')

    def set_dtype(self, flag):
        """
        Sets a global floating point type to be used in the models
        :param flag: string flag indicating a floating point type
        """
        if flag == 'float':
            self.dtype = self.FloatTensor
        elif flag == 'double':
            self.dtype = self.DoubleTensor
        elif flag == 'half':
            self.dtype = self.HalfTensor
        else:
            self.dtype = self.FloatTensor

    def set_itype(self, flag):
        """
        Sets a global integer type to be used in the models
        :param flag: string flag indicating an integer type
        """

        if flag == 'char':
            self.itype = self.CharTensor
        elif flag == 'short':
            self.itype = self.DoubleTensor
        elif flag == 'int':
            self.itype = self.IntTensor
        elif flag == 'long':
            self.itype = self.LongTensor
        else:
            self.itype = self.IntTensor

    def convert_non_cuda_types(self):
        """
        Sets all tensor types to non-cuda data types
        """
        self.use_CUDA = False
        self.FloatTensor = torch.FloatTensor
        self.DoubleTensor = torch.DoubleTensor
        self.HalfTensor = torch.HalfTensor
        self.ByteTensor = torch.ByteTensor
        self.CharTensor = torch.CharTensor
        self.ShortTensor = torch.ShortTensor
        self.IntTensor = torch.IntTensor
        self.LongTensor = torch.LongTensor

    def convert_cuda_types(self):
        """
        Sets all tensor types to cuda data types
        """

        self.use_CUDA = True
        self.FloatTensor = torch.cuda.FloatTensor
        self.DoubleTensor = torch.cuda.DoubleTensor
        self.HalfTensor = torch.cuda.HalfTensor
        self.ByteTensor = torch.cuda.ByteTensor
        self.CharTensor = torch.cuda.CharTensor
        self.ShortTensor = torch.cuda.ShortTensor
        self.IntTensor = torch.cuda.IntTensor
        self.LongTensor = torch.cuda.LongTensor
