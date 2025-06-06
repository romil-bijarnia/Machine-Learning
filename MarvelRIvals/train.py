# train.py
import torch, torch.nn as nn, torch.optim as optim
import gymnasium as gym
from marvel_env import MarvelRivalsEnv
from torch.distributions import Normal

env   = MarvelRivalsEnv()
obs_dim  = env.observation_space.shape[0]
act_dim  = env.action_space.shape[0]

class Policy(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, 256), nn.ReLU(),
            nn.Linear(256, 256), nn.ReLU(),
        )
        self.mu  = nn.Linear(256, act_dim)
        self.log_std = nn.Parameter(torch.zeros(act_dim))
        self.v    = nn.Linear(256, 1)
    def forward(self, x):
        h = self.net(x)
        return self.mu(h), self.log_std.exp(), self.v(h)

pi = Policy()
opt = optim.Adam(pi.parameters(), lr=3e-4)
clip = 0.2

for epoch in range(4000):
    obs_buf, act_buf, adv_buf, ret_buf, logp_buf = [], [], [], [], []
    obs, _ = env.reset()
    done=False; ep_ret=0; ep_len=0
    while len(obs_buf) < 2048:
        obs_t = torch.as_tensor(obs, dtype=torch.float32)
        mu, std, v = pi(obs_t)
        dist = Normal(mu, std)
        act  = dist.sample()
        logp = dist.log_prob(act).sum(0)
        next_obs, rew, done, _, _ = env.step(act.numpy())
        obs_buf.append(obs); act_buf.append(act); logp_buf.append(logp)
        adv_buf.append(rew - v.item()); ret_buf.append(rew)
        obs = next_obs; ep_ret+=rew; ep_len+=1
        if done: obs,_ = env.reset()

    # convert to tensors
    obs_t = torch.tensor(obs_buf, dtype=torch.float32)
    act_t = torch.stack(act_buf)
    logp_old = torch.stack(logp_buf).detach()
    adv_t = torch.tensor(adv_buf, dtype=torch.float32)
    ret_t = torch.tensor(ret_buf, dtype=torch.float32)

    # one PPO update
    for _ in range(4):
        mu, std, v = pi(obs_t)
        dist = Normal(mu, std)
        logp = dist.log_prob(act_t).sum(-1)
        ratio = torch.exp(logp - logp_old)
        clip_adv = torch.clamp(ratio, 1-clip, 1+clip) * adv_t
        loss_pi = -(torch.min(ratio*adv_t, clip_adv)).mean()
        loss_v  = ((ret_t - v.squeeze())**2).mean()
        loss = loss_pi + 0.5*loss_v
        opt.zero_grad(); loss.backward(); opt.step()
    if epoch % 10 == 0:
        print(f'Epoch {epoch:4d}\tLastEpRet {ep_ret:.3f}\tEpLen {ep_len}')
