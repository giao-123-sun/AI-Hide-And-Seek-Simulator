# model.py
import torch
import torch.nn as nn
import torch.nn.functional as F

class ActorCritic(nn.Module):
    def __init__(self, input_dims, n_actions):
        super(ActorCritic, self).__init__()
        
        self.fc1 = nn.Linear(input_dims, 128)
        self.fc2 = nn.Linear(128, 128)
        
        # Actor: 输出动作概率
        self.actor = nn.Linear(128, n_actions)
        
        # Critic: 输出状态价值
        self.critic = nn.Linear(128, 1)

    def forward(self, state):
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        
        action_probs = F.softmax(self.actor(x), dim=-1)
        state_value = self.critic(x)
        
        return action_probs, state_value