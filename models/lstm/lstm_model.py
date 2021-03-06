#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) IBM Corporation 2018
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import torch
from torch import nn

from models.sequential_model import SequentialModel


class LSTM(SequentialModel):
    def __init__(self, params):

        super(LSTM, self).__init__(params)

        self.tm_in_dim = params["control_bits"] + params["data_bits"]
        self.data_bits = params["data_bits"]
        try:
            self.output_units = params['output_bits']
        except KeyError:
            self.output_units = params['data_bits']

        self.hidden_state_dim = params["hidden_state_dim"]
        self.num_layers = params["num_layers"]
        assert self.num_layers > 0, "Number of LSTM layers should be > 0"

        # Create the LSTM layers
        self.lstm_layers = nn.ModuleList()
        self.lstm_layers.append(nn.LSTMCell(
            self.tm_in_dim, self.hidden_state_dim))
        self.lstm_layers.extend(
            [nn.LSTMCell(self.hidden_state_dim, self.hidden_state_dim)
             for _ in range(1, self.num_layers)])

        self.linear = nn.Linear(self.hidden_state_dim, self.output_units)

    def forward(self, data_tuple):
        (x, targets) = data_tuple
        # Check if the class has been converted to cuda (through .cuda()
        # method)
        dtype = self.app_state.dtype

        # Create the hidden state tensors
        h = [
            torch.zeros(
                x.size(0),
                self.hidden_state_dim,
                requires_grad=False).type(dtype) for _ in range(
                self.num_layers)]

        # Create the internal state tensors
        c = [
            torch.zeros(
                x.size(0),
                self.hidden_state_dim,
                requires_grad=False).type(dtype) for _ in range(
                self.num_layers)]

        outputs = []

        for x_t in x.chunk(x.size(1), dim=1):
            h[0], c[0] = self.lstm_layers[0](x_t.squeeze(1), (h[0], c[0]))
            for i in range(1, self.num_layers):
                h[i], c[i] = self.lstm_layers[i](h[i - 1], (h[i], c[i]))

            out = self.linear(h[-1])
            outputs += [out]

        outputs = torch.stack(outputs, 1)
        return outputs
