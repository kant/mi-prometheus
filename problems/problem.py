#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""problem.py: contains base class for all problems"""
__author__      = "Tomasz Kornuta"


import collections
from abc import ABCMeta, abstractmethod

_DataTuple = collections.namedtuple('DataTuple', ('inputs', 'targets'))

class DataTuple(_DataTuple):
    """Tuple used by storing batches of data by problems"""
    __slots__ = ()


class Problem(metaclass=ABCMeta):
    """ Class representing base class for all Problems.
    """

    def __init__(self, params):
        """ 
        Initializes problem object.

        :param params: Dictionary of parameters (read from configuration file).        
        """
        # Set default loss function.
        self.loss_function = None


    def set_loss_function(self, loss_function):
        """ Sets loss function.

        :param criterion: Loss function (e.g. nn.CrossEntropyLoss()) that will be set as optimization criterion.
        """
        self.loss_function = loss_function


    @abstractmethod
    def generate_batch(self):
        """
        Generates batch of sequences of given length. 
        Abstract - to be defined in derived classes. 
        """

    def return_generator(self):
        """
        Returns a generator yielding a batch  of size [BATCH_SIZE, 2*SEQ_LENGTH+2, CONTROL_BITS+DATA_BITS].
        Additional elements of sequence are  start and stop control markers, stored in additional bits.
       
        : returns: A tuple: input with shape [BATCH_SIZE, 2*SEQ_LENGTH+2, CONTROL_BITS+DATA_BITS], output 
        """
        # Create "generator".
        while True:
            yield self.generate_batch()

    def evaluate_loss(self, data_tuple, logits, _):
        """ Calculates loss between the predictions/logits and targets (from data_tuple) using the selected loss function.
        
        :param logits: Logits being output of the model.
        :param data_tuple: Data tuple containing inputs and targets.
        :param _: auxiliary tuple (aux_tuple) is not used in this function. 
        """
        # Unpack tuple.
        (_, targets) = data_tuple

        # Compute loss using the provided loss function. 
        loss = self.loss_function(logits, targets)

        return loss

    def add_statistics(self, stat_col):
        """
        Add statistics to collector. 
        EMPTY - To be redefined in inheriting classes.

        :param stat_col: Statistics collector.
        """
        pass
        
    def collect_statistics(self, stat_col, data_tuple, logits, _):
        """
        Base statistics collection. 
        EMPTY - To be redefined in inheriting classes.

        :param stat_col: Statistics collector.
        :param data_tuple: Data tuple containing inputs and targets.
        :param logits: Logits being output of the model.
        :param _: auxiliary tuple (aux_tuple) is not used in this function. 
        """
        pass