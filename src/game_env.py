# game_env.py
import numpy as np
from ursina import *
import random

# --- 游戏世界的配置 (可以从之前的文件复制) ---
# ... (此处省略PROP_TYPES, LEVEL_LAYOUT, WAYPOINTS等定义，请从之前的代码复制)
PROP_TYPES = {
    'desk': {'model': 'cube', 'scale': (4, 1, 2), 'color': color.brown},
    'chair': {'model': 'cube', 'scale': (1, 2, 1), 'color': color.black},
    'plant_pot': {'model': 'cylinder', 'scale': (1.5, 0.8, 1.5), 'color': color.orange},
    'plant_leaves': {'model': 'cylinder', 'scale': (1.2, 2.5, 1.2), 'color': color.green},
    'monitor': {'model': 'cube', 'scale': (1.5, 1, 0.2), 'color': color.dark_gray},
    'partition': {'model': 'cube', 'scale': (0.2, 4, 8), 'color': color.rgba(200, 200, 200, 200)},
}
LEVEL_LAYOUT = [ ('desk', (-12, 0, 10)), ('monitor', (-12, 0.5, 10)), ('chair', (-12, 0, 8)), ('desk', (-12, 0, 0)), ('monitor', (-12, 0.5, 0)), ('chair', (-12, 0, -2)), ('desk', (-12, 0, -10)), ('monitor', (-12, 0.5, -10)), ('chair', (-12, 0, -12)), ('partition', (-8, 0, 5)), ('desk', (12, 0, 10)), ('monitor', (12, 0.5, 10)), ('chair', (12, 0, 8)), ('desk', (12, 0, 0)), ('monitor', (12, 0.5, 0)), ('chair', (12, 0, -2)), ('desk', (12, 0, -10)), ('monitor', (12, 0.5, -10)), ('chair', (12, 0, -12)), ('partition', (8, 0, 5)), ('plant_pot', (0, 0, 0)), ('plant_pot', (0, 0, 5)), ]
NUM_HIDERS = 3

class Prop(Entity):
    # ... (Prop类的定义与之前相同)
    def __init__(self, **kwargs):
        super().__init__(collider='box', **kwargs)
        self.is_hider = False
        self.shot = False
        self.checked_by_ai = False
    def get_shot(self):
        if self.shot: return False
        if self.is_hider:
            self.color = color.red; self.shot = True; return True
        return False

class HideAndSeekEnv:
    def __init__(self):
        self.app = Ursina(borderless=False, development_mode=False, window_title="AI Training Environment")
        # 观察空间: AI位置(2), AI朝向(1), 最近3个未检查道具的相对位置(3*2=6)
        # Total = 2 + 1 + 6 = 9
        self.observation_space_n = 9
        # 动作空间: 0:前进, 1:后退, 2:左转, 3:右转, 4:开火
        self.action_space_n = 5
        self.game_over = False
        self.max_steps = 1000 # 每局游戏的最大步数

        # 关闭默认的相机控制器
        camera.position = (0, 30, -35)
        camera.rotation_x = 45


    def reset(self):
        """重置环境到初始状态"""
        # --- THE FIX ---
        # Access the global 'scene' object directly, not through 'self.app'
        [destroy(e) for e in scene.children if isinstance(e, (Prop, SeekerAI))]
        
        self.step_count = 0
        self.game_over = False
        self.hiders_found = 0
        self.ammo = 10
        self.all_props = self._setup_scene()
        self.seeker = self._setup_seeker()
        
        # After resetting, we need to re-enable the main scene light and sky
        # as they might be destroyed if not handled carefully.
        # A simple way is to ensure they aren't parented to something that gets destroyed,
        # or re-initialize them if needed. For now, the destroy logic is specific enough.
        
        return self._get_observation()
    def _setup_scene(self):
        """创建场景和道具"""
        all_props = []
        hider_choices = random.sample(LEVEL_LAYOUT, NUM_HIDERS)
        for i, (prop_type, pos) in enumerate(LEVEL_LAYOUT):
            # ... (创建道具的代码与之前相同)
            prop_info = PROP_TYPES[prop_type]; is_hider = (prop_type, pos) in hider_choices
            if prop_type == 'plant_pot':
                pot = Prop(name=f'prop_{i}_pot', model=prop_info['model'], scale=prop_info['scale'], color=prop_info['color'], position=pos, is_hider=is_hider)
                leaves = Prop(name=f'prop_{i}_leaves', model=PROP_TYPES['plant_leaves']['model'], scale=PROP_TYPES['plant_leaves']['scale'], color=PROP_TYPES['plant_leaves']['color'], position=pos+(0, prop_info['scale'][1], 0), is_hider=is_hider)
                all_props.extend([pot, leaves])
            else:
                entity = Prop(name=f'prop_{i}', model=prop_info['model'], scale=prop_info['scale'], color=prop_info['color'], position=pos, is_hider=is_hider)
                if prop_type == 'monitor': entity.y += 0.5
                all_props.append(entity)
        return all_props

    def _setup_seeker(self):
        return SeekerAI(position=(0, 0.5, -15))

    def _get_observation(self):
        """生成AI的观察向量"""
        obs = np.zeros(self.observation_space_n)
        # AI自身状态
        obs[0] = self.seeker.x / 20 # 归一化
        obs[1] = self.seeker.z / 20 # 归一化
        obs[2] = self.seeker.rotation_y / 360 # 归一化

        # 最近的3个未检查道具
        unchecked_props = [p for p in self.all_props if not p.checked_by_ai]
        unchecked_props.sort(key=lambda p: distance_xz(self.seeker.position, p.position))
        
        for i in range(min(3, len(unchecked_props))):
            prop = unchecked_props[i]
            obs[3 + i*2] = (prop.x - self.seeker.x) / 20 # 相对位置
            obs[4 + i*2] = (prop.z - self.seeker.z) / 20 # 相对位置
        
        return obs

    def step(self, action):
        """执行一个动作，返回(观察, 奖励, 是否结束, 信息)"""
        self.step_count += 1
        reward = -0.01 # 时间流逝惩罚

        # 执行动作
        if action == 0: self.seeker.position += self.seeker.forward * self.seeker.speed * time.dt
        elif action == 1: self.seeker.position -= self.seeker.forward * self.seeker.speed * time.dt
        elif action == 2: self.seeker.rotation_y -= self.seeker.turn_speed * time.dt
        elif action == 3: self.seeker.rotation_y += self.seeker.turn_speed * time.dt
        elif action == 4: # 开火
            reward -= 0.1 # 开火成本
            self.ammo -= 1
            hit_info = raycast(self.seeker.world_position + Vec3(0,1,0), self.seeker.forward, distance=10, ignore=[self.seeker,])
            if hit_info.entity and isinstance(hit_info.entity, Prop):
                hit_info.entity.checked_by_ai = True
                if hit_info.entity.get_shot():
                    reward += 10 # 找到躲藏者的大奖励
                    self.hiders_found += 1
                else:
                    reward -= 1 # 射错的惩罚

        # 更新游戏世界 (非常重要)
        self.app.step()

        # 检查结束条件
        if self.hiders_found == NUM_HIDERS or self.ammo <= 0 or self.step_count >= self.max_steps:
            self.game_over = True
            if self.hiders_found == NUM_HIDERS:
                reward += 100 # 获胜的终极大奖

        return self._get_observation(), reward, self.game_over, {}

class SeekerAI(Entity):
    def __init__(self, **kwargs):
        super().__init__(model='cube', scale=(1, 2, 1), color=color.red, **kwargs)
        self.speed = 250 # 速度需要调整，因为time.dt在非实时模式下很小
        self.turn_speed = 3600