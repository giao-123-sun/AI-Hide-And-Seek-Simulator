# AI Hide & Seek Simulator - Developer Documentation (v0.2)

## 1. Project Overview

* **Project Name:** AI Hide & Seek Simulator
* **Core Goal:** To create a simulation environment where AI agents can learn and execute complex spatial strategies of "hiding" (as props) and "seeking" (as hunters).
* **Current Stage:** The project is in its initial phase (v0.2), featuring a playable 3D game framework where a human player acts as the Seeker against stationary Hider props.

## 2. Core Technologies

* **Programming Language:** Python 3
* **Game Engine:** Ursina (A high-level engine built on top of Panda3D)
* **Key Dependencies:** `ursina`

## 3. Code Architecture

The entire game logic is currently contained within a single Python script. The architecture can be broken down as follows:

### 3.1. Configuration Constants

Global variables at the top of the script control the game's balance and design.
* `STARTING_AMMO`, `GAME_TIME_SECONDS`, `NUM_HIDERS`: Control game difficulty and duration.
* `PROP_TYPES`: A dictionary defining the visual properties (model, scale, color) of each type of prop. To add a new prop type, simply add an entry here.
* `LEVEL_LAYOUT`: A list of tuples `(prop_type, position)` that dictates the static layout of the level. The level is built by iterating through this list.

### 3.2. Key Classes

* **`Prop(Entity)`**: The most important custom class. It inherits from Ursina's `Entity`.
    * **Attributes:**
        * `is_hider (bool)`: Determines if this prop is a target.
        * `shot (bool)`: A flag to prevent a Hider from being counted multiple times.
    * **Methods:**
        * `get_shot()`: Handles the logic when the prop is shot by the player.

### 3.3. Core Functions & Game Loop

* **`update()`**: This function is assigned to `app.update` and acts as the main game loop, executed every frame. It's responsible for:
    * Updating UI elements (timer, ammo count).
    * Checking for win/loss conditions.
    * Handling the game-over state transition.
* **`input(key)`**: This function is assigned to `app.input` and handles all discrete user inputs. It's responsible for:
    * Processing shooting mechanics (`left mouse down`).
    * Handling screenshot logic (`f2`).
    * Quitting the game (`q`).

### 3.4. Key Systems (Handled by Ursina)

* **Player Control:** Handled entirely by the `ursina.prefabs.first_person_controller.FirstPersonController` prefab. It automatically manages WASD movement, mouse look, gravity, and collisions.
* **Rendering & Scene Graph:** Ursina manages the scene. We simply add `Entity` objects to it.
* **Lighting & Shadows:** A `DirectionalLight` entity provides global lighting. Individual entities must have `.shadow_caster = True` and `.shadow_receiver = True` to participate in the shadow system.
* **Interaction:** The "shooting" mechanic relies on `mouse.hovered_entity`, which is a powerful Ursina feature that returns the entity currently under the mouse cursor.

## 4. Future Development Roadmap

### Phase 1: Core Gameplay Refinement
* [ ] **Multiple Levels:** Create a system to load different `LEVEL_LAYOUT` configurations.
* [ ] **Playable Hiders:** Implement a game mode where human players can control a prop and choose a hiding spot during a "preparation phase".
* [ ] **Improved UI/UX:** Add a main menu, pause menu, and more polished in-game UI.
* [ ] **Asset Improvement:** Replace primitive models (`cube`, `cylinder`) with custom 3D models (e.g., `.obj` files).

### Phase 2: AI Implementation (The Core Vision)
* [ ] **AI Hider Agent:**
    * **Goal:** Develop an AI that can analyze the `LEVEL_LAYOUT` and choose an optimal hiding spot.
    * **Metrics for "Good Spot":** Low visibility, good occlusion, conforms to environmental patterns (e.g., a chair is usually near a desk).
* [ ] **AI Seeker Agent:**
    * **Goal:** Develop an AI to replace the human player as the Seeker.
    * **Initial Approach:** Implement pathfinding (e.g., A* algorithm) to navigate the map.
    * **Advanced Approach:** Develop search strategies. Instead of random searching, the AI should prioritize areas with high prop density, check common hiding spots, and have a memory of cleared areas.

### Phase 3: Polishing & Distribution
* [ ] **Sound Design:** Add background music, footstep sounds, and more varied interaction sounds.
* [ ] **Packaging:** Use tools like `PyInstaller` to package the game into a standalone executable file for easy distribution.