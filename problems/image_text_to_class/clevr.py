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

"""clevr.py: This file contains 2 classes :

          - ClevrDataset (CLEVR object class): This class creates a Dataset object to represent a CLEVR dataset.
            ClevrDataset build the embedding for questions and answers

          - Clevr (CLEVR Problem class): This class generates batches over a CLEVRDataset object.
            It also has a show_sample() method that displays a sample (image, question, answer).
  """
__author__ = "Vincent Albouy"

import json
import numpy as np
import os
import re
from PIL import Image
import torch
from tqdm import tqdm
import matplotlib.pyplot as plt
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from torch.utils.data.sampler import RandomSampler
from problems.problem import DataTuple
from problems.image_text_to_class.image_text_to_class_problem import ImageTextToClassProblem, ImageTextTuple
from misc.app_state import AppState
from problems.utils.language import Language

app_state = AppState()


class ClevrDataset(Dataset):
    """
    Inherits from the Dataset class to represent the CLEVR dataset. Will be used by the Clevr class below to generate
    batches.
    ---------------
    class Dataset(object): An abstract class representing a Dataset.
    All other datasets should subclass it. All subclasses should override __len__, that provides the size of the dataset
    , and __getitem__, supporting integer indexing in range from 0 to len(self) exclusive.
    """

    def __init__(self, train, clevr_dir, clevrhumans_dir, clevr_humans):
        """
        Instantiate a ClevrDataset object.

        :param train: Boolean to indicate whether or not the dataset is constructed for training.
        :param clevr_dir:  clevr directory
        :param clevrhumans_dir: clevr humans directory
        :param clevrhumans: Boolean - is it training phase?
        
        """
        super(ClevrDataset).__init__()

        # clevr directory
        self.clevr_dir = clevr_dir

        # clevr humans directory
        self.clevrhumans_dir = clevrhumans_dir

        # boolean: clevr humans used?
        self.clevr_humans = clevr_humans

        # boolean: is it training phase?
        self.train = train

        #create an object language from Language class - This object will be used to create the words embeddings
        self.language = Language('lang')

        #building the embeddings
        self.dictionaries = self.build_dictionaries()


        if self.clevr_humans:

            # load appropriate images & questions from clevr humans
            if train:
                quest_json_filename = os.path.join(self.clevrhumans_dir, 'questions', 'CLEVR-Humans-train.json')
                self.img_dir = os.path.join(self.clevr_dir, 'images', 'train')
            else:
                quest_json_filename = os.path.join(self.clevrhumans_dir, 'questions', 'CLEVR-Humans-val.json')
                self.img_dir = os.path.join(self.clevr_dir, 'images', 'val')


            with open(quest_json_filename, 'r') as json_file:
                self.questions = json.load(json_file)['questions']

        else:
            # load appropriate images & questions from clevr
            if train:
                quest_json_filename = os.path.join(self.clevr_dir, 'questions', 'CLEVR_train_questions.json')
                self.img_dir = os.path.join(self.clevr_dir, 'images', 'train')
            else:
                quest_json_filename = os.path.join(self.clevr_dir, 'questions', 'CLEVR_val_questions.json')
                self.img_dir = os.path.join(self.clevr_dir, 'images', 'val')


            with open(quest_json_filename, 'r') as json_file:
                self.questions = json.load(json_file)['questions']


    def tokenize(self, sentence):
        """
        Separate the punctuations from the words to tokenize it afterwards.
        Also lowercase the sentence.

        :param sentence: sentence to process
        :return: 'tokenized' sentence.
        """

        # punctuation should be separated from the words
        s = re.sub('([.,;:!?()])', r' \1 ', sentence)
        s = re.sub('\s{2,}', ' ', s)

        # tokenize
        split = s.split()

        # normalize all words to lowercase
        lower = [w.lower() for w in split]

        return lower

    def build_dictionaries(self):
        """Creates the word embeddings
        
        - 1. Collects all datasets word
        - 2. Uses Language object to create the embeddings
        
         If it is the first time you run this code, it will take longer to load the embedding from torchtext
         """

        print(' ---> Constructing the dictionaries with word embedding, may take some time ')

        #making an empty list of words meant to store all possible datasets words
        words_list = []
        #answer dictionnary with indices empty list
        answ_to_ix = {}


        #loading the right json file to build embeddings from

        if self.clevr_humans:

            if self.train:
                json_train_filename = os.path.join(self.clevrhumans_dir, 'questions', 'CLEVR-Humans-train.json')
            else:
                json_train_filename = os.path.join(self.clevrhumans_dir, 'questions', 'CLEVR-Humans-val.json')

        else:
            if self.train:
                json_train_filename = os.path.join(self.clevr_dir, 'questions', 'CLEVR_train_questions.json')
            else:
                json_train_filename = os.path.join(self.clevr_dir, 'questions', 'CLEVR_val_questions.json')


        # load all words from training data to a list named words_list[]

        with open(json_train_filename, "r") as f:
            questions = json.load(f)['questions']

            for q in tqdm(questions):
                # display a progress bar
                question = self.tokenize(q['question'])
                answer = q['answer']

                for word in question:
                    if word not in words_list:
                        words_list.append(word)

                a = answer.lower()
                if a not in answ_to_ix:
                    ix = len(answ_to_ix) + 1
                    answ_to_ix[a] = ix


        """ build embeddings from the chosen database / Example: glove.6B.100d """

        self.language.build_pretrained_vocab(words_list, vectors='glove.6B.100d')

        ret = ( answ_to_ix)
        return ret

    def to_dictionary_indexes(self, dictionary, sentence):
        """
        Outputs indexes of the dictionary corresponding to the words in the sequence.
        Case insensitive.
        """
        split = self.tokenize(sentence)

        idxs = torch.tensor([dictionary[w] for w in split]).type(app_state.LongTensor)
        return idxs

    def __len__(self):
        """Return the length of the questions set"""
        return len(self.questions)

    def __getitem__(self, idx):
        """
        Getter method to access the dataset and return a sample.
        :param idx: index of the sample to return.
        :return: {'image': image, 'question': question, 'answer': answer, 'current_question': current_question}
        """
        #get current question with indices idx
        current_question = self.questions[idx]

        #load image and convert it to RGB format
        img_filename = os.path.join(self.img_dir, current_question['image_filename'])
        image = Image.open(img_filename).convert('RGB')
        image = np.array(image)

        #choose padding size
        padding_size = 50

        #embed the question
        question = self.language.embed_sentence(current_question['question'])

        #padding the question
        padding = torch.zeros((padding_size - question.size(0), question.size(1)))
        question =torch.cat((question, padding), 0)

        # embed the answer
        #answer = self.language.embed_sentence(current_question['answer'])
        answer = self.to_dictionary_indexes(self.dictionaries, current_question['answer'])

        #make a dictionnary with all the outputs
        sample = {'image': image, 'question': question, 'answer': answer, 'current_question': current_question}

        return sample


class Clevr(ImageTextToClassProblem):
    """CLEVR Problem class: This class generates batches over a ClevrDataset object.
        It also has a show_sample method that displays a sample (image, question, answer)"""

    def __init__(self, params):
        """
        Instantiate the Clevr class.
        :param params: dict of parameters.
        """

        # parse parameters from the params dict
        self.clevr_dir = params['CLEVR_dir']
        self.clevrhumans_dir = params['CLEVR_humans_dir']
        self.train = params['train']
        self.batch_size = params['batch_size']
        self.clevr_humans = params['use_clevr_humans']
        self.clevr_dataset_train = ClevrDataset(self.train, self.clevr_dir, self.clevrhumans_dir, self.clevr_humans)

        # call base constructor

    def generate_batch(self):
        """Generates a batch of size: batch_size and returns it in the tuple data_tuple=(images, questions, answers).
            auxtuple returns the questions and answers (strings) : useful for the visualization"""

        clevr_train_loader = DataLoader(self.clevr_dataset_train, batch_size=self.batch_size,
                                        sampler=RandomSampler(self.clevr_dataset_train))
        clevr_train_loader = next(iter(clevr_train_loader))

        images = clevr_train_loader['image']
        questions = clevr_train_loader['question']
        answers = clevr_train_loader['answer']
        current_questions = clevr_train_loader['current_question']
        aux_tuple = (current_questions['question'], current_questions['answer'])
        image_text_tuple = ImageTextTuple(images, questions)

        return DataTuple(image_text_tuple, answers), aux_tuple

    def show_sample(self, data_tuple, aux_tuple, sample_number=0):
        """displays an image with the corresponding question and answer """

        plt.figure(1)
        ((image, question), answer) = data_tuple
        (written_question, written_answer) = aux_tuple
        image = image[sample_number, :, :, :]
        plt.title(written_question[sample_number])
        plt.xlabel(written_answer[sample_number])
        plt.imshow(image)
        plt.show()


if __name__ == "__main__":
    """Unitest that generates a batch and displays a sample """

    params = {'batch_size': 5, 'CLEVR_dir': 'CLEVR_v1.0', 'CLEVR_humans_dir': 'CLEVR-Humans', 'train': True,
              'use_clevr_humans': True}
    problem = Clevr(params)
    data_tuple, aux_tuple = problem.generate_batch()
    print(data_tuple)
    print(aux_tuple)
    problem.show_sample(data_tuple, aux_tuple, sample_number=2)


