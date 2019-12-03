import numpy as np
from mc_ic import MC_IC

import torch as T
import torch.nn.functional as F
import torch.optim as optim
from dmp_ic import DMP_IC

import time
t0 = time.time()

T.cuda.set_device(1)

net_path = "../data/test_graph/NetHEPT.npy"
IC = DMP_IC(net_path)

def Penal_K(K, lr=0.01, iter=100, rand=False, eval_step=True):
    S = T.zeros(IC.N, requires_grad=True)
    opt = optim.SGD([S], lr=lr)

    INF = []
    LOSS = []
    LOSS_min = 1E+10
    Patient = 10
    
    case_seed = [6024, 2119, 267, 1241, 682, 47, 6573, 2462, 37, 66, 1434, 4469, 592, 512, 12464]

    for i in range(1, iter):
        opt.zero_grad()
        Seed = T.sigmoid(S)
        Sigmas =IC.run(Seed)
        print(IC.Theta_t)
        print(max(IC.Theta_t))

        penal = T.pow(Seed.sum()-K, 2)
        loss = -Sigmas[-1] + penal
        print("Loss = {:.2f}, Penal = {:.2f}".format(loss.item(), penal.item()))
        loss.backward()
        print("GRAD")
        print(T.max(S.grad), T.min(S.grad))
        opt.step()
        
        LOSS.append(loss.item())
        if eval_step: 
            idx = T.argsort(Seed, descending=True)
            seed_list = idx[:K]
            inf = MC_IC(net_path, seed_list.tolist(), mc=1000)[-1]

            Seed_tensor = T.zeros(IC.N); Seed_tensor[seed_list] = 1
            Sigmas = IC.run(Seed_tensor)
            print("Inf  = {:.2f}, DMP_Inf = {:.2f}".format(inf, Sigmas[-1].item()))
            INF.append(inf)

        print("*"*72)
        print(S[case_seed])
        print(S.grad[case_seed])
        print(IC.out_weight_d[case_seed])
        wd_arg = T.argsort(IC.out_weight_d, descending=True)[:K]
        print(IC.out_weight_d[wd_arg])
        print("*"*72)

    # Final...
    Seed = T.sigmoid(S)
    idx = T.argsort(Seed, descending=True)
    seed_list = idx[:K].tolist()
    INF.append(MC_IC(net_path, seed_list, mc=1000)[-1])
    return seed_list, INF, LOSS, Seed.tolist()

Penal_K(15, lr=1E-4, iter=10)
"""
penal_log_10_lr = []
for k in range(15, 51, 2):
    lr_log = []
    for lr in [1E-4]:
        print("***", k, "***", lr)
        lr_log.append(Penal_K(k, lr=lr, iter=10))
    penal_log_10_lr.append(lr_log)
    
penal_log_10_lr_sigma = [[max(log_lr[1]) for log_lr in log_k] for log_k in penal_log_10_lr]
penal_log_10_lr_sigma_max = [max(s) for s in penal_log_10_lr_sigma]

out_weight_degree = IC.out_weight_d
idx = T.argsort(out_weight_degree, descending=True)

import pickle as pkl

with open("lr_sigma_dmp.pkl", "wb") as f:
    pkl.dump(penal_log_10_lr_sigma, f)
with open("lr_sigma_dmp_max.pkl", "wb") as f:
    pkl.dump(penal_log_10_lr_sigma_max, f)
"""