import random
import time
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
# 1. 导入光照
from ursina.lights import DirectionalLight

# --- 游戏设置 (与之前相同) ---
STARTING_AMMO = 8
GAME_TIME_SECONDS = 90
NUM_HIDERS = 5

# --- 道具与关卡定义 (已更新) ---
PROP_TYPES = {
    'desk': {'model': 'cube', 'scale': (4, 1, 2), 'color': color.brown},
    'chair': {'model': 'cube', 'scale': (1, 2, 1), 'color': color.black},
    # 4. 更新盆栽，让它由圆柱体组成
    'plant_pot': {'model': 'cylinder', 'scale': (1.5, 0.8, 1.5), 'color': color.orange},
    'plant_leaves': {'model': 'cylinder', 'scale': (1.2, 2.5, 1.2), 'color': color.green},
    'monitor': {'model': 'cube', 'scale': (1.5, 1, 0.2), 'color': color.dark_gray},
    # 3. 新增隔断墙
    'partition': {'model': 'cube', 'scale': (0.2, 4, 8), 'color': color.rgba(200, 200, 200, 200)},
}

# 3. 全新设计的“办公室”布局
LEVEL_LAYOUT = [
    # 办公区1 (左侧)
    ('desk', (-12, 0, 10)), ('monitor', (-12, 0.5, 10)), ('chair', (-12, 0, 8)),
    ('desk', (-12, 0, 0)), ('monitor', (-12, 0.5, 0)), ('chair', (-12, 0, -2)),
    ('desk', (-12, 0, -10)), ('monitor', (-12, 0.5, -10)), ('chair', (-12, 0, -12)),
    ('partition', (-8, 0, 5)), # 隔断

    # 办公区2 (右侧)
    ('desk', (12, 0, 10)), ('monitor', (12, 0.5, 10)), ('chair', (12, 0, 8)),
    ('desk', (12, 0, 0)), ('monitor', (12, 0.5, 0)), ('chair', (12, 0, -2)),
    ('desk', (12, 0, -10)), ('monitor', (12, 0.5, -10)), ('chair', (12, 0, -12)),
    ('partition', (8, 0, 5)), # 隔断
    
    # 中央装饰区
    ('plant_pot', (0, 0, 0)),
    ('plant_pot', (0, 0, 5)),
]

# --- 道具类 (与之前相同) ---
class Prop(Entity):
    def __init__(self, **kwargs):
        super().__init__(collider='box', **kwargs)
        self.is_hider = False
        self.shot = False

    def get_shot(self):
        if self.shot: return False
        if self.is_hider:
            print("DEBUG: Hit a hider!")
            self.color = color.red
            self.shot = True
            return True
        return False

# --- 主程序开始 ---
app = Ursina(borderless=False)

# --- 世界创建 (已更新) ---
# 1. 给地面和墙壁添加纹理
ground = Entity(model='plane', scale=(40, 1, 40), color=color.white, texture='brick', texture_scale=(5,5), collider='box')
wall_1 = Entity(model='cube', scale=(41, 10, 1), position=(-20, 5, 0), texture='brick', texture_scale=(10,5))
wall_2 = Entity(model='cube', scale=(41, 10, 1), position=(20, 5, 0), texture='brick', texture_scale=(10,5))
wall_3 = Entity(model='cube', scale=(1, 10, 41), position=(0, 5, 20), texture='brick', texture_scale=(10,5))
wall_4 = Entity(model='cube', scale=(1, 10, 41), position=(0, 5, -20), texture='brick', texture_scale=(10,5))

# 5. 添加天空背景
sky = Sky()

# 2. 添加定向光和阴影
light = DirectionalLight(y=10, z=5, shadows=True, rotation=(30, -45, 0))

# --- 道具和躲藏者创建 ---
all_entities = [ground, wall_1, wall_2, wall_3, wall_4]
hider_choices = random.sample(LEVEL_LAYOUT, NUM_HIDERS)

for prop_type, pos in LEVEL_LAYOUT:
    prop_info = PROP_TYPES[prop_type]
    
    # 4. 特殊处理复合道具“盆栽”
    if prop_type == 'plant_pot':
        pot = Prop(model=prop_info['model'], scale=prop_info['scale'], color=prop_info['color'], position=pos)
        leaves_info = PROP_TYPES['plant_leaves']
        leaves = Prop(model=leaves_info['model'], scale=leaves_info['scale'], color=leaves_info['color'], position=pos+(0, prop_info['scale'][1], 0))
        # 决定盆栽是否是躲藏者 (锅和叶子算一体)
        is_hider = (prop_type, pos) in hider_choices
        pot.is_hider = is_hider
        leaves.is_hider = is_hider
        all_entities.extend([pot, leaves])
    else:
        # 普通道具
        entity = Prop(model=prop_info['model'], scale=prop_info['scale'], color=prop_info['color'], position=pos)
        if prop_type == 'monitor': entity.y += 0.5
        entity.is_hider = (prop_type, pos) in hider_choices
        all_entities.append(entity)

# 2. 为所有实体启用阴影
for e in all_entities:
    e.shadow_caster = True
    e.shadow_receiver = True

# --- 玩家创建 ---
player = FirstPersonController(position=(0, 2, -15), origin_y=-0.5)
player.shadow_caster = True # 玩家自己也产生阴影

# --- 游戏状态和UI (与之前相同) ---
game_state = {'ammo': STARTING_AMMO, 'hiders_found': 0, 'game_over': False, 'winner': None}
ammo_text = Text(f"Ammo: {game_state['ammo']}", origin=(-0.5, -0.5), position=(-0.8, -0.4), scale=2)
# ... (其他UI代码与上一版相同，为简洁省略，请直接复制使用) ...
time_text = Text("Time: ", origin=(-0.5, -0.5), position=(-0.8, -0.35), scale=2)
hiders_text = Text(f"Hiders Found: 0 / {NUM_HIDERS}", origin=(-0.5, -0.5), position=(-0.8, -0.3), scale=2)
crosshair = Text('+', scale=3, origin=(0,0), color=color.white)
start_time = time.time()

def update():
    # ... (update函数逻辑与上一版相同，为简洁省略，请直接复制使用) ...
    if game_state['game_over']: return
    ammo_text.text = f"Ammo: {game_state['ammo']}"
    hiders_text.text = f"Hiders Found: {game_state['hiders_found']} / {NUM_HIDERS}"
    time_left = GAME_TIME_SECONDS - (time.time() - start_time)
    if time_left < 0:
        time_left = 0
        game_state['game_over'] = True
        game_state['winner'] = "Hiders" if game_state['hiders_found'] < NUM_HIDERS else "Seeker"
    time_text.text = f"Time: {int(time_left)}"
    if game_state['hiders_found'] == NUM_HIDERS:
        game_state['game_over'] = True
        game_state['winner'] = "Seeker"
    elif game_state['ammo'] == 0 and game_state['hiders_found'] < NUM_HIDERS:
        game_state['game_over'] = True
        game_state['winner'] = "Hiders"
    if game_state['game_over']:
        Text(f"{game_state['winner']} Win!", scale=5, origin=(0,0), y=0.2, color=color.yellow)
        player.disable()

def input(key):
    # ... (input函数逻辑与上一版相同，为简洁省略，请直接复制使用) ...
    if game_state['game_over']:
        if key == 'q': application.quit()
        return
            
    if key == 'left mouse down':
        if game_state['ammo'] > 0:
            game_state['ammo'] -= 1
            if mouse.hovered_entity and isinstance(mouse.hovered_entity, Prop):
                if mouse.hovered_entity.get_shot():
                    game_state['hiders_found'] += 1

# 运行
app.run()