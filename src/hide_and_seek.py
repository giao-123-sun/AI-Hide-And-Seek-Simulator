import pygame
import random
import sys

# --- 游戏设置 (Game Settings) ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
MAP_WIDTH = 1600  # 地图宽度，大于屏幕
MAP_HEIGHT = 1200 # 地图高度，大于屏幕
FPS = 60

# 颜色定义 (Colors)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
STEEL_BLUE = (70, 130, 180) # 办公桌颜色
SADDLE_BROWN = (139, 69, 19) # 椅子颜色
DARK_GREEN = (0, 100, 0)     # 盆栽颜色

# 搜捕者设置 (Seeker Settings)
SEEKER_SPEED = 5
STARTING_AMMO = 8 # 子弹稍微多一点，因为地图大了
SEEKER_COLOR = RED

# 躲藏者/道具设置 (Hider/Prop Settings)
# 定义了不同类型的道具
PROP_TYPES = {
    "desk": {"color": STEEL_BLUE, "size": (150, 60)},
    "chair": {"color": SADDLE_BROWN, "size": (40, 40)},
    "plant": {"color": DARK_GREEN, "size": (50, 70)},
}
NUM_HIDERS = 3

# 预设的关卡布局: (类型, (x坐标, y坐标))
LEVEL_LAYOUT = [
    # 周围的墙壁/边界
    ("desk", (0, 0)), ("desk", (150, 0)), ("desk", (300, 0)), ("desk", (450, 0)), ("desk", (600, 0)),
    ("desk", (750, 0)),("desk", (900, 0)),("desk", (1050, 0)),("desk", (1200, 0)), ("desk", (1350, 0)),
    ("desk", (0, 1140)), ("desk", (150, 1140)), ("desk", (300, 1140)), ("desk", (450, 1140)), ("desk", (600, 1140)),
    ("desk", (750, 1140)),("desk", (900, 1140)),("desk", (1050, 1140)),("desk", (1200, 1140)), ("desk", (1350, 1140)),
    # 内部的办公区
    ("desk", (200, 200)), ("chair", (250, 270)),
    ("desk", (200, 400)), ("chair", (250, 350)), ("plant", (140, 380)),
    ("desk", (600, 300)), ("chair", (600, 250)),
    ("desk", (600, 500)), ("chair", (600, 570)),
    ("desk", (1000, 200)), ("chair", (950, 220)),
    ("desk", (1000, 600)), ("chair", (1050, 550)), ("plant", (1150, 620)),
    ("desk", (1200, 800)), ("chair", (1250, 870)),
    ("plant", (50, 800)), ("plant", (1400, 100)),
]

# 游戏时间 (Game Timer)
GAME_TIME_SECONDS = 60

# --- 游戏对象类 (Game Object Classes) ---

class Seeker(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([30, 40])
        self.image.fill(SEEKER_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = x # 这是在整个地图上的坐标 (世界坐标)
        self.rect.y = y

    def update(self):
        keystate = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keystate[pygame.K_a]: dx = -SEEKER_SPEED
        if keystate[pygame.K_d]: dx = SEEKER_SPEED
        if keystate[pygame.K_w]: dy = -SEEKER_SPEED
        if keystate[pygame.K_s]: dy = SEEKER_SPEED
        
        # 移动并检查是否超出地图边界
        if 0 < self.rect.x + dx < MAP_WIDTH - self.rect.width:
            self.rect.x += dx
        if 0 < self.rect.y + dy < MAP_HEIGHT - self.rect.height:
            self.rect.y += dy

class Prop(pygame.sprite.Sprite):
    def __init__(self, prop_type, pos, is_hider=False):
        super().__init__()
        prop_info = PROP_TYPES[prop_type]
        self.image = pygame.Surface(prop_info["size"])
        self.image.fill(prop_info["color"])
        self.rect = self.image.get_rect()
        self.rect.topleft = pos # 世界坐标
        self.is_hider = is_hider

class HitMarker(pygame.sprite.Sprite):
    def __init__(self, world_pos):
        super().__init__()
        self.image = pygame.Surface([10, 10])
        pygame.draw.circle(self.image, BLACK, (5, 5), 5)
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect(center=world_pos) # 世界坐标
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time > 500:
            self.kill()

# --- 辅助函数 (Helper Functions) ---

def draw_text(surface, text, size, x, y, color):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)

def create_camera(seeker_rect):
    """计算镜头偏移量"""
    x = -seeker_rect.centerx + SCREEN_WIDTH / 2
    y = -seeker_rect.centery + SCREEN_HEIGHT / 2
    # 限制镜头不超出地图边界
    x = min(0, x) # 不向右滚动超过地图左边界
    y = min(0, y) # 不向下滚动超过地图上边界
    x = max(-(MAP_WIDTH - SCREEN_WIDTH), x) # 不向左滚动超过地图右边界
    y = max(-(MAP_HEIGHT - SCREEN_HEIGHT), y) # 不向上滚动超过地图下边界
    return pygame.Rect(x, y, MAP_WIDTH, MAP_HEIGHT)

def draw_minimap(surface, seeker, props):
    """绘制小地图"""
    # 小地图的尺寸和位置
    minimap_w, minimap_h = 200, 150
    minimap_x, minimap_y = SCREEN_WIDTH - minimap_w - 10, 10
    
    # 比例尺
    scale_x = minimap_w / MAP_WIDTH
    scale_y = minimap_h / MAP_HEIGHT

    # 绘制背景
    minimap_surface = pygame.Surface((minimap_w, minimap_h))
    minimap_surface.fill(GRAY)
    minimap_surface.set_alpha(180) # 半透明

    # 绘制所有道具的缩略图
    for prop in props:
        mini_prop_x = int(prop.rect.x * scale_x)
        mini_prop_y = int(prop.rect.y * scale_y)
        mini_prop_w = int(prop.rect.width * scale_x) + 1
        mini_prop_h = int(prop.rect.height * scale_y) + 1
        pygame.draw.rect(minimap_surface, prop.image.get_at((0,0)), (mini_prop_x, mini_prop_y, mini_prop_w, mini_prop_h))

    # 绘制搜捕者位置
    seeker_mini_x = int(seeker.rect.centerx * scale_x)
    seeker_mini_y = int(seeker.rect.centery * scale_y)
    pygame.draw.circle(minimap_surface, RED, (seeker_mini_x, seeker_mini_y), 3)

    # 将小地图画到主屏幕上
    surface.blit(minimap_surface, (minimap_x, minimap_y))

def show_game_over_screen(winner):
    # ... (此函数与之前版本相同，此处省略以节省空间) ...
    # ... (The game over screen function is the same as the previous version) ...
    # (Copy the `show_game_over_screen` function from the previous code block here)
    screen.fill(GRAY)
    if winner == "Hiders":
        font = pygame.font.Font(None, 74)
        text = font.render("Hiders Win!", True, DARK_GREEN)
        screen.blit(text, (SCREEN_WIDTH/2 - text.get_width()/2, SCREEN_HEIGHT/4))
    else:
        font = pygame.font.Font(None, 74)
        text = font.render("Seeker Wins!", True, RED)
        screen.blit(text, (SCREEN_WIDTH/2 - text.get_width()/2, SCREEN_HEIGHT/4))
    
    font = pygame.font.Font(None, 30)
    text = font.render("Press 'R' to Play Again or 'Q' to Quit", True, WHITE)
    screen.blit(text, (SCREEN_WIDTH/2 - text.get_width()/2, SCREEN_HEIGHT/2))
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_r:
                    waiting = False
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()


# --- 主游戏循环 (Main Game Loop) ---

# --- 主游戏循环 (Main Game Loop) ---

def game_loop():
    # 初始化精灵组
    all_sprites = pygame.sprite.Group()
    props_group = pygame.sprite.Group()
    hiders_group = pygame.sprite.Group()

    # 从布局中选择一些道具作为躲藏者
    hider_choices = random.sample(LEVEL_LAYOUT, NUM_HIDERS)
    
    # 创建所有道具
    for prop_type, pos in LEVEL_LAYOUT:
        is_hider = (prop_type, pos) in hider_choices
        prop = Prop(prop_type, pos, is_hider=is_hider)
        props_group.add(prop)
        all_sprites.add(prop)
        if is_hider:
            hiders_group.add(prop)
    
    # 创建搜捕者
    seeker = Seeker(MAP_WIDTH / 2, MAP_HEIGHT / 2)
    all_sprites.add(seeker)

    # 游戏变量
    ammo = STARTING_AMMO
    hiders_found = 0
    start_time = pygame.time.get_ticks()
    game_over = False
    winner = None # 初始化winner变量

    # ↓↓↓ --- 代码修正之处 --- ↓↓↓
    # 在循环开始前，先对camera进行一次初始化
    camera = create_camera(seeker.rect)
    # ↑↑↑ -------------------- ↑↑↑

    running = True
    while running:
        # 1. 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and ammo > 0 and not game_over:
                ammo -= 1
                # 将屏幕坐标转换为世界坐标
                screen_pos = pygame.mouse.get_pos()
                world_pos_x = screen_pos[0] - camera.x
                world_pos_y = screen_pos[1] - camera.y
                
                all_sprites.add(HitMarker((world_pos_x, world_pos_y)))

                # 检查是否击中
                for hider in hiders_group:
                    if hider.rect.collidepoint(world_pos_x, world_pos_y):
                        hider.kill() # 从所有组中移除
                        hiders_group.remove(hider)
                        hiders_found += 1
                        print("Hit a hider!")
                        break # 一次射击最多击中一个

        # 2. 逻辑更新
        if not game_over:
            all_sprites.update()
            # 在每一帧都更新镜头位置
            camera = create_camera(seeker.rect)

            # 检查胜利/失败条件
            time_left = GAME_TIME_SECONDS - (pygame.time.get_ticks() - start_time) / 1000
            if hiders_found == NUM_HIDERS:
                game_over = True
                winner = "Seeker"
            elif time_left <= 0 or ammo <= 0:
                if hiders_found < NUM_HIDERS:
                    game_over = True
                    winner = "Hiders"
                else: # 恰好在最后一秒或最后一发子弹找到所有人
                    game_over = True
                    winner = "Seeker"


        # 3. 绘制
        screen.fill(WHITE) # 背景

        # 绘制所有在镜头内的精灵
        for sprite in props_group:
            screen.blit(sprite.image, sprite.rect.move(camera.topleft))
        screen.blit(seeker.image, seeker.rect.move(camera.topleft))
        for sprite in all_sprites:
             if isinstance(sprite, HitMarker):
                 screen.blit(sprite.image, sprite.rect.move(camera.topleft))

        # 绘制UI
        draw_text(screen, f"Ammo: {ammo}", 30, 10, 10, BLACK)
        draw_text(screen, f"Time: {int(time_left) if time_left > 0 else 0}", 30, 10, 40, BLACK)
        draw_text(screen, f"Hiders Found: {hiders_found} / {NUM_HIDERS}", 30, 10, 70, BLACK)
        
        # 绘制小地图
        draw_minimap(screen, seeker, props_group)

        if game_over:
            # 在显示结束画面之前，最后再绘制一次游戏状态
            pygame.display.flip() 
            pygame.time.wait(1000) # 短暂等待，让玩家看到最后一击
            show_game_over_screen(winner)
            game_loop() # 重新开始游戏

        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()
# --- 主程序入口 ---
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Advanced 2D Hide and Seek")
    clock = pygame.time.Clock()
    game_loop()