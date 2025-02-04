import codecs
import os
import collections
from six.moves import cPickle
import numpy as np
from ted.ted import TED

class TextLoader():


    def __init__(self, data_dir, batch_size, seq_length, encoding='utf-8'):
        self.data_dir = data_dir
        self.batch_size = batch_size
        self.seq_length = seq_length
        self.encoding = encoding

        input_file = os.path.join(data_dir, "oh_input.txt")
        vocab_file = os.path.join(data_dir, "oh_vocab.pkl")
        tensor_file = os.path.join(data_dir, "oh_data.npy")

        self.process(input_file, vocab_file, tensor_file)

        self.create_batches()
        self.reset_batch_pointer()


    def process(self, input_file, vocab_file, tensor_file):
        self.ted = TED("ted")
        self.ted.normalize_profiles_locally()
        self.ted.normalize_views()
        self.ted.generate_tokenized_vocab()
        
        self.vocab_size = self.ted.vocab_size
        self.vocab_list = self.ted.vocab_list
        self.vocab = dict(zip(self.ted.vocab_list, range(self.ted.vocab_size)))
        self.tensor = np.array([self.vocab[word] for word in self.ted.words])


    def create_batches(self):
        self.num_batches = int(len(self.tensor) / (self.batch_size *
                                                   self.seq_length))

        # When the data (tensor) is too small, let's give them a better error message
        if self.num_batches==0:
            assert False, "Not enough data. Make seq_length and batch_size small."

        self.tensor = self.tensor[:self.num_batches * self.batch_size * self.seq_length]
        xdata = self.tensor
        ydata = np.copy(self.tensor)
        ydata[:-1] = xdata[1:]
        ydata[-1] = xdata[0]
        self.x_batches = np.split(xdata.reshape(self.batch_size, -1), self.num_batches, 1)
        self.y_batches = np.split(ydata.reshape(self.batch_size, -1), self.num_batches, 1)


    def next_batch(self):
        word_count = self.pointer * self.batch_size * self.seq_length
        if word_count >= self.ted.talk_counts[self.profile_pointer]:
            self.profile_pointer += 1
            
        profile = self.ted.profiles[self.profile_pointer]
        views = self.ted.views[self.profile_pointer]

        x, y = self.x_batches[self.pointer], self.y_batches[self.pointer]
        self.pointer += 1
        if self.pointer >= len( self.x_batches ):
            self.reset_batch_pointer()

        profile = np.array([profile for i in range(self.batch_size)])
        views = np.array([views for i in range(self.batch_size)])
        views = np.reshape(views, (self.batch_size, 1))

        return x, y, profile, views


    def random_batch(self):
        pointer = np.random.randint(len(self.x_batches))

        word_count = pointer * self.batch_size * self.seq_length
        profile_pointer = 0
        while profile_pointer < len(self.ted.talk_counts) and word_count < self.ted.talk_counts[profile_pointer]:
            profile_pointer += 1
        
        profile_pointer -= 1
 
        x = self.x_batches[pointer]
        y = self.y_batches[pointer]

        profile = self.ted.profiles[profile_pointer]
        profile = np.array([profile for i in range(self.batch_size)])
        views = self.ted.views[profile_pointer]
        views = np.array([views for i in range(self.batch_size)])
        views = np.reshape(views, (self.batch_size, 1))

        return x, y, profile, views


    def reset_batch_pointer(self):
        self.pointer = 0
        self.profile_pointer = 0
        

if __name__ == "__main__":
    t = TextLoader( ".", 50, 50 )