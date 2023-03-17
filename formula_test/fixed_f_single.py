# calculate optimized g with fixed f
# calculate h score

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import numpy as np
from matplotlib import pyplot as plt
from torch.utils.data import Dataset,DataLoader,TensorDataset
import loading
from fixed_f_vanilla import vanilla_fg


class single_fg(vanilla_fg):

    '''
    calculation with fixed feature extractor with single source transfer only
    '''

    def __init__(self, data_path, model_path, t_id, batch_size=None, s_id=0):
        
        super(single_fg, self).__init__(data_path=data_path, model_path=model_path, t_id=t_id, batch_size=batch_size)   
        self.data_s = loading.load_data(path = data_path, id = s_id)

    
    def get_transfer_g(self):
        pass


    def get_g_s(self, alpha=0.2):

        images, labels = next(iter(self.data))
        # take the first batch as input data
        labels_one_hot = torch.zeros(len(labels), self.n_label).scatter_(1, labels.view(-1,1), 1)
        f = self.model_f(Variable(images).to(self.device)).cpu().detach().numpy()
        g = self.model_g(Variable(labels_one_hot).to(self.device)).cpu().detach().numpy()

        images_s, labels_s = next(iter(self.data_s))
        labels_one_hot_s = torch.zeros(len(labels_s), self.n_label).scatter_(1, labels_s.view(-1,1), 1)
        f_s = self.model_f(Variable(images_s).to(self.device)).cpu().detach().numpy()
        g_s = self.model_g(Variable(labels_one_hot_s).to(self.device)).cpu().detach().numpy()

        # g = self.get_transfer_g()
        g = (1-alpha) * g + alpha * g_s

        # expectation and normalization of f and g
        e_f = f.mean(0)
        n_f = f - e_f
        # e_g = g.mean(0)
        # n_g = g - e_g

        gamma_f = n_f.T.dot(n_f) / n_f.shape[0]

        ce_f = self. get_conditional_exp(f, images, labels)
        ce_f_s = self. get_conditional_exp(f_s, images_s, labels_s)
        g_y_hat = np.linalg.inv(gamma_f).dot(((1-alpha) * ce_f + alpha * ce_f_s).T).T
        
        g_y = np.array([g[torch.where(labels == i)][0] for i in range(labels.max()+1)])
        
        g_rand = np.random.random(g_y.shape)

        return g_rand, g_y, g_y_hat



    # # classification accuracy with different gy
    # def get_accuracy(self, gc):
        
    #     acc = 0
    #     total = 0

    #     for images, labels in self.test_data:

    #         labels= labels.numpy()
    #         fc=self.model_f(Variable(images).to(self.device)).data.cpu().numpy()
    #         f_mean=np.sum(fc,axis=0)/fc.shape[0]
    #         fcp=fc-f_mean
            
    #         gce=np.sum(gc,axis=0)/self.n_label
    #         gcp=gc-gce
    #         fgp=np.dot(fcp,gcp.T)
    #         acc += (np.argmax(fgp, axis = 1) == labels).sum()
    #         print(np.where(np.argmax(fgp, axis = 1) != labels))
    #         total += len(images)

    #     acc = float(acc) / total
    #     return acc



if __name__ == '__main__':
    import time

    DATA_PATH = "/home/viki/Codes/MultiSource/2/multi-source/data_set_2/"
    MODEL_PATH = "/home/viki/Codes/MultiSource/3/formula_test/weight/"
    SAVE_PATH = "/home/viki/Codes/MultiSource/3/formula_test/results/"
    N_TASK = 21
    alpha = 0.4

    for t_id in range(21):

        acc = np.zeros((N_TASK,3))
        
        for id in range(21):
            cal = single_fg(DATA_PATH, MODEL_PATH, t_id=t_id, s_id=id)
            
            g_r, g, g_hat = cal.get_g_s(alpha)
            rand = cal.get_accuracy(gc=g_r)
            org = cal.get_accuracy(gc=g)
            hat = cal.get_accuracy(gc=g_hat)
            print("-------------source_task_id:{:d}-------------".format(id))
            print("random:{:.1%}\noriginal:{:.1%}\ncalculated:{:.1%}\n".format(rand, org, hat))
            acc[id] = rand, org, hat
            print("-------------end-------------")

        np.savetxt(SAVE_PATH+'single_acc_table_'+time.strftime("%m%d", time.localtime())+'_alpha='+str(alpha)+'_t='+str(t_id)+'.npy', acc)