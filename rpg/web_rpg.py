import random

CLASSES = {
    "Crusader": {"max_hp": 40, "atk": 6, "def": 3},
    "Rogue": {"max_hp": 30, "atk": 8, "def": 2},
    "Barbarian": {"max_hp": 45, "atk": 7, "def": 2},
}

ENEMIES = [
    {"name": "Goblin", "max_hp": 20, "atk": 4, "def": 1},
    {"name": "Orc", "max_hp": 30, "atk": 6, "def": 2},
    {"name": "Vampire", "max_hp": 26, "atk": 7, "def": 2},
    {"name": "Skeleton", "max_hp": 22, "atk": 5, "def": 2},
]

def health_bar(hp: int, max_hp: int, width: int = 16) -> str:
    hp = max(0, min(hp, max_hp))
    filled = int((hp / max_hp) * width) if max_hp else 0
    return f"[{'█'*filled}{'░'*(width-filled)}] {hp}/{max_hp}"

def new_player(name: str, job: str) -> dict:
    job = job if job in CLASSES else "Crusader"
    base = CLASSES[job]
    return {
        "name": name or "Hero",
        "job": job,
        "max_hp": base["max_hp"],
        "hp": base["max_hp"],
        "atk": base["atk"],
        "def": base["def"],
        "gold": 0,
        "log": [f"Narrator: {name or 'Hero'} the {job} steps into the Ashen Road..."],
    }

def spawn_enemy() -> dict:
    e = random.choice(ENEMIES).copy()
    return {"name": e["name"], "max_hp": e["max_hp"], "hp": e["max_hp"], "atk": e["atk"], "def": e["def"]}

def roll_damage(attacker_atk: int, defender_def: int) -> int:
    # simple RPG damage: (atk - def) + small roll, min 1
    base = max(1, attacker_atk - defender_def)
    return base + random.randint(0, 3)

def fight_turn(player: dict, enemy: dict) -> str:
    # player attacks
    pdmg = roll_damage(player["atk"], enemy["def"])
    enemy["hp"] -= pdmg
    player["log"].append(f"You hit the {enemy['name']} for {pdmg}.")
    if enemy["hp"] <= 0:
        player["log"].append(f"The {enemy['name']} falls! You win this battle.")
        player["gold"] += 5
        player["log"].append("You gained 5 gold.")
        return "enemy_dead"

    # enemy attacks
    edmg = roll_damage(enemy["atk"], player["def"])
    player["hp"] -= edmg
    player["log"].append(f"The {enemy['name']} hits you for {edmg}.")
    if player["hp"] <= 0:
        player["log"].append("You collapse... defeated.")
        return "player_dead"

    return "continue"
