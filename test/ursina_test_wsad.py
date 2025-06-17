from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

# 创建一个最简单的Ursina应用
app = Ursina()

# 只有一个地面
ground = Entity(model='plane', scale=30, color=color.green, texture='white_cube', collider='box')

# 只有一个玩家控制器
player = FirstPersonController()

# 打印提示
print("--- Minimal Test Running ---")
print("You should be able to move with WASD and look with the mouse.")
print("If this doesn't work, the issue is with your Python/Ursina environment.")

# 运行应用
app.run()