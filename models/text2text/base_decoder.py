#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Implementation of a GRU based decoder for text2text problems (e.g. translation)"""
__author__ = "Vincent Marois "

from torch import nn
import torch.nn.functional as F


class DecoderRNN(nn.Module):
    """GRU Decoder for Encoder-Decoder"""

    def __init__(self, hidden_size, output_voc_size):
        """
        Initializes an Decoder network based on a Gated Recurrent Unit.
        :param hidden_size: length of embedding vectors.
        :param output_voc_size: size of the vocabulary set to be embedded by the Embedding layer.
        """
        # call base constructor.
        super(DecoderRNN, self).__init__()
        self.hidden_size = hidden_size

        # Embedding: creates a look-up table of the embedding of a vocabulary set
        # (size: output_voc_size -> output_language.n_words) on vectors of size hidden_size.
        # adds 1 dimension to the shape of the tensor
        # WARNING: input must be of type LongTensor
        self.embedding = nn.Embedding(num_embeddings=output_voc_size, embedding_dim=hidden_size)

        # Apply a multi-layer gated recurrent unit (GRU) RNN to an input sequence.
        # NOTE: default number of recurrent layers is 1
        # 1st parameter: expected number of features in the input -> same as hidden_size because of embedding
        # 2nd parameter: expected number of features in hidden state -> hidden_size.
        # batch_first=True -> input and output tensors are provided as (batch, seq, feature)
        # batch_first=True do not affect hidden states
        self.gru = nn.GRU(input_size=hidden_size, hidden_size=hidden_size, num_layers=1, batch_first=True)

        # Apply a linear transformation to the incoming data: y=Ax+b
        # basically project from the hidden space to the output vocabulary set
        self.out = nn.Linear(in_features=hidden_size, out_features=output_voc_size)

        # Apply the Log(Softmax(x)) function to an n-dimensional input Tensor along the specified dimension
        # doesn't change the shape
        self.softmax = nn.LogSoftmax(dim=-1)

    def forward(self, input, hidden):
        """
        Runs the Decoder.
        :param input: tensor of indices, of size [batch_size x 1] (word by word looping)
        :param hidden: initial hidden state for each element in the input batch.
        Should be of size [1 x batch_size x hidden_size]
        :return:
                - output should be of size [batch_size x 1 x output_voc_size]: tensor containing the
                output features h_t from the last layer of the RNN, for each t.
                - hidden should be of size [1 x batch_size x hidden_size]: tensor containing the hidden state for
                t = seq_length
        """
        embedded = self.embedding(input)
        # should be of shape [batch_size x 1 x hidden_size]

        gru_input = F.relu(embedded)  # doesn't change shape
        gru_output, hidden = self.gru(gru_input, hidden)
        # gru_output: [batch_size x 1 x hidden_size], hidden: [1 x batch_size x hidden_size]

        output = self.out(gru_output)  # [batch_size x 1 x output_voc_size]

        output = self.softmax(output)  # doesn't change shape

        return output, hidden