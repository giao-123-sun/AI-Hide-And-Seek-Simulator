
# train.py
import torch
import torch.optim as optim
from torch.distributions import Categorical
import numpy as np
from collections import deque
import os  # 1. 导入 os 库

# 导入TensorBoard的SummaryWriter
from torch.utils.tensorboard import SummaryWriter

from game_env import HideAndSeekEnv, NUM_HIDERS
from model import ActorCritic

# --- 超参数 ---
LEARNING_RATE = 0.0005
GAMMA = 0.99 
NUM_EPISODES = 50000
SAVE_EVERY_EPISODES = 50  # 每多少个回合保存一次

# 1. 定义检查点文件路径
CHECKPOINT_PATH = 'seeker_ai_checkpoint.pth'

def main():
    # 初始化环境和模型
    env = HideAndSeekEnv()
    model = ActorCritic(env.observation_space_n, env.action_space_n)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    start_episode = 0

    # --- 2. 加载检查点 (如果存在) ---
    if os.path.exists(CHECKPOINT_PATH):
        print(f"--- Loading checkpoint from {CHECKPOINT_PATH} ---")
        checkpoint = torch.load(CHECKPOINT_PATH)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_episode = checkpoint['episode'] + 1 # 从下一个回合开始
        print(f"--- Resuming training from episode {start_episode} ---")
    else:
        print("--- No checkpoint found, starting from scratch ---")

    writer = SummaryWriter(f'runs/hide_and_seek_ai_v{start_episode}') # 以起始回合命名，方便区分

    # 初始化用于计算动态指标的数据队列
    reward_history = deque(maxlen=100)
    success_history = deque(maxlen=100)
    steps_on_success_history = deque(maxlen=100)
    ammo_on_success_history = deque(maxlen=100)

    print("--- Starting Training with Visualization ---")
    # 修改循环以从正确的起始点开始
    for episode in range(start_episode, NUM_EPISODES):
        log_probs = []
        values = []
        rewards = []
        done = False
        
        state = env.reset()
        
        while not done:
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            action_probs, state_value = model(state_tensor)
            
            dist = Categorical(action_probs)
            action = dist.sample()
            log_prob = dist.log_prob(action)
            
            new_state, reward, done, _ = env.step(action.item())
            
            log_probs.append(log_prob)
            values.append(state_value)
            rewards.append(torch.tensor([reward], dtype=torch.float))
            
            state = new_state
        
        # --- 训练网络 (与之前相同) ---
        returns = []
        R = 0
        for r in reversed(rewards):
            R = r + GAMMA * R
            returns.insert(0, R)
        returns = torch.tensor(returns)
        log_probs = torch.cat(log_probs)
        values = torch.cat(values).squeeze()
        advantage = returns - values
        actor_loss = -(log_probs * advantage.detach()).mean()
        critic_loss = advantage.pow(2).mean()
        loss = actor_loss + critic_loss
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # --- 计算并记录指标 ---
        total_reward_this_episode = sum(r.item() for r in rewards)
        reward_history.append(total_reward_this_episode)
        is_success = env.hiders_found == NUM_HIDERS
        success_history.append(1 if is_success else 0)
        if is_success:
            steps_on_success_history.append(env.step_count)
            ammo_on_success_history.append(10 - env.ammo)

        # --- 3. 保存检查点和写入日志 ---
        if episode % 10 == 0:
            avg_reward = np.mean(reward_history)
            success_rate = np.mean(success_history)
            avg_steps = np.mean(steps_on_success_history) if steps_on_success_history else 0
            avg_ammo = np.mean(ammo_on_success_history) if ammo_on_success_history else 0
            
            print(f"Ep {episode} | Avg Reward: {avg_reward:.2f} | Success Rate: {success_rate:.2f} | Loss: {loss.item():.4f}")
            
            writer.add_scalar('Loss/total_loss', loss.item(), episode)
            writer.add_scalar('Metrics/Average_Reward_100_Eps', avg_reward, episode)
            writer.add_scalar('Metrics/Success_Rate_100_Eps', success_rate, episode)
            if avg_steps > 0: writer.add_scalar('Performance/Avg_Steps_on_Success', avg_steps, episode)
            if avg_ammo > 0: writer.add_scalar('Performance/Avg_Ammo_on_Success', avg_ammo, episode)

        # 定期保存模型
        if episode % SAVE_EVERY_EPISODES == 0 and episode > 0:
            torch.save({
                'episode': episode,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
            }, CHECKPOINT_PATH)
            print(f"--- Checkpoint saved at episode {episode} to {CHECKPOINT_PATH} ---")

    writer.close()
    # 训练完全结束后，再保存一次最终模型
    torch.save(model.state_dict(), 'seeker_ai_final.pth')
    print(f"--- Training Finished. Final model saved to seeker_ai_final.pth ---")

if __name__ == '__main__':
    main()