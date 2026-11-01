import pygame
from opensimplex import OpenSimplex
import random
import math

pygame.init()


# ==================================================
# 화면
# ==================================================

WIDTH = 1200
HEIGHT = 700

INFO_WIDTH = 400
MAP_WIDTH = WIDTH - INFO_WIDTH

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("세계 시뮬레이션 - 4단계: 문명·국가 발전 v8")

clock = pygame.time.Clock()


# ==================================================
# 세계 크기
# ==================================================

WORLD_WIDTH = 200
WORLD_HEIGHT = 200

BASE_TILE_SIZE = 12

BLOCK_SIZE = 15   # 재해 확률을 굴릴 때 쓰는 지역(region) 단위


# ==================================================
# 지형 색깔 / 이름
# ==================================================

TERRAIN_COLORS = {

    "water": (48, 105, 205),
    "river": (100, 190, 235),
    "plain": (210, 200, 120),
    "forest": (34, 122, 58),
    "mountain": (150, 150, 150),
    "desert": (225, 195, 130)

}


TERRAIN_NAMES = {

    "water": "바다",
    "river": "강",
    "plain": "평야",
    "forest": "숲",
    "mountain": "산",
    "desert": "사막"

}


# ==================================================
# 지형별 기본 자원량
# ==================================================

TERRAIN_BASE_RESOURCES = {

    "water":    {"food": 30,  "water": 0,   "wood": 0,   "iron": 0,  "minerals": 0,  "oil": 15},
    "plain":    {"food": 90,  "water": 50,  "wood": 15,  "iron": 5,  "minerals": 5,  "oil": 5},
    "forest":   {"food": 40,  "water": 40,  "wood": 100, "iron": 10, "minerals": 10, "oil": 5},
    "mountain": {"food": 10,  "water": 20,  "wood": 10,  "iron": 80, "minerals": 70, "oil": 10},
    "desert":   {"food": 5,   "water": 5,   "wood": 0,   "iron": 15, "minerals": 25, "oil": 40},
    "river":    {"food": 120, "water": 150, "wood": 30,  "iron": 5,  "minerals": 5,  "oil": 5},
    "coast":    {"food": 70,  "water": 80,  "wood": 10,  "iron": 5,  "minerals": 5,  "oil": 20}

}


IRON_GRADES = [
    (500, 2000, 0.35),
    (2000, 5000, 0.30),
    (5000, 10000, 0.20),
    (10000, 20000, 0.10),
    (20000, 50000, 0.05)
]

MINERAL_GRADES = [
    (1000, 10000, 0.80),
    (10000, 30000, 0.17),
    (30000, 60000, 0.03)
]

OIL_GRADES = [
    (5000, 50000, 0.80),
    (50000, 150000, 0.20)
]

IRON_ZONE_COUNT = (30, 70)
MINERAL_ZONE_COUNT = (20, 50)
OIL_ZONE_COUNT = (10, 30)


OVERLAY_COLORS = {

    "food": (70, 200, 70),
    "water": (60, 150, 235),
    "wood": (150, 100, 40),
    "iron": (210, 130, 50),
    "minerals": (190, 90, 230),
    "oil": (40, 40, 40)

}

OVERLAY_NAMES = {

    "food": "식량",
    "water": "물",
    "wood": "목재",
    "iron": "철",
    "minerals": "광물",
    "oil": "석유",
    "territory": "영토"

}

OVERLAY_KEYS = {
    pygame.K_1: "food",
    pygame.K_2: "water",
    pygame.K_3: "wood",
    pygame.K_4: "iron",
    pygame.K_5: "minerals",
    pygame.K_6: "oil",
    pygame.K_7: "territory"
}


# ==================================================
# 자연재해 정의 (전염병은 인구 시스템이 생기기 전까지 보류)
# ==================================================

DISASTER_DEFS = {

    "flood": {
        "name": "홍수", "color": (70, 130, 230),
        "radius": (3, 8), "large_radius": (8, 15), "large_chance": 0.15,
        "duration": (1, 3), "large_duration": (3, 5),
        "effects": {"food": (-0.5, -0.2), "wood": (-0.15, -0.05)},
        "population": (-0.20, -0.05),
        "after_effect": {"food": (0.05, 0.15)}, "after_duration": (1, 2)
    },

    "drought": {
        "name": "가뭄", "color": (200, 150, 60),
        "radius": (5, 10), "large_radius": (10, 20), "large_chance": 0.2,
        "duration": (2, 5), "large_duration": (5, 10),
        "effects": {"water": (-0.7, -0.3), "food": (-0.7, -0.2), "wood": (-0.4, -0.1)},
        "growth_penalty": (-1.0, -0.3)
    },

    "volcano": {
        "name": "화산 폭발", "color": (210, 60, 40),
        "radius": (3, 6), "large_radius": (10, 20), "large_chance": 0.4,
        "duration": (1, 2), "large_duration": (2, 5),
        "effects": {"food": (-0.8, -0.3), "wood": (-0.6, -0.2)},
        "population": (-0.50, -0.10),
        "after_effect": {"food": (0.10, 0.30)}, "after_duration": (2, 4)
    },

    "earthquake": {
        "name": "지진", "color": (150, 110, 60),
        "radius": (5, 10), "large_radius": (10, 20), "large_chance": 0.2,
        "duration": (1, 5), "large_duration": (1, 5),
        "effects": {"mining": (-0.5, -0.1)},
        "population": (-0.30, -0.05)
    },

    "storm": {
        "name": "폭풍", "color": (90, 90, 200),
        "radius": (5, 12), "large_radius": (12, 25), "large_chance": 0.15,
        "duration": (1, 2), "large_duration": (1, 2),
        "effects": {"food": (-0.4, -0.1), "wood": (-0.3, -0.1)},
        "population": (-0.15, -0.03)
    },

    "fire": {
        "name": "산불", "color": (230, 90, 30),
        "radius": (2, 4), "large_radius": (5, 15), "large_chance": 0.3,
        "duration": (1, 3), "large_duration": (1, 3),
        "effects": {"wood": (-0.4, -0.1), "food": (-0.4, -0.1)},
        "population": (-0.15, -0.02),
        "density_damage": (20, 80)
    }

}

DISASTER_TYPES = list(DISASTER_DEFS.keys())

# ==================================================
# 문명 / 국가 / 영토 / 외교 시스템
# ==================================================
CIV_COUNT = 8
CIV_NAMES = ["아르카", "벨론", "카르마", "델타", "엘리온", "프레아", "가이아", "하르트"]
CIV_COLORS = [
    (220, 70, 70), (70, 115, 230), (65, 175, 95), (205, 135, 45),
    (155, 85, 205), (45, 175, 185), (225, 175, 55), (125, 125, 135)
]
civilizations = []
territory_owner = [-1] * (WORLD_WIDTH * WORLD_HEIGHT)
diplomacy = {}
active_wars = []
active_epidemics = []

# ===== 성능/안정성 설정 =====
CLIMATE_UPDATE_INTERVAL = 20
RISK_REBUILD_INTERVAL = 100
MAX_EVENT_HISTORY = 2500
AUTO_YEARS_PER_TICK = 20
disaster_risk_pools = {}
disaster_event_serial = 0

# ===== 문명 속도 조절 =====
# 의료는 2000년 전후에 100에 가까워지도록 역사적 상한을 둔다.
MEDICAL_TARGET_YEAR = 2000
DIPLOMACY_INTERVAL = 2
TERRITORY_EXPANSION_INTERVAL = 1
ENV_CACHE_INTERVAL = 3
# 영토-인구 비례 조절. 한 칸당 적정 인구가 지나치게 넓게 흔들리지 않게 한다.
BASE_PEOPLE_PER_TILE = 245.0
TERRITORY_TARGET_FILL = 0.78       # 적정 영토에서 수용력의 약 78% 정도를 목표로 함
TERRITORY_MAX_EXPAND_PER_YEAR = 12 # 영토 부족 시 한 해 최대 12칸까지, 단 항상 기존 국경에 연결해서 확장
TERRITORY_SHRINK_START = 1.65     # 적정 영토의 1.65배보다 넓고 인구가 적으면 변두리 일부 포기
NEARBY_COLONY_MAX_GAP = 6         # 섬 확장은 기존 영토에서 최대 6칸 이내의 가까운 해안만 허용
NEARBY_COLONY_INTERVAL = 25       # 원거리 점프가 아니라 드문 근거리 해안 정착만 허용
EXTINCTION_POPULATION = 300  # 이 인구 이하로 떨어지면 즉시 완전 멸망

# ===== 전쟁 빈도 / 거리 / 시대 제한 =====
WAR_START_YEAR = 450          # 영토가 어느 정도 자리 잡은 뒤인 450년부터 전쟁 가능
WAR_CHECK_INTERVAL = 4        # 전쟁 후보는 4년에 한 번 검사해 지나치게 연속 발생하지 않게 함
GLOBAL_WAR_GAP_MIN = 32       # 세계 전체 새 전쟁 최소 간격
GLOBAL_WAR_GAP_MAX = 52
WAR_MIN_DURATION = 5          # 전쟁은 최소 5년
WAR_MAX_DURATION = 20         # 최대 20년
WAR_TRUCE_MIN = 22            # 종전 후 같은 상대와 바로 재전쟁 방지
WAR_TRUCE_MAX = 40
next_global_war_year = WAR_START_YEAR

_NEIGHBORS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def civ_alive(civ):
    return civ.get("alive", True) and civ["population"] > EXTINCTION_POPULATION


def pair_key(a, b):
    return (min(a["id"], b["id"]), max(a["id"], b["id"]))


def get_diplomacy(a, b):
    key = pair_key(a, b)
    if key not in diplomacy:
        diplomacy[key] = {
            "relation": random.uniform(-18, 12),
            "last_trade_year": -999999,
            "truce_until": -1,
        }
    return diplomacy[key]


def relation_label(value):
    if value <= -60:
        return "적대"
    if value <= -20:
        return "긴장"
    if value < 20:
        return "중립"
    if value < 60:
        return "우호"
    return "동맹"


def change_relation(a, b, delta):
    d = get_diplomacy(a, b)
    d["relation"] = clamp(d["relation"] + delta, -100, 100)


def wealth_level(civ):
    # 총재산을 그대로 쓰면 인구가 큰 나라가 무조건 100이 되므로 1인당 재산을 로그 스케일로 정규화.
    per_capita = civ["wealth"] / max(civ["population"], 1)
    return clamp(24.0 * math.log10(1.0 + max(per_capita, 0.0)), 0, 100)


def development_level(civ):
    # 사용자가 정한 5개 핵심 스탯만 저장하고, 기술력/발달도는 파생값으로 계산.
    return clamp(
        civ["intelligence"] * 0.40
        + civ["medical"] * 0.20
        + wealth_level(civ) * 0.40,
        0, 100
    )


def civilization_stage(civ):
    """(단계번호, 단계명) - 발달도와 인구를 둘 다 만족해야 상위 단계로 진입."""
    if not civ_alive(civ):
        return -1, "멸망"
    pop = civ["population"]
    dev = development_level(civ)
    if dev >= 85 and pop >= 50_000:
        return 5, "고도 문명"
    if dev >= 70 and pop >= 20_000:
        return 4, "발전국"
    if dev >= 50 and pop >= 10_000:
        return 3, "문명국"
    if dev >= 35 and pop >= 3_000:
        return 2, "초기 국가"
    if dev >= 20 and pop >= 1_000:
        return 1, "정착 부족"
    return 0, "원시 부족"


def trade_range(civ):
    stage, _ = civilization_stage(civ)
    if stage < 2:
        return 0
    if stage == 2:
        return 18
    if stage == 3:
        return 45
    if stage == 4:
        return 90
    return 200


def can_trade(civ):
    return (
        civ_alive(civ)
        and civ["population"] >= 3_000
        and civ["intelligence"] >= 35
        and civ["wealth"] >= 5_000
        and development_level(civ) >= 35
    )


def can_diplomacy(civ):
    return (
        civ_alive(civ)
        and civ["population"] >= 3_000
        and civ["intelligence"] >= 35
        and development_level(civ) >= 35
    )


def can_start_war(civ):
    # 너무 원시적인 부족의 전쟁은 막되, 초기 국가 정도부터 가능하게 한다.
    return (
        year >= WAR_START_YEAR
        and civ_alive(civ)
        and civ["population"] >= 3_000
        and civ["intelligence"] >= 32
        and civ["wealth"] >= 5_000
        and development_level(civ) >= 32
    )


def war_range(civ):
    """비접경 국가와 싸울 수 있는 최대 '영토 사이 간격'.

    200x200 지도에서 예전 45~80칸은 지나치게 넓었다.
    이제 초중기에는 아주 가까운 나라만, 후기로 가도 지도 반대편과는 싸울 수 없다.
    """
    dev = development_level(civ)
    if year < 800:
        era_cap = 14.0
    elif year < 1300:
        era_cap = 20.0
    else:
        era_cap = 28.0
    return min(era_cap, 8.0 + dev * 0.25)


def territory_gap_estimate(a, b):
    """두 나라의 실제 영토 사이 간격을 빠르게 근사한다.

    영토가 거의 원형/연결형이라는 현재 시뮬레이션 특성을 이용해
    수도 사이 거리에서 각 국가의 '영토 반지름'을 빼 준다.
    접경 여부는 countries_border()가 별도로 정확히 검사한다.
    값이 작을수록 실제 국경끼리 가깝다.
    """
    if countries_border(a, b):
        return 0.0
    center_dist = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
    radius_a = math.sqrt(max(len(a.get("territory", ())), 1) / math.pi)
    radius_b = math.sqrt(max(len(b.get("territory", ())), 1) / math.pi)
    return max(0.0, center_dist - radius_a - radius_b)


def is_large_war_capable(civ):
    return (
        civ["population"] >= 15_000
        and civ["intelligence"] >= 45
        and civ["wealth"] >= 25_000
    )


def find_civilization_at(x, y):
    if 0 <= x < WORLD_WIDTH and 0 <= y < WORLD_HEIGHT:
        owner = territory_owner[y * WORLD_WIDTH + x]
        if 0 <= owner < len(civilizations):
            civ = civilizations[owner]
            if civ_alive(civ):
                return civ
    # 영토 밖에서도 본거지 근처라면 선택 가능
    best = None
    best_dist = 999999
    for civ in civilizations:
        if not civ_alive(civ):
            continue
        d = (x - civ["x"]) ** 2 + (y - civ["y"]) ** 2
        if d < best_dist and d <= 6 * 6:
            best = civ
            best_dist = d
    return best


def get_resource_value_fast(mode, x, y):
    """시뮬레이션 내부 계산용. 화면 표시용 round()를 생략해 대량 계산을 빠르게 한다."""
    idx = y * WORLD_WIDTH + x
    if mode == "food":
        return food_map[y][x] * multiplier_maps["food"].get(idx, 1.0)
    if mode == "water":
        return water_map[y][x] * multiplier_maps["water"].get(idx, 1.0)
    if mode == "wood":
        return wood_map[y][x] * multiplier_maps["wood"].get(idx, 1.0)
    mining_mult = multiplier_maps["mining"].get(idx, 1.0)
    if mode == "iron":
        return iron_map[y][x] * mining_mult
    if mode == "minerals":
        return mineral_map[y][x] * mining_mult
    if mode == "oil":
        return oil_map[y][x] * mining_mult
    return 0.0


def get_civ_environment(civ, max_samples=48):
    cached = civ.get("env_cache")
    cached_year = civ.get("env_cache_year", -999999)
    if cached is not None and year - cached_year < ENV_CACHE_INTERVAL:
        return cached

    sums = {"food": 0.0, "water": 0.0, "wood": 0.0, "iron": 0.0, "minerals": 0.0, "oil": 0.0}
    tiles = civ.get("territory") or set()
    if tiles:
        if len(tiles) > max_samples:
            # set 전체를 매년 다 훑지 않도록 균등 간격 표본을 사용.
            arr = tuple(tiles)
            step = len(arr) / max_samples
            sample = [arr[int(i * step)] for i in range(max_samples)]
        else:
            sample = tiles
        count = 0
        for idx in sample:
            y, x = divmod(idx, WORLD_WIDTH)
            for k in sums:
                sums[k] += get_resource_value_fast(k, x, y)
            count += 1
        if count:
            result = {k: v / count for k, v in sums.items()}
            civ["env_cache"] = result
            civ["env_cache_year"] = year
            return result

    # 영토가 없는 초기/예외 상황에서는 본거지 주변을 사용.
    count = 0
    radius = 4
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy > radius * radius:
                continue
            x, y = civ["x"] + dx, civ["y"] + dy
            if not (0 <= x < WORLD_WIDTH and 0 <= y < WORLD_HEIGHT) or world[y][x] == "water":
                continue
            for k in sums:
                sums[k] += get_resource_value_fast(k, x, y)
            count += 1
    result = {k: (v / count if count else 0.0) for k, v in sums.items()}
    civ["env_cache"] = result
    civ["env_cache_year"] = year
    return result


def choose_civilization_start():
    candidates = []
    weights = []
    for y in range(WORLD_HEIGHT):
        for x in range(WORLD_WIDTH):
            if world[y][x] == "water":
                continue
            key = get_terrain_key(x, y)
            score = {"river": 7.0, "coast": 5.0, "plain": 5.0, "forest": 2.5, "mountain": 0.8, "desert": 0.5}.get(key, 1.0)
            score *= 0.5 + food_map[y][x] / 100 + water_map[y][x] / 150
            candidates.append((x, y))
            weights.append(max(score, 0.1))
    for _ in range(300):
        x, y = random.choices(candidates, weights=weights, k=1)[0]
        if all((x-c["x"])**2 + (y-c["y"])**2 >= 20**2 for c in civilizations):
            return x, y
    return random.choice(candidates)


def _refresh_frontier_for(civ):
    frontier = set()
    for idx in civ["territory"]:
        y, x = divmod(idx, WORLD_WIDTH)
        for dx, dy in _NEIGHBORS4:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT):
                continue
            nidx = ny * WORLD_WIDTH + nx
            if world[ny][nx] != "water" and territory_owner[nidx] == -1:
                frontier.add(nidx)
    civ["frontier"] = frontier


def claim_tile(civ, idx):
    """일반 영토 확장은 반드시 기존 영토와 4방향으로 연결되어야 한다.

    초기 첫 칸만 예외. 이 안전장치 때문에 다른 코드가 실수로 먼 칸을 넘겨도
    지도에 점처럼 갑자기 영토가 생기지 않는다.
    """
    if not civ_alive(civ) or not (0 <= idx < WORLD_WIDTH * WORLD_HEIGHT):
        return False
    y, x = divmod(idx, WORLD_WIDTH)
    if world[y][x] == "water" or territory_owner[idx] != -1:
        return False

    if civ.get("territory"):
        connected = False
        for dx, dy in _NEIGHBORS4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT:
                if territory_owner[ny * WORLD_WIDTH + nx] == civ["id"]:
                    connected = True
                    break
        if not connected:
            return False

    territory_owner[idx] = civ["id"]
    civ["territory"].add(idx)
    civ["env_cache_year"] = -999999
    civ["frontier"].discard(idx)
    for dx, dy in _NEIGHBORS4:
        nx, ny = x + dx, y + dy
        if 0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT:
            nidx = ny * WORLD_WIDTH + nx
            if world[ny][nx] != "water" and territory_owner[nidx] == -1:
                civ["frontier"].add(nidx)
    return True


def create_civilization(i):
    x, y = choose_civilization_start()
    key = get_terrain_key(x, y)
    local_food = get_resource_value("food", x, y)
    local_water = get_resource_value("water", x, y)
    local_mining = get_resource_value("iron", x, y) + get_resource_value("minerals", x, y) + get_resource_value("oil", x, y)

    population = random.randint(500, 3000)
    intelligence = random.randint(35, 60)
    medical = random.randint(5, 20)
    wealth = random.randint(1000, 10000)
    food = random.randint(5000, 15000)

    if key == "river":
        population *= random.uniform(1.05, 1.18)
        food *= random.uniform(1.12, 1.28)
        medical += random.uniform(1, 2)
    elif key in ("plain", "coast"):
        population *= random.uniform(1.02, 1.10)
        food *= random.uniform(1.04, 1.15)
    elif key in ("mountain", "desert"):
        wealth *= random.uniform(1.03, 1.12)

    wealth *= 1 + clamp(local_mining / 6000, 0, 0.15)
    intelligence += clamp((local_food - 60) / 80, -2, 2)
    medical += clamp((local_water - 40) / 55, -2, 2)

    population = int(clamp(population, 500, 3000))
    # 시작 직후 몇 년 연속 흉작이 와도 모든 문명이 동시에 붕괴하지 않도록
    # 최소 6년치 식량 비축량을 보장한다. 지형이 좋은 곳은 기존 랜덤값이 더 클 수 있다.
    food = max(float(food), population * 6.0)

    return {
        "id": i,
        "name": CIV_NAMES[i],
        "color": CIV_COLORS[i],
        "x": x, "y": y,
        "population": population,
        "intelligence": clamp(intelligence, 0, 100),
        "medical": clamp(medical, 0, 100),
        "wealth": max(0.0, wealth),
        "food": max(0.0, food),
        "alive": True,
        "territory": set(),
        "frontier": set(),
        "env_cache": None,
        "env_cache_year": -999999,
        "trade_bonus": {"food": 0.0, "wood": 0.0, "iron": 0.0, "minerals": 0.0, "oil": 0.0},
        "last_food_production": 0.0,
        "last_food_consumption": 0.0,
        "last_wealth_change": 0.0,
        "last_population_change": 0,
        "status": "안정",
        "applied_disasters": set(),
        "war_cooldown_until": 0,
        "war_fatigue": 0.0,
        "poverty_years": 0,
        "famine_years": 0,
        "peace_years": 0,
        "last_war_damage": 0.0,
    }


def generate_civilizations():
    global civilizations, territory_owner, diplomacy, active_wars, active_epidemics, next_global_war_year
    civilizations = []
    territory_owner = [-1] * (WORLD_WIDTH * WORLD_HEIGHT)
    diplomacy = {}
    active_wars = []
    active_epidemics = []
    next_global_war_year = WAR_START_YEAR

    for i in range(CIV_COUNT):
        civ = create_civilization(i)
        civilizations.append(civ)
        # 시작 영토도 초기 인구에 맞춰 5~14칸 정도의 연결된 덩어리로 만든다.
        capital_idx = civ["y"] * WORLD_WIDTH + civ["x"]
        claim_tile(civ, capital_idx)
        _refresh_frontier_for(civ)
        initial_target = int(clamp(round(civ["population"] / 240), 5, 14))
        while len(civ["territory"]) < initial_target:
            valid = [idx for idx in civ["frontier"] if territory_owner[idx] == -1]
            if not valid:
                break
            env = get_civ_environment(civ)
            best = max(random.sample(valid, min(len(valid), 12)), key=lambda idx: expansion_tile_score(civ, idx, env))
            if not claim_tile(civ, best):
                break
        _refresh_frontier_for(civ)


def medical_historical_ceiling(current_year):
    if current_year <= 0:
        return 18.0
    progress = clamp(current_year / MEDICAL_TARGET_YEAR, 0, 1)
    # 초반은 매우 느리고 근현대로 갈수록 빨라지는 형태.
    return clamp(18.0 + 82.0 * (progress ** 0.90), 18.0, 100.0)


def disaster_overlap_fraction(civ, disaster, max_samples=100):
    """국가 영토 중 실제 재해 반경에 들어간 비율을 근사한다.
    큰 나라의 변두리에서 난 재해가 나라 전체 인구의 절반을 없애는 현상을 방지한다.
    """
    tiles = civ.get("territory") or set()
    if not tiles:
        dx = civ["x"] - disaster["x"]
        dy = civ["y"] - disaster["y"]
        return 1.0 if dx * dx + dy * dy <= disaster["radius"] ** 2 else 0.0

    if len(tiles) > max_samples:
        arr = tuple(tiles)
        step = len(arr) / max_samples
        sample = [arr[int(i * step)] for i in range(max_samples)]
    else:
        sample = tiles

    r2 = disaster["radius"] ** 2
    hit = 0
    count = 0
    for idx in sample:
        y, x = divmod(idx, WORLD_WIDTH)
        dx = x - disaster["x"]
        dy = y - disaster["y"]
        if dx * dx + dy * dy <= r2:
            hit += 1
        count += 1
    return hit / max(count, 1)


def apply_disaster_to_civilizations():
    for civ in civilizations:
        if not civ_alive(civ):
            continue
        for d in active_disasters:
            did = d.get("event_id")
            if did is None or did in civ["applied_disasters"] or d["type"].endswith("_after"):
                continue

            dx = civ["x"] - d["x"]
            dy = civ["y"] - d["y"]
            capital_hit = dx * dx + dy * dy <= (d["radius"] + 1) ** 2
            overlap = disaster_overlap_fraction(civ, d)
            if overlap <= 0 and not capital_hit:
                continue

            definition = DISASTER_DEFS[d["type"]]
            base = definition.get("population")
            severity_mult = {"약함": 0.75, "보통": 1.15, "강함": 1.55}.get(d.get("severity"), 1.0)
            if d.get("large"):
                severity_mult *= 1.20
            medical_protection = 1.0 - 0.55 * civ["medical"] / 100.0

            # 실제 피해 면적을 반영. 수도가 직접 맞으면 최소 65% 강도로 처리한다.
            impact_scale = 0.25 + 0.75 * math.sqrt(clamp(overlap, 0, 1))
            if capital_hit:
                impact_scale = max(impact_scale, 0.65)

            if base:
                raw_loss = abs(random.uniform(*base)) * severity_mult * medical_protection * impact_scale
                raw_loss = clamp(raw_loss, 0.005, 0.55)
                old = civ["population"]
                civ["population"] = max(0, int(civ["population"] * (1 - raw_loss)))
                civ["last_population_change"] += civ["population"] - old

            # 경제/식량도 피해 면적만큼 감소. 강한 재해는 여전히 크게 체감된다.
            food_loss = clamp(random.uniform(0.04, 0.16) * severity_mult * medical_protection * impact_scale, 0, 0.38)
            wealth_loss = clamp(random.uniform(0.02, 0.12) * severity_mult * medical_protection * impact_scale, 0, 0.30)
            civ["food"] *= 1 - food_loss
            civ["wealth"] *= 1 - wealth_loss
            civ["status"] = definition["name"]
            civ["applied_disasters"].add(did)


def epidemic_for(civ_id):
    for e in active_epidemics:
        if e["civ_id"] == civ_id:
            return e
    return None


def start_epidemic(civ, imported=False):
    if not civ_alive(civ) or epidemic_for(civ["id"]) is not None:
        return
    # 의료 0이면 대략 10~15년, 의료 50이면 6~10년, 의료 100이면 2~4년.
    duration = int(round(13 - civ["medical"] * 0.095 + random.uniform(-2, 2)))
    duration = int(clamp(duration, 2, 15))
    active_epidemics.append({
        "civ_id": civ["id"],
        "start_year": year,
        "end_year": year + duration - 1,
        "imported": imported,
    })
    civ["status"] = "전염병"
    event_history.append((year, f"{civ['name']} 전염병 {'유입' if imported else '발생'} ({duration}년 예상)"))


def update_epidemics():
    # 신규 자연 발생: 국가별 연 0.5%
    infected_ids = {e["civ_id"] for e in active_epidemics}
    for civ in civilizations:
        if civ_alive(civ) and civ["id"] not in infected_ids and random.random() < 0.005:
            start_epidemic(civ)

    # 최근 3년 내 무역국 사이에는 전염병 유입 가능성 증가.
    infected_ids = {e["civ_id"] for e in active_epidemics}
    for key, rel in list(diplomacy.items()):
        if rel.get("last_trade_year", -9999) < year - 3:
            continue
        a_id, b_id = key
        a, b = civilizations[a_id], civilizations[b_id]
        if not (civ_alive(a) and civ_alive(b)):
            continue
        if a_id in infected_ids and b_id not in infected_ids:
            chance = 0.025 * (1 - 0.70 * b["medical"] / 100)
            if random.random() < chance:
                start_epidemic(b, imported=True)
                infected_ids.add(b_id)
        elif b_id in infected_ids and a_id not in infected_ids:
            chance = 0.025 * (1 - 0.70 * a["medical"] / 100)
            if random.random() < chance:
                start_epidemic(a, imported=True)
                infected_ids.add(a_id)

    # 지속 중인 전염병은 매년 피해. 의료가 높을수록 사망률과 기간이 모두 감소.
    survivors = []
    for e in active_epidemics:
        civ = civilizations[e["civ_id"]]
        if not civ_alive(civ):
            continue
        if year > e["end_year"]:
            event_history.append((year, f"{civ['name']} 전염병 종식"))
            continue
        civ["status"] = "전염병"
        severity = random.uniform(0.012, 0.040)
        mortality = severity * (1.0 - 0.82 * civ["medical"] / 100)
        old = civ["population"]
        civ["population"] = max(0, int(civ["population"] * (1 - mortality)))
        civ["last_population_change"] += civ["population"] - old
        civ["wealth"] *= 1 - clamp(0.015 + mortality * 1.5, 0, 0.08)
        civ["food"] *= 1 - clamp(0.01 + mortality, 0, 0.06)
        survivors.append(e)
    active_epidemics[:] = survivors


def countries_border(a, b):
    if not a["territory"] or not b["territory"]:
        return False
    # 작은 쪽의 영토만 검사.
    small = a if len(a["territory"]) <= len(b["territory"]) else b
    other_id = b["id"] if small is a else a["id"]
    for idx in small["territory"]:
        y, x = divmod(idx, WORLD_WIDTH)
        for dx, dy in _NEIGHBORS4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT:
                if territory_owner[ny * WORLD_WIDTH + nx] == other_id:
                    return True
    return False


def bordering_countries(civ):
    """현재 실제 영토 국경을 맞댄 살아 있는 국가 목록."""
    result = []
    if not civ_alive(civ):
        return result
    for other in civilizations:
        if other["id"] == civ["id"] or not civ_alive(other):
            continue
        if countries_border(civ, other):
            result.append(other)
    return result


def war_lock_reason(civ):
    """UI에서 전쟁 가능 조건을 간단히 표시."""
    reasons = []
    if year < WAR_START_YEAR:
        reasons.append(f"시대 {year}/{WAR_START_YEAR}년")
    if civ["population"] < 3_000:
        reasons.append(f"인구 {civ['population']:,}/3,000")
    if civ["intelligence"] < 32:
        reasons.append(f"지능 {civ['intelligence']:.1f}/32")
    if civ["wealth"] < 5_000:
        reasons.append(f"재산 {civ['wealth']:,.0f}/5,000")
    dev = development_level(civ)
    if dev < 32:
        reasons.append(f"발달도 {dev:.1f}/32")
    return " · ".join(reasons) if reasons else "전쟁 가능"


def territory_resource_strength(civ, env=None):
    """현재 보유 영토의 자원 종합 점수(0~1.5 정도).
    식량/물은 생존, 철/광물/석유는 국가 확장·군사 능력에 더 크게 반영한다.
    """
    if env is None:
        env = get_civ_environment(civ)
    survival = clamp(env["food"] / 95, 0, 1.4) * 0.34 + clamp(env["water"] / 80, 0, 1.4) * 0.24
    industry = (
        clamp(env["wood"] / 70, 0, 1.6) * 0.10
        + clamp(env["iron"] / 55, 0, 1.8) * 0.15
        + clamp(env["minerals"] / 60, 0, 1.8) * 0.11
        + clamp(env["oil"] / 55, 0, 1.8) * 0.06
    )
    return clamp(survival + industry, 0, 1.5)


def ideal_people_per_tile(civ, env=None):
    """나라별 적정 인구밀도.

    지형/자원/발달도에 따라 차이는 나지만 범위를 좁게 잡아
    '영토는 작은데 인구만 수십 배' 또는 그 반대가 생기지 않게 한다.
    """
    if env is None:
        env = get_civ_environment(civ)

    # 생존 자원이 좋은 지역은 조금 더 높은 밀도를 버틸 수 있지만 차이는 제한한다.
    food_water = clamp((env["food"] / 95) * 0.62 + (env["water"] / 80) * 0.38, 0.55, 1.45)
    resource_mult = clamp(0.82 + (food_water - 0.75) * 0.34, 0.80, 1.22)

    # 발달할수록 같은 면적에 더 많은 인구를 유지할 수 있다. 이것도 과도하게 커지지 않게 제한한다.
    dev = development_level(civ)
    dev_mult = clamp(0.90 + dev * 0.0038, 0.90, 1.28)

    # 무역은 식량/자원 압력을 완화하지만 밀도를 10% 이상 올리지는 않는다.
    trade_mult = 1.0 + clamp(sum(civ.get("trade_bonus", {}).values()) * 0.010, 0, 0.08)

    density = BASE_PEOPLE_PER_TILE * resource_mult * dev_mult * trade_mult
    return clamp(density, 175.0, 390.0)


def estimated_carrying_capacity(civ, env=None):
    """현재 영토 크기에 거의 비례하는 인구 수용력.

    핵심은 '칸 수 × 적정 인구밀도'이고, 자원/발달도는 밀도를 조금만 바꾼다.
    따라서 영토 크기와 인구 규모가 시각적으로 너무 동떨어지지 않는다.
    """
    if env is None:
        env = get_civ_environment(civ)
    tiles = max(1, len(civ.get("territory", ())))
    density = ideal_people_per_tile(civ, env)

    war_penalty = 0.82 if active_war_for_civ(civ) is not None else (0.93 if civ.get("war_fatigue", 0) > 45 else 1.0)
    capacity = tiles * density * war_penalty
    return clamp(capacity, 500.0, 5_000_000.0)


def target_territory_size(civ, env=None):
    """현재 인구라면 어느 정도 영토가 자연스러운지 계산한다."""
    if env is None:
        env = get_civ_environment(civ)
    density = ideal_people_per_tile(civ, env)
    # 목표는 수용력의 약 78% 정도를 채우는 상태. 너무 빽빽하지도, 너무 텅 비지도 않게 한다.
    target = math.ceil(civ["population"] / max(density * TERRITORY_TARGET_FILL, 1.0))
    return max(4, target)


def expansion_profile(civ, env=None):
    """인구에 비해 영토가 부족한 정도 + 자원 부족 + 국가 능력을 계산한다."""
    if env is None:
        env = get_civ_environment(civ)

    cap = estimated_carrying_capacity(civ, env)
    current_tiles = max(1, len(civ.get("territory", ())))
    target_tiles = target_territory_size(civ, env)
    territory_deficit = max(0.0, (target_tiles - current_tiles) / max(target_tiles, 1))
    density = civ["population"] / max(cap, 1)
    resource_need = resource_pressure(civ, env)
    military = military_power(civ) / 100.0
    dev = development_level(civ) / 100.0
    wealth = clamp(wealth_level(civ) / 100.0, 0, 1)
    resources = territory_resource_strength(civ, env)

    # 가장 큰 이유는 '인구에 비해 땅이 부족함'. 자원 부족은 그 다음 보정값이다.
    need = clamp(territory_deficit * 0.90 + resource_need * 0.38 + max(0, density - 0.82) * 0.35, 0, 1.35)
    ability = clamp(0.18 + military * 0.34 + dev * 0.24 + wealth * 0.14 + min(resources, 1.0) * 0.10, 0, 1.15)
    return cap, density, resource_need, military, need, ability


def expansion_tile_score(civ, idx, env):
    """현재 부족한 자원을 보완하는 방향으로 새 영토를 선택한다."""
    y, x = divmod(idx, WORLD_WIDTH)
    food = get_resource_value_fast("food", x, y)
    water = get_resource_value_fast("water", x, y)
    wood = get_resource_value_fast("wood", x, y)
    iron = get_resource_value_fast("iron", x, y)
    minerals = get_resource_value_fast("minerals", x, y)
    oil = get_resource_value_fast("oil", x, y)

    wf = 1.10 + (0.95 if env["food"] < 55 or civ["food"] < civ["population"] * 2 else 0.0)
    ww = 0.90 + (0.85 if env["water"] < 35 else 0.0)
    wi = 0.18 + (0.55 if env["iron"] < 18 else 0.0) + military_power(civ) / 420
    wm = 0.12 + (0.35 if env["minerals"] < 18 else 0.0)
    wo = 0.05 + (0.25 if year >= 900 and env["oil"] < 12 else 0.0)
    return food * wf + water * ww + wood * 0.12 + iron * wi + minerals * wm + oil * wo + random.random() * 10


def _nearby_coastal_colonization(civ, env):
    """가까운 섬/해안만 작은 '덩어리'로 정착한다.

    예전처럼 전 세계 빈 칸을 바로 한 칸씩 찍는 방식은 사용하지 않는다.
    기존 영토에서 최대 NEARBY_COLONY_MAX_GAP칸 이내이고, 물을 사이에 둔 가까운 육지만 후보가 된다.
    """
    if year < 850 or year % NEARBY_COLONY_INTERVAL != 0:
        return 0
    if not civ.get("territory"):
        return 0

    current_tiles = len(civ["territory"])
    target_tiles = target_territory_size(civ, env)
    if current_tiles >= target_tiles:
        return 0

    # 기존 영토의 해안 가장자리만 출발점으로 사용한다.
    owned_coasts = []
    for idx in civ["territory"]:
        y, x = divmod(idx, WORLD_WIDTH)
        if any(
            0 <= x + dx < WORLD_WIDTH and 0 <= y + dy < WORLD_HEIGHT
            and world[y + dy][x + dx] == "water"
            for dx, dy in _NEIGHBORS4
        ):
            owned_coasts.append((x, y))
    if not owned_coasts:
        return 0

    # 가까운 바다 건너편의 미점유 육지만 후보. 수도에서 먼 전 세계 랜덤 점프는 금지.
    seeds = []
    for ox, oy in random.sample(owned_coasts, min(len(owned_coasts), 40)):
        for dy in range(-NEARBY_COLONY_MAX_GAP, NEARBY_COLONY_MAX_GAP + 1):
            for dx in range(-NEARBY_COLONY_MAX_GAP, NEARBY_COLONY_MAX_GAP + 1):
                if dx == 0 and dy == 0:
                    continue
                if dx * dx + dy * dy > NEARBY_COLONY_MAX_GAP ** 2:
                    continue
                nx, ny = ox + dx, oy + dy
                if not (0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT):
                    continue
                nidx = ny * WORLD_WIDTH + nx
                if territory_owner[nidx] != -1 or world[ny][nx] == "water":
                    continue
                # 이미 육지로 직접 이어진 frontier라면 일반 확장이 처리하므로 제외.
                direct = any(
                    0 <= nx + ax < WORLD_WIDTH and 0 <= ny + ay < WORLD_HEIGHT
                    and territory_owner[(ny + ay) * WORLD_WIDTH + (nx + ax)] == civ["id"]
                    for ax, ay in _NEIGHBORS4
                )
                if direct:
                    continue
                seeds.append(nidx)

    if not seeds:
        return 0

    seed = max(random.sample(seeds, min(30, len(seeds))), key=lambda idx: expansion_tile_score(civ, idx, env))

    # 한 점만 생기지 않도록 seed 주변의 연결된 미점유 육지를 BFS로 4~9칸 묶어서 정착.
    wanted = min(max(4, target_tiles - current_tiles), 9)
    queue = [seed]
    seen = {seed}
    cluster = []
    pos = 0
    while pos < len(queue) and len(cluster) < wanted:
        idx = queue[pos]
        pos += 1
        if territory_owner[idx] != -1:
            continue
        y, x = divmod(idx, WORLD_WIDTH)
        if world[y][x] == "water":
            continue
        cluster.append(idx)
        for dx, dy in _NEIGHBORS4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT:
                nidx = ny * WORLD_WIDTH + nx
                if nidx not in seen and territory_owner[nidx] == -1 and world[ny][nx] != "water":
                    seen.add(nidx)
                    queue.append(nidx)

    # 아주 작은 1~2칸 섬이면 '점 식민지'를 만들지 않는다.
    if len(cluster) < 4:
        return 0

    for idx in cluster:
        territory_owner[idx] = civ["id"]
        civ["territory"].add(idx)
    civ["env_cache_year"] = -999999
    _refresh_frontier_for(civ)
    return len(cluster)


def _same_owner_neighbor_count(civ, idx):
    y, x = divmod(idx, WORLD_WIDTH)
    count = 0
    for dx, dy in _NEIGHBORS4:
        nx, ny = x + dx, y + dy
        if 0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT:
            if territory_owner[ny * WORLD_WIDTH + nx] == civ["id"]:
                count += 1
    return count


def _abandon_sparse_edge(civ, env):
    """전쟁/재난 뒤 인구가 크게 줄었는데 영토만 과도하게 큰 경우 변두리부터 천천히 포기한다.

    이때 같은 나라 이웃이 0~1개인 끝부분만 제거하므로 본토가 조각나는 현상을 최대한 피한다.
    """
    if active_war_for_civ(civ) is not None or civ.get("peace_years", 0) < 8:
        return 0
    current = len(civ.get("territory", ()))
    target = target_territory_size(civ, env)
    if current <= max(target + 3, int(target * TERRITORY_SHRINK_START)):
        return 0

    excess = current - max(target, 4)
    remove_n = min(4, max(1, excess // 35 + 1))
    candidates = []
    capital_idx = civ["y"] * WORLD_WIDTH + civ["x"]
    for idx in civ["territory"]:
        if idx == capital_idx:
            continue
        n = _same_owner_neighbor_count(civ, idx)
        if n <= 1:
            candidates.append(idx)

    # 수도에서 먼 끝부분부터 포기한다.
    candidates.sort(
        key=lambda idx: (idx % WORLD_WIDTH - civ["x"]) ** 2 + (idx // WORLD_WIDTH - civ["y"]) ** 2,
        reverse=True,
    )
    removed = 0
    for idx in candidates[:remove_n]:
        if idx not in civ["territory"]:
            continue
        civ["territory"].remove(idx)
        territory_owner[idx] = -1
        removed += 1
    if removed:
        civ["env_cache_year"] = -999999
        _refresh_frontier_for(civ)
    return removed


def _remove_tiny_territory_fragments(civ, min_size=4):
    """버그/점령 계산으로 생긴 1~3칸짜리 고립 점 영토를 자동 정리한다."""
    tiles = set(civ.get("territory", ()))
    if not tiles:
        return 0

    components = []
    unseen = set(tiles)
    while unseen:
        start = unseen.pop()
        comp = {start}
        queue = [start]
        pos = 0
        while pos < len(queue):
            idx = queue[pos]
            pos += 1
            y, x = divmod(idx, WORLD_WIDTH)
            for dx, dy in _NEIGHBORS4:
                nx, ny = x + dx, y + dy
                if 0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT:
                    nidx = ny * WORLD_WIDTH + nx
                    if nidx in unseen:
                        unseen.remove(nidx)
                        comp.add(nidx)
                        queue.append(nidx)
        components.append(comp)

    if len(components) <= 1:
        return 0

    capital_idx = civ["y"] * WORLD_WIDTH + civ["x"]
    removed = 0
    for comp in components:
        # 수도가 있는 본토는 크기와 상관없이 유지. 4칸 이상인 실제 식민/점령 덩어리도 유지.
        if capital_idx in comp or len(comp) >= min_size:
            continue
        for idx in comp:
            if territory_owner[idx] == civ["id"]:
                territory_owner[idx] = -1
            civ["territory"].discard(idx)
            removed += 1
    if removed:
        civ["env_cache_year"] = -999999
        _refresh_frontier_for(civ)
    return removed


def expand_territories():
    if year % TERRITORY_EXPANSION_INTERVAL != 0:
        return

    for civ in civilizations:
        if not civ_alive(civ):
            continue

        env = get_civ_environment(civ)
        current_tiles = len(civ.get("territory", ()))
        target_tiles = target_territory_size(civ, env)
        cap, density, resource_need, military, need, ability = expansion_profile(civ, env)

        # 인구에 비해 이미 땅이 충분하면 무작정 넓히지 않는다.
        deficit = max(0, target_tiles - current_tiles)
        if deficit > 0:
            # 영토가 인구에 비해 부족하면 이전보다 적극적으로 넓힌다.
            # 여러 칸을 먹더라도 claim_tile() 때문에 항상 기존 국경과 연결된 모양으로만 확장된다.
            attempts = 2 + deficit // 10
            if deficit >= 25:
                attempts += 2
            if deficit >= 60:
                attempts += 2
            if resource_need > 0.45:
                attempts += 1
            if military > 0.62 and ability > 0.62:
                attempts += 1
            # 전쟁 중에도 확장을 완전히 멈추진 않지만 평시의 절반 정도로 둔다.
            if active_war_for_civ(civ) is not None:
                attempts = max(1, attempts // 2)
            attempts = int(clamp(attempts, 0, TERRITORY_MAX_EXPAND_PER_YEAR))

            for _ in range(attempts):
                valid = [idx for idx in civ["frontier"] if territory_owner[idx] == -1]
                if not valid:
                    _refresh_frontier_for(civ)
                    valid = [idx for idx in civ["frontier"] if territory_owner[idx] == -1]
                    if not valid:
                        break

                candidates = random.sample(valid, min(20, len(valid)))
                best = max(candidates, key=lambda idx: expansion_tile_score(civ, idx, env))
                if claim_tile(civ, best):
                    env = get_civ_environment(civ)

        # 본토 frontier가 막혔고 영토가 부족한 경우에만 가까운 섬으로 드문 확장.
        if len(civ.get("territory", ())) < target_territory_size(civ, env):
            _nearby_coastal_colonization(civ, env)

        # 인구가 크게 줄었는데 영토만 지나치게 넓은 상태도 천천히 정리한다.
        env = get_civ_environment(civ)
        _abandon_sparse_edge(civ, env)
        _remove_tiny_territory_fragments(civ)


def military_power(civ):
    """인구·경제뿐 아니라 보유 전략자원과 보급 능력을 반영한 군사력(0~100 근사)."""
    if not civ_alive(civ):
        return 0.0
    env = get_civ_environment(civ)
    pop_score = clamp(22.0 * math.log10(1.0 + civ["population"] / 900), 0, 100)
    wealth_score = clamp(20.0 * math.log10(1.0 + civ["wealth"] / 3_000), 0, 100)
    intel_score = civ["intelligence"]
    medical_score = civ["medical"]
    food_score = clamp(civ["food"] / max(civ["population"] * 4, 1) * 100, 0, 100)
    territory_score = clamp(math.sqrt(max(len(civ.get("territory", ())), 0)) * 7.0, 0, 100)
    strategic_score = clamp(
        env["iron"] * 1.05 + env["minerals"] * 0.62 + env["oil"] * 0.46 + env["wood"] * 0.16,
        0, 100
    )
    fatigue_mult = clamp(1.0 - civ.get("war_fatigue", 0) / 240, 0.58, 1.0)
    power = (
        pop_score * 0.28
        + wealth_score * 0.22
        + intel_score * 0.15
        + medical_score * 0.06
        + food_score * 0.08
        + territory_score * 0.06
        + strategic_score * 0.15
    )
    return clamp(power * fatigue_mult, 0, 100)


def at_war(a, b):
    ids = {a["id"], b["id"]}
    return any({w["a"], w["b"]} == ids for w in active_wars)


def active_war_for_civ(civ):
    for w in active_wars:
        if civ["id"] in (w["a"], w["b"]):
            return w
    return None


def war_opponent(civ, war=None):
    war = war or active_war_for_civ(civ)
    if war is None:
        return None
    other_id = war["b"] if war["a"] == civ["id"] else war["a"]
    if 0 <= other_id < len(civilizations):
        other = civilizations[other_id]
        return other if civ_alive(other) else None
    return None


def resource_pressure(civ, env):
    pressure = 0.0
    if civ["food"] < civ["population"] * 1.5:
        pressure += 0.40
    if env["iron"] < 15:
        pressure += 0.20
    if env["wood"] < 20:
        pressure += 0.10
    if env["water"] < 30:
        pressure += 0.20
    if env["minerals"] < 15:
        pressure += 0.10
    return clamp(pressure, 0, 1)


def trade_between(a, b, env_a, env_b):
    if not (can_trade(a) and can_trade(b)) or at_war(a, b):
        return False
    dist = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
    if dist > min(trade_range(a), trade_range(b)):
        return False
    rel = get_diplomacy(a, b)
    if rel["relation"] <= -55:
        return False

    needs_a = []
    needs_b = []
    if a["food"] < a["population"] * 2.5: needs_a.append("food")
    if b["food"] < b["population"] * 2.5: needs_b.append("food")
    for k, threshold in (("wood", 22), ("iron", 18), ("minerals", 18), ("oil", 12)):
        if env_a[k] < threshold and env_b[k] > threshold * 1.5: needs_a.append(k)
        if env_b[k] < threshold and env_a[k] > threshold * 1.5: needs_b.append(k)

    # 서로 보완 관계가 있거나 우호 관계면 일반 교역 가능.
    complement = bool(needs_a or needs_b)
    # 평화국은 무역을 꽤 자주 하게 해서 전쟁 없이 성장하는 국가도 생긴다.
    chance = 0.14 + max(rel["relation"], 0) / 750
    if complement:
        chance += 0.18
    if random.random() >= chance:
        return False

    labels = []
    if "food" in needs_a and b["food"] > b["population"] * 3:
        amount = min(b["food"] - b["population"] * 3, max(a["population"] * 0.45, 180))
        amount = max(0, amount)
        a["food"] += amount
        b["food"] -= amount
        labels.append("식량")
    if "food" in needs_b and a["food"] > a["population"] * 3:
        amount = min(a["food"] - a["population"] * 3, max(b["population"] * 0.45, 180))
        amount = max(0, amount)
        b["food"] += amount
        a["food"] -= amount
        labels.append("식량")

    for k, label in (("wood", "목재"), ("iron", "철"), ("minerals", "광물"), ("oil", "석유")):
        if k in needs_a:
            a["trade_bonus"][k] = min(1.0, a["trade_bonus"][k] + 0.25)
            labels.append(label)
        if k in needs_b:
            b["trade_bonus"][k] = min(1.0, b["trade_bonus"][k] + 0.25)
            labels.append(label)

    volume = max(120.0, min(a["wealth"], b["wealth"]) * random.uniform(0.004, 0.016))
    a["wealth"] += volume * 0.40
    b["wealth"] += volume * 0.40
    rel["last_trade_year"] = year
    change_relation(a, b, 2.0)
    if labels and random.random() < 0.55:
        event_history.append((year, f"{a['name']} ↔ {b['name']} 무역 ({'/'.join(sorted(set(labels)))})"))
    return True


def maybe_start_war(attacker, defender, env_a, env_b):
    global next_global_war_year

    # 시대 제한: 300년 전에는 어떤 경우에도 전쟁이 시작되지 않는다.
    if year < WAR_START_YEAR or year % WAR_CHECK_INTERVAL != 0:
        return False
    # 세계 전체 새 전쟁 빈도를 제한해서 100년에 여러 전쟁이 우르르 터지는 현상을 막는다.
    if year < next_global_war_year:
        return False
    if not can_start_war(attacker) or not civ_alive(defender):
        return False
    if attacker["id"] == defender["id"] or at_war(attacker, defender):
        return False
    if year < attacker.get("war_cooldown_until", 0):
        return False
    # 한 국가는 동시에 최대 1개의 전쟁만 진행한다.
    if any(attacker["id"] in (w["a"], w["b"]) for w in active_wars):
        return False
    if any(defender["id"] in (w["a"], w["b"]) for w in active_wars):
        return False

    rel = get_diplomacy(attacker, defender)
    if year <= rel.get("truce_until", -1):
        return False

    border = countries_border(attacker, defender)
    capital_distance = math.hypot(attacker["x"] - defender["x"], attacker["y"] - defender["y"])
    territory_gap = 0.0 if border else territory_gap_estimate(attacker, defender)
    max_distance = min(war_range(attacker), war_range(defender))

    # 핵심 안전장치: 비접경 국가는 '실제 영토끼리' 충분히 가까울 때만 전쟁 가능.
    # 수도가 가까워 보여도 영토 간격이 멀면 전쟁하지 않는다.
    if not border and territory_gap > max_distance:
        return False
    # 수도 자체도 지나치게 멀면 금지. 영토 반지름 근사 오차로 먼 나라가 통과하는 것을 한 번 더 막는다.
    if not border and capital_distance > max_distance + 34.0:
        return False

    pressure = resource_pressure(attacker, env_a)
    target_richness = clamp((env_b["iron"] + env_b["minerals"] + env_b["food"]) / 220, 0, 1)
    crowding = clamp(attacker["population"] / max(12_000 + len(attacker["territory"]) * 180, 1), 0, 1)
    hostility = clamp((-rel["relation"] + 10) / 110, 0, 1)

    power_a = military_power(attacker)
    power_b = military_power(defender)
    advantage = clamp((power_a - power_b + 18) / 55, 0, 1)

    # 접촉했다고 자동 전쟁하지 않는다. 관계/자원/과밀/전력 우위가 있어야 확률이 올라간다.
    distance_factor = 1.0 if border else clamp(1.0 - territory_gap / max(max_distance * 1.15, 1), 0.18, 0.78)
    war_chance = (
        0.006
        + 0.024 * pressure
        + 0.014 * target_richness
        + 0.018 * crowding
        + 0.045 * hostility
        + 0.032 * advantage
        + (0.008 if border else 0.0)
    ) * distance_factor

    # 강대국이 약소국을 노리는 경우 약간 올라가지만 너무 자주 발생하지 않게 제한한다.
    if power_a >= power_b * 1.35:
        war_chance += 0.008
    if power_a >= power_b * 1.70:
        war_chance += 0.006

    # 우호 관계일수록 확률을 크게 낮춘다.
    if rel["relation"] >= 60:
        war_chance *= 0.04
    elif rel["relation"] >= 30:
        war_chance *= 0.16
    elif rel["relation"] >= 10:
        war_chance *= 0.45

    if random.random() >= clamp(war_chance, 0, 0.10):
        return False

    large = is_large_war_capable(attacker) and is_large_war_capable(defender)
    # 한 번 시작한 전쟁은 너무 빨리 끝나지 않게 5~20년 범위에서 지속된다.
    min_years = random.randint(WAR_MIN_DURATION, 8)
    low_max = 13 if large else 10
    max_years = random.randint(max(min_years + 3, low_max), WAR_MAX_DURATION)
    active_wars.append({
        "a": attacker["id"], "b": defender["id"],
        "start_year": year, "min_years": min_years, "max_years": max_years,
        "score": 0.0, "large": large,
        "casualties_a": 0, "casualties_b": 0,
        "food_lost_a": 0.0, "food_lost_b": 0.0,
        "wealth_lost_a": 0.0, "wealth_lost_b": 0.0,
    })
    change_relation(attacker, defender, random.uniform(-40, -65))
    attacker["status"] = "전쟁"
    defender["status"] = "전쟁"

    # 다음 새 전쟁은 세계 전체 기준 32~52년 뒤에나 시작할 수 있다.
    next_global_war_year = year + random.randint(GLOBAL_WAR_GAP_MIN, GLOBAL_WAR_GAP_MAX)

    contact = "접경전쟁" if border else f"근거리전쟁/영토간격 {territory_gap:.0f}칸"
    event_history.append((year, f"{attacker['name']}와 {defender['name']} 전쟁 시작 ({attacker['name']} 공격 · {contact} · 최대 {max_years}년)"))
    return True


def transfer_border_territory(winner, loser, amount):
    """실제 접경선에서만 영토를 덩어리로 점령한다.

    비접경 전쟁은 인구/경제 피해는 줄 수 있지만, 지도 반대편에 1칸짜리 점령지가
    갑자기 생기지는 않는다. 영토 이동은 두 나라 영토가 맞닿았을 때만 발생한다.
    """
    if amount <= 0 or not loser.get("territory") or not winner.get("territory"):
        return 0

    border_candidates = []
    for idx in loser["territory"]:
        y, x = divmod(idx, WORLD_WIDTH)
        for dx, dy in _NEIGHBORS4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT:
                if territory_owner[ny * WORLD_WIDTH + nx] == winner["id"]:
                    border_candidates.append(idx)
                    break

    # 서로 안 붙어 있으면 영토 점령 없음. 원거리전쟁으로 점 영토가 생기는 핵심 오류 차단.
    if not border_candidates:
        return 0

    seed = min(
        border_candidates,
        key=lambda idx: (idx % WORLD_WIDTH - winner["x"]) ** 2 + (idx // WORLD_WIDTH - winner["y"]) ** 2,
    )

    # 접경 seed에서 loser 영토 내부로 BFS해서 하나의 연결된 덩어리만 가져온다.
    queue = [seed]
    seen = {seed}
    chosen = []
    pos = 0
    while pos < len(queue) and len(chosen) < amount:
        idx = queue[pos]
        pos += 1
        if idx not in loser["territory"]:
            continue
        chosen.append(idx)
        y, x = divmod(idx, WORLD_WIDTH)
        for dx, dy in _NEIGHBORS4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT:
                nidx = ny * WORLD_WIDTH + nx
                if nidx in loser["territory"] and nidx not in seen:
                    seen.add(nidx)
                    queue.append(nidx)

    moved = 0
    for idx in chosen:
        if idx not in loser["territory"]:
            continue
        loser["territory"].discard(idx)
        winner["territory"].add(idx)
        territory_owner[idx] = winner["id"]
        moved += 1

    if moved:
        winner["env_cache_year"] = -999999
        loser["env_cache_year"] = -999999
        _refresh_frontier_for(winner)
        _refresh_frontier_for(loser)
        _remove_tiny_territory_fragments(winner)
        _remove_tiny_territory_fragments(loser)
    return moved


def update_wars():
    remaining = []
    for w in list(active_wars):
        a, b = civilizations[w["a"]], civilizations[w["b"]]
        if not (civ_alive(a) and civ_alive(b)):
            continue

        a["status"] = "⚔ 전쟁 중"
        b["status"] = "⚔ 전쟁 중"

        base_a = military_power(a)
        base_b = military_power(b)
        # 운 요소는 매우 작게 두어 강한 국가가 장기전에서도 우세하도록 한다.
        pa = base_a * random.uniform(0.985, 1.015)
        pb = base_b * random.uniform(0.985, 1.015)
        total = max(pa + pb, 1.0)
        a_share = pa / total
        b_share = pb / total

        # 전쟁 피로가 누적되면 생산/보급이 더 무너진다.
        a["war_fatigue"] = clamp(a.get("war_fatigue", 0.0) + random.uniform(4.0, 7.5) * (0.8 + b_share), 0, 100)
        b["war_fatigue"] = clamp(b.get("war_fatigue", 0.0) + random.uniform(4.0, 7.5) * (0.8 + a_share), 0, 100)

        # 직접 전투 사망. 약한 나라가 더 큰 피해를 받지만 양쪽 모두 상당한 손실을 입는다.
        # 진짜 장기 피해의 상당 부분은 아래 식량/경제 붕괴에서 추가로 발생한다.
        loss_a = random.uniform(0.004, 0.010) * (0.55 + b_share * 1.65)
        loss_b = random.uniform(0.004, 0.010) * (0.55 + a_share * 1.65)
        if w["large"]:
            loss_a *= 1.25
            loss_b *= 1.25
        # 압도적인 전력 차이면 약한 쪽 피해를 더 크게 만든다.
        if pa > pb * 1.45:
            loss_b *= 1.35
            loss_a *= 0.82
        elif pb > pa * 1.45:
            loss_a *= 1.35
            loss_b *= 0.82
        loss_a = clamp(loss_a, 0.002, 0.032)
        loss_b = clamp(loss_b, 0.002, 0.032)

        old_a, old_b = a["population"], b["population"]
        a["population"] = max(0, int(a["population"] * (1 - loss_a)))
        b["population"] = max(0, int(b["population"] * (1 - loss_b)))
        da = old_a - a["population"]
        db = old_b - b["population"]
        a["last_population_change"] -= da
        b["last_population_change"] -= db
        w["casualties_a"] += da
        w["casualties_b"] += db

        # 전쟁은 농지·보급·교역·산업을 파괴한다. 식량과 재산 손실을 크게 줘서
        # 이후 몇 년간 기근/빈곤으로 추가 인구 감소가 이어질 수 있다.
        food_rate_a = clamp(random.uniform(0.055, 0.115) * (0.75 + b_share) * (1 + a["war_fatigue"] / 220), 0.03, 0.18)
        food_rate_b = clamp(random.uniform(0.055, 0.115) * (0.75 + a_share) * (1 + b["war_fatigue"] / 220), 0.03, 0.18)
        wealth_rate_a = clamp(random.uniform(0.025, 0.065) * (0.75 + b_share), 0.015, 0.10)
        wealth_rate_b = clamp(random.uniform(0.025, 0.065) * (0.75 + a_share), 0.015, 0.10)

        old_food_a, old_food_b = a["food"], b["food"]
        old_wealth_a, old_wealth_b = a["wealth"], b["wealth"]
        a["food"] *= 1 - food_rate_a
        b["food"] *= 1 - food_rate_b
        a["wealth"] *= 1 - wealth_rate_a
        b["wealth"] *= 1 - wealth_rate_b
        w["food_lost_a"] += old_food_a - a["food"]
        w["food_lost_b"] += old_food_b - b["food"]
        w["wealth_lost_a"] += old_wealth_a - a["wealth"]
        w["wealth_lost_b"] += old_wealth_b - b["wealth"]
        a["last_war_damage"] = food_rate_a + wealth_rate_a
        b["last_war_damage"] = food_rate_b + wealth_rate_b

        delta = (pa - pb) / total
        w["score"] += delta * 1.05

        years = year - w["start_year"] + 1

        # 우세한 쪽이 매년 조금씩 점령하되, 초반 1~2년에는 급격한 영토 삭제를 막는다.
        if years >= 2 and abs(delta) > 0.018:
            winner, loser = (a, b) if delta > 0 else (b, a)
            advantage = clamp(abs(delta) * 3.2, 0.06, 0.90)
            fraction = 0.005 + advantage * (0.025 if w["large"] else 0.017)
            amount = max(1, int(len(loser["territory"]) * fraction))
            amount = min(amount, 38 if w["large"] else 20)
            transfer_border_territory(winner, loser, amount)

        # 생존선 이하/영토 소멸이면 즉시 국가 멸망. 접경 중이면 일부 영토가 넘어가고,
        # 비접경 전쟁이면 점 영토를 만들지 않기 위해 멀리 있는 영토는 합병하지 않는다.
        if a["population"] <= EXTINCTION_POPULATION or b["population"] <= EXTINCTION_POPULATION:
            winner, loser = (b, a) if a["population"] <= EXTINCTION_POPULATION else (a, b)
            transfer_border_territory(winner, loser, len(loser.get("territory", ())))
            loser["population"] = 0
            event_history.append((year, f"{winner['name']}가 {loser['name']}를 장기전 끝에 붕괴시킴"))
            continue

        if not a["territory"] or not b["territory"]:
            winner, loser = (b, a) if not a["territory"] else (a, b)
            transfer_border_territory(winner, loser, len(loser.get("territory", ())))
            loser["population"] = 0
            event_history.append((year, f"{loser['name']}가 모든 영토를 잃어 {winner['name']}에 흡수"))
            continue

        # 최소 기간 전에는 아무리 우세해도 종전하지 않는다. 최대 20년에는 반드시 끝난다.
        decisive = years >= w.get("min_years", WAR_MIN_DURATION) and abs(w["score"]) >= 1.65
        if years >= w["max_years"] or decisive:
            if abs(w["score"]) < 0.12:
                # 거의 무승부면 점령을 최소화한다.
                winner = a if pa >= pb else b
                loser = b if winner is a else a
                frac = 0.03
                result_label = "근소한 승리"
            else:
                winner, loser = (a, b) if w["score"] >= 0 else (b, a)
                margin = abs(w["score"])
                if margin < 0.55:
                    frac = 0.08
                    result_label = "승리"
                elif margin < 1.15:
                    frac = 0.18
                    result_label = "대승"
                else:
                    frac = 0.30
                    result_label = "압도적 승리"
            extra = max(1, int(len(loser["territory"]) * frac))
            transfer_border_territory(winner, loser, min(extra, 120))

            rel = get_diplomacy(a, b)
            rel["truce_until"] = year + random.randint(WAR_TRUCE_MIN, WAR_TRUCE_MAX)
            a["war_cooldown_until"] = year + random.randint(14, 26)
            b["war_cooldown_until"] = year + random.randint(14, 26)
            event_history.append((
                year,
                f"{a['name']}와 {b['name']} 전쟁 종결 ({years}년) - {winner['name']} {result_label} · "
                f"전투 인구피해 {w['casualties_a'] + w['casualties_b']:,}명"
            ))
        else:
            remaining.append(w)

    active_wars[:] = remaining


def update_interactions():
    if year % DIPLOMACY_INTERVAL != 0:
        return

    alive = [c for c in civilizations if civ_alive(c)]
    envs = {c["id"]: get_civ_environment(c) for c in alive}

    for i in range(len(alive)):
        for j in range(i + 1, len(alive)):
            a, b = alive[i], alive[j]
            if not (can_diplomacy(a) or can_diplomacy(b) or can_start_war(a) or can_start_war(b)):
                continue

            rel = get_diplomacy(a, b)
            if at_war(a, b):
                continue

            border = countries_border(a, b)
            pa = resource_pressure(a, envs[a["id"]])
            pb = resource_pressure(b, envs[b["id"]])

            # 평화라고 자동으로 우호국이 되지 않게 아주 작은 변화만 둔다.
            change_relation(a, b, random.uniform(-0.10, 0.10))

            # 접경은 전쟁 확률을 높이는 요인일 뿐, 전쟁을 강제로 발생시키지 않는다.
            if border:
                crowd_a = clamp(a["population"] / max(12_000 + len(a["territory"]) * 180, 1), 0, 1)
                crowd_b = clamp(b["population"] / max(12_000 + len(b["territory"]) * 180, 1), 0, 1)
                competition = (pa + pb) * 0.45 + (crowd_a + crowd_b) * 0.30
                if competition > 0.25:
                    change_relation(a, b, -random.uniform(0.10, 0.45) * competition)

            traded = trade_between(a, b, envs[a["id"]], envs[b["id"]])

            # 전쟁은 300년 이후, 일정 주기로 검사한다. 자원압력/군사력 차이가 크면 조금 더 자주 발생한다.
            # 접경은 보너스일 뿐 강제 전쟁이 아니며, 비접경국도 일정 거리 이내일 때만 후보가 된다.
            hostile_or_stressed = (
                rel["relation"] < 0
                or pa > 0.30
                or pb > 0.30
                or military_power(a) > military_power(b) * 1.35
                or military_power(b) > military_power(a) * 1.35
            )
            if year >= WAR_START_YEAR and year % WAR_CHECK_INTERVAL == 0 and ((not traded) or hostile_or_stressed):
                maybe_start_war(a, b, envs[a["id"]], envs[b["id"]])
                if not at_war(a, b):
                    maybe_start_war(b, a, envs[b["id"]], envs[a["id"]])


def extinct_civilization(civ, reason="인구 붕괴"):
    """문명이 생존 한계 이하로 내려가면 흔적 없이 게임 시스템에서 제거한다.

    civilizations 리스트의 슬롯 자체는 territory_owner의 국가 ID 인덱스를 보존하기 위해
    남겨 두지만, 살아 있는 국가로는 절대 취급되지 않는다.
    """
    if not civ.get("alive", True):
        return

    civ["alive"] = False
    civ["population"] = 0
    civ["food"] = 0.0
    civ["wealth"] = 0.0
    civ["status"] = "멸망"
    civ["trade_bonus"] = {k: 0.0 for k in civ.get("trade_bonus", {})}

    # 지도에서 영토를 완전히 제거한다.
    for idx in list(civ.get("territory", ())):
        if 0 <= idx < len(territory_owner) and territory_owner[idx] == civ["id"]:
            territory_owner[idx] = -1
    civ["territory"].clear()
    civ["frontier"].clear()

    # 멸망한 국가에 붙어 있던 전염병/전쟁 상태도 즉시 제거한다.
    active_epidemics[:] = [e for e in active_epidemics if e.get("civ_id") != civ["id"]]
    ended_wars = []
    remaining_wars = []
    for w in active_wars:
        if civ["id"] in (w.get("a"), w.get("b")):
            ended_wars.append(w)
        else:
            remaining_wars.append(w)
    active_wars[:] = remaining_wars

    for w in ended_wars:
        other_id = w["b"] if w["a"] == civ["id"] else w["a"]
        if 0 <= other_id < len(civilizations):
            other = civilizations[other_id]
            if other.get("alive", False):
                other["war_cooldown_until"] = max(other.get("war_cooldown_until", -9999), year + 5)
                event_history.append((year, f"{civ['name']} 멸망으로 {civ['name']}와 {other['name']} 전쟁 종료"))

    event_history.append((year, f"{civ['name']} 멸망 ({reason})"))


def check_extinctions():
    """300명 이하의 문명은 100명 같은 잔존 상태로 남지 않고 즉시 0명 처리한다."""
    for civ in civilizations:
        if civ.get("alive", True) and civ["population"] <= EXTINCTION_POPULATION:
            extinct_civilization(civ)


def simulate_civilizations():
    # 연간 변화량 초기화 + 전쟁 후유증 회복
    for civ in civilizations:
        civ["last_population_change"] = 0
        civ["last_wealth_change"] = 0.0
        civ["last_war_damage"] = 0.0
        if civ_alive(civ):
            current_war = active_war_for_civ(civ)
            if current_war is None:
                civ["peace_years"] = civ.get("peace_years", 0) + 1
                civ["war_fatigue"] = max(0.0, civ.get("war_fatigue", 0.0) - random.uniform(2.5, 4.5))
                civ["status"] = "회복 중" if civ["war_fatigue"] > 25 else "안정"
            else:
                civ["peace_years"] = 0
                civ["status"] = "⚔ 전쟁 중"
            for k in civ["trade_bonus"]:
                civ["trade_bonus"][k] *= 0.84

    apply_disaster_to_civilizations()
    update_epidemics()
    check_extinctions()

    for civ in civilizations:
        if not civ_alive(civ):
            continue

        env = get_civ_environment(civ)
        pop = civ["population"]
        intel = civ["intelligence"]
        medical = civ["medical"]
        war = active_war_for_civ(civ)
        fatigue = civ.get("war_fatigue", 0.0)

        # ===== 식량 =====
        food_factor = clamp((env["food"] / 100) + civ["trade_bonus"]["food"] * 0.18, 0, 1.6)
        water_factor = clamp(env["water"] / 80, 0.68, 1.20)
        intelligence_factor = 0.94 + intel / 360
        medical_factor = 0.98 + medical / 900
        raw_food_per_person = (0.94 + 0.34 * food_factor) * intelligence_factor * medical_factor * water_factor
        severe_resource_stress = (env["food"] < 22 or env["water"] < 16)
        normal_floor = 0.90 if severe_resource_stress else (1.03 + intel * 0.0007)
        food_per_person = max(raw_food_per_person, normal_floor)

        # 전쟁 중에는 농촌/수송/노동력이 망가져 생산량이 크게 떨어지고 군수 때문에 소비가 증가한다.
        if war is not None:
            war_prod_mult = clamp(0.79 - fatigue * 0.0032, 0.48, 0.79)
            war_cons_mult = 1.14 + min(fatigue, 100) * 0.0016
        else:
            # 전쟁 후에도 피로가 높으면 완전히 회복될 때까지 생산성이 낮다.
            war_prod_mult = clamp(1.0 - fatigue * 0.0018, 0.78, 1.0)
            war_cons_mult = 1.0

        food_production = pop * food_per_person * war_prod_mult
        food_consumption = pop * war_cons_mult
        old_food = civ["food"]
        civ["food"] = max(0.0, civ["food"] + food_production - food_consumption)
        civ["last_food_production"] = food_production
        civ["last_food_consumption"] = food_consumption

        available = old_food + food_production
        if available < food_consumption:
            shortage = clamp((food_consumption - available) / max(food_consumption, 1), 0, 1)
            # 기근 사망은 전쟁 직접 사망과 별도로 작동한다. 전쟁 피로가 높을수록 더 치명적이다.
            loss = 0.004 + 0.060 * shortage
            if war is not None:
                loss *= 1.15 + fatigue / 180
            loss = clamp(loss, 0, 0.11)
            old = civ["population"]
            civ["population"] = max(0, int(civ["population"] * (1 - loss)))
            civ["last_population_change"] += civ["population"] - old
            civ["status"] = "⚔ 전쟁·기근" if war is not None else "기근"

        pop = civ["population"]
        if pop <= EXTINCTION_POPULATION:
            continue

        storage_capacity = pop * (10.0 + civ["intelligence"] * 0.11)
        civ["food"] = min(civ["food"], storage_capacity)

        # ===== 경제 =====
        resource_value = (
            env["wood"] / 65 + env["iron"] / 90 + env["minerals"] / 110 + env["oil"] / 130
            + civ["trade_bonus"]["wood"] * 0.45
            + civ["trade_bonus"]["iron"] * 0.65
            + civ["trade_bonus"]["minerals"] * 0.55
            + civ["trade_bonus"]["oil"] * 0.55
        )
        resource_factor = clamp(0.78 + resource_value * 0.035, 0.75, 1.45)
        production = pop * (0.08 + intel / 900) * resource_factor
        maintenance = pop * (0.055 + medical / 3000)
        construction = civ["wealth"] * 0.003 if civ["wealth"] > 8_000 else 0

        if war is not None:
            production *= clamp(0.72 - fatigue * 0.0027, 0.42, 0.72)
            maintenance *= 1.35 + fatigue * 0.004
            construction *= 0.35
        elif fatigue > 0:
            production *= clamp(1.0 - fatigue * 0.0020, 0.80, 1.0)

        wealth_change = production - maintenance - construction
        civ["wealth"] = max(0.0, civ["wealth"] + wealth_change)
        civ["last_wealth_change"] = wealth_change

        # ===== 빈곤/기근 누적 =====
        food_per_capita = civ["food"] / max(pop, 1)
        wealth_per_capita = civ["wealth"] / max(pop, 1)
        if food_per_capita < 0.8:
            civ["famine_years"] = civ.get("famine_years", 0) + 1
        else:
            civ["famine_years"] = max(0, civ.get("famine_years", 0) - 2)

        if wealth_per_capita < 0.45:
            civ["poverty_years"] = civ.get("poverty_years", 0) + 1
        else:
            civ["poverty_years"] = max(0, civ.get("poverty_years", 0) - 1)

        # 장기간 빈곤과 기근이 겹치면 전투가 없어도 질병/영양실조/이주로 인구가 감소한다.
        collapse_loss = 0.0
        if civ["famine_years"] >= 3:
            collapse_loss += min(0.028, 0.004 + civ["famine_years"] * 0.0017)
        if civ["poverty_years"] >= 6:
            collapse_loss += min(0.020, 0.002 + civ["poverty_years"] * 0.0010)
        if civ["famine_years"] >= 7 and civ["poverty_years"] >= 10:
            collapse_loss += 0.018
        if collapse_loss > 0:
            old = civ["population"]
            civ["population"] = max(0, int(civ["population"] * (1 - clamp(collapse_loss, 0, 0.075))))
            civ["last_population_change"] += civ["population"] - old
            civ["status"] = "전쟁 후 붕괴" if fatigue > 30 else "기근·빈곤"
            pop = civ["population"]
            if pop <= EXTINCTION_POPULATION:
                continue

        # ===== 의료 =====
        ceiling = medical_historical_ceiling(year)
        food_security = clamp(civ["food"] / max(pop * 3, 1), 0, 1)
        wealth_security = clamp(civ["wealth"] / max(pop * 8, 1), 0, 1)
        if civ["medical"] < ceiling:
            catchup = clamp((ceiling - civ["medical"]) * 0.0025, 0, 0.12)
            medical_change = 0.018 + 0.018 * wealth_security + 0.012 * food_security + 0.012 * (intel / 100) + catchup
            if civ["wealth"] < pop * 0.8 or civ["food"] < pop:
                medical_change *= 0.35
            if war is not None:
                medical_change *= 0.35
            civ["medical"] = min(ceiling, civ["medical"] + medical_change)
        elif civ["medical"] > ceiling + 4:
            civ["medical"] -= 0.01
        civ["medical"] = clamp(civ["medical"], 0, 100)

        # ===== 지능 =====
        intelligence_change = 0.004
        if wealth_security > 0.55: intelligence_change += 0.008
        if food_security > 0.65: intelligence_change += 0.006
        if civ["medical"] > 55: intelligence_change += 0.006
        if civ["food"] < pop: intelligence_change -= 0.020
        if civ["wealth"] < pop * 0.5: intelligence_change -= 0.008
        if war is not None: intelligence_change -= 0.006
        civ["intelligence"] = clamp(civ["intelligence"] + clamp(intelligence_change, -0.08, 0.035), 0, 100)

        # ===== 인구 성장: 수용력 기반 강한 제어 =====
        food_security = clamp(civ["food"] / max(pop * 4, 1), 0, 1.2)
        wealth_security = clamp(civ["wealth"] / max(pop * 8, 1), 0, 1.1)
        growth = 0.0006 + 0.0018 * food_security + 0.0010 * (civ["medical"] / 100) + 0.0007 * wealth_security

        if war is not None:
            growth -= 0.014 + fatigue * 0.00008
        if civ["food"] < pop * 1.5:
            growth -= 0.007
        if civ["food"] < pop * 0.6:
            growth -= 0.020
        if civ["food"] < pop * 0.2:
            growth -= 0.035
        if civ["poverty_years"] > 8:
            growth -= 0.006

        for d in active_disasters:
            if d["type"] == "drought":
                dx = civ["x"] - d["x"]
                dy = civ["y"] - d["y"]
                if dx * dx + dy * dy <= d["radius"] ** 2:
                    growth += random.uniform(*DISASTER_DEFS["drought"]["growth_penalty"]) / 100
                    break

        # 실제 영토 크기와 그 영토의 자원을 기준으로 인구 수용력을 계산한다.
        carrying_capacity = estimated_carrying_capacity(civ, env)
        density_ratio = civ["population"] / max(carrying_capacity, 1)

        # 영토와 인구가 비례하도록 목표 밀도 주변에서 성장률을 강하게 조절한다.
        # 60~85%는 정상 범위, 90%부터 과밀 압력, 100% 초과는 확실한 감소.
        if density_ratio > 0.60:
            growth -= 0.0035 * ((density_ratio - 0.60) / 0.40)
        if density_ratio > 0.85:
            growth -= 0.012 * ((density_ratio - 0.85) / 0.15)
        if density_ratio > 1.0:
            growth -= 0.035 * min(density_ratio - 1.0, 1.5)
        if density_ratio > 1.20:
            growth -= 0.025 * min(density_ratio - 1.20, 1.2)

        # 반대로 영토만 지나치게 넓고 인구가 너무 적을 때는 약한 회복 여지를 주되,
        # 영토가 계속 더 늘어나는 것은 expand_territories()가 막는다.
        if density_ratio < 0.42 and food_security > 0.65 and wealth_security > 0.45 and war is None:
            growth += 0.0008

        growth = clamp(growth, -0.085, 0.0042)
        old = civ["population"]
        civ["population"] = max(0, int(civ["population"] * (1 + growth)))
        civ["last_population_change"] += civ["population"] - old

    check_extinctions()
    expand_territories()
    update_interactions()
    update_wars()
    check_extinctions()


def get_civilization_stats_text(civ):
    stage_id, stage_name = civilization_stage(civ)
    dev = development_level(civ) if civ_alive(civ) else 0
    war = active_war_for_civ(civ) if civ_alive(civ) else None
    lines = [
        f"단계: {stage_name}  발달도: {dev:.1f}",
        f"인구: {civ['population']:,}",
        f"지능: {civ['intelligence']:.1f}",
        f"의료: {civ['medical']:.1f} / 상한 {medical_historical_ceiling(year):.1f}",
        f"재산: {civ['wealth']:,.0f}",
        f"식량: {civ['food']:,.0f}",
        f"영토: {len(civ.get('territory', [])):,}칸 · 적정 영토: 약 {target_territory_size(civ):,}칸",
        f"인구 밀도: {civ['population'] / max(len(civ.get('territory', ())), 1):,.0f}명/칸 · 적정 {ideal_people_per_tile(civ):,.0f}명/칸",
        f"인구 수용력: 약 {estimated_carrying_capacity(civ):,.0f}명",
        f"군사력: {military_power(civ):.1f}/100 · 자원력: {territory_resource_strength(civ):.2f}",
        f"접경국: {len(bordering_countries(civ))}개",
        f"전쟁 조건: {war_lock_reason(civ)}",
        f"전쟁 범위: 약 {war_range(civ):.0f}칸",
        f"식량 생산/소비: {civ['last_food_production']:,.0f}/{civ['last_food_consumption']:,.0f}",
        f"빈곤 누적: {civ.get('poverty_years', 0)}년 · 기근 누적: {civ.get('famine_years', 0)}년",
        f"전쟁 피로: {civ.get('war_fatigue', 0):.0f}/100",
        f"상태: {civ['status']}",
    ]
    if war:
        opponent = war_opponent(civ, war)
        years = year - war["start_year"] + 1
        if opponent is not None:
            lines.append(f"⚔ 전쟁 중: {opponent['name']}와 {years}년차 / 최대 {war['max_years']}년")
    epi = epidemic_for(civ["id"])
    if epi:
        lines.append(f"전염병: {max(0, epi['end_year'] - year + 1)}년 남음")
    return lines


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ==================================================
# 해안 판정
# ==================================================

def compute_coast():

    global is_coast

    is_coast = [[False] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]

    for y in range(WORLD_HEIGHT):
        for x in range(WORLD_WIDTH):

            if world[y][x] == "water":
                continue

            found = False

            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):

                    if dx == 0 and dy == 0:
                        continue

                    nx, ny = x + dx, y + dy

                    if 0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT:
                        if world[ny][nx] == "water":
                            found = True
                            break

                if found:
                    break

            is_coast[y][x] = found


def get_terrain_key(x, y):

    t = world[y][x]

    if t == "water":
        return "water"

    if is_coast[y][x]:
        return "coast"

    return t


# ==================================================
# 산기슭 사막 판정 (구리 반암광상처럼 현실 지질 반영)
# ==================================================

def compute_desert_near_mountain(radius=6):

    global desert_near_mountain

    desert_near_mountain = [[False] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]

    for y in range(WORLD_HEIGHT):
        for x in range(WORLD_WIDTH):

            if world[y][x] != "desert":
                continue

            found = False

            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):

                    nx, ny = x + dx, y + dy

                    if 0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT:
                        if world[ny][nx] == "mountain":
                            found = True
                            break

                if found:
                    break

            desert_near_mountain[y][x] = found


# ==================================================
# 재해 관련 환경 계산 (화산지역/지진위험지역/강주변/폭풍위험해안/건조도)
# ==================================================

def compute_disaster_environment():

    global dryness_map, rainfall_map
    global is_volcano, earthquake_risk_tier
    global river_near1, river_near_big, storm_risk_coast

    dryness_map = [[0.0] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]
    rainfall_map = [[0.0] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]

    for y in range(WORLD_HEIGHT):
        for x in range(WORLD_WIDTH):

            m = moisture_map[y][x]
            t = temperature_map[y][x]

            dryness = 50 - m * 80 + (t - 15) * 1.2
            dryness_map[y][x] = clamp(dryness, 0, 100)
            rainfall_map[y][x] = clamp(100 - dryness_map[y][x], 0, 100)

    # 화산 (산의 2~5%)

    is_volcano = [[False] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]

    mountain_tiles = [
        (x, y) for y in range(WORLD_HEIGHT) for x in range(WORLD_WIDTH)
        if world[y][x] == "mountain"
    ]

    volcano_fraction = random.uniform(0.02, 0.05)
    volcano_count = int(len(mountain_tiles) * volcano_fraction)

    for x, y in random.sample(mountain_tiles, min(volcano_count, len(mountain_tiles))):
        is_volcano[y][x] = True

    # 지진 위험지역 (육지의 10~20%, 그중 30%는 고위험)

    earthquake_risk_tier = [[0] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]

    land_tiles = [
        (x, y) for y in range(WORLD_HEIGHT) for x in range(WORLD_WIDTH)
        if world[y][x] != "water"
    ]

    risk_fraction = random.uniform(0.10, 0.20)
    risk_count = int(len(land_tiles) * risk_fraction)
    risk_tiles = random.sample(land_tiles, min(risk_count, len(land_tiles)))

    high_count = int(len(risk_tiles) * 0.3)
    high_tiles = set(random.sample(risk_tiles, min(high_count, len(risk_tiles))))

    for x, y in risk_tiles:
        earthquake_risk_tier[y][x] = 2 if (x, y) in high_tiles else 1

    # 강 주변 / 큰 강 주변

    river_near1 = [[False] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]
    river_near_big = [[False] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]

    for y in range(WORLD_HEIGHT):
        for x in range(WORLD_WIDTH):

            if world[y][x] == "water":
                continue

            count1 = 0
            count2 = 0

            for dy in range(-2, 3):
                for dx in range(-2, 3):

                    nx, ny = x + dx, y + dy

                    if 0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT:
                        if world[ny][nx] == "river":
                            count2 += 1
                            if abs(dx) <= 1 and abs(dy) <= 1:
                                count1 += 1

            river_near1[y][x] = count1 > 0
            river_near_big[y][x] = count2 >= 3

    # 폭풍 위험 해안 (해안의 30%)

    storm_risk_coast = [[False] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]

    coast_tiles = [
        (x, y) for y in range(WORLD_HEIGHT) for x in range(WORLD_WIDTH)
        if is_coast[y][x]
    ]

    storm_count = int(len(coast_tiles) * 0.3)

    for x, y in random.sample(coast_tiles, min(storm_count, len(coast_tiles))):
        storm_risk_coast[y][x] = True


# ==================================================
# 재해별 해당 칸의 연간 발생확률 (문서 2~7번, 범위 중간값 사용)
# ==================================================

def get_tile_probability(dtype, x, y):

    t = world[y][x]

    if dtype == "flood":

        # 기본 0.3% / 최대 1%

        if t == "water":
            return 0

        if river_near_big[y][x]:
            return 0.009
        if river_near1[y][x]:
            return 0.007
        if t == "plain" or is_coast[y][x]:
            return 0.0045

        return 0.003

    if dtype == "drought":

        # 기본 0.3% / 최대 1%

        if t == "water":
            return 0

        if t == "desert":
            return 0.0088 if moisture_map[y][x] < -0.4 else 0.006

        if t == "plain":
            return 0.0027

        return 0.0012

    if dtype == "volcano":

        # 기본 0.005% / 최대 0.1% (훨씬 희귀해짐)

        return 0.00053 if is_volcano[y][x] else 0

    if dtype == "earthquake":

        # 표에서 변동 없음 (기본 0.2% / 최대 2%)

        if t == "water":
            return 0

        tier = earthquake_risk_tier[y][x]

        if tier == 2:
            return 0.016
        if tier == 1:
            return 0.0085

        return 0.002

    if dtype == "storm":

        # 기본 0.3% / 최대 1%

        if t == "water":
            return 0

        if is_coast[y][x]:
            return 0.0081 if storm_risk_coast[y][x] else 0.005

        if t == "plain":
            return 0.0027

        return 0.002

    if dtype == "fire":

        if t != "forest":
            return 0

        d = dryness_map[y][x]

        if d > 85:
            return 0.0175
        if d > 60:
            return 0.0115
        if d > 30:
            return 0.005

        return 0.002

    return 0


# ==================================================
# 재해 발생시키기
# ==================================================

def trigger_disaster(dtype, x, y):

    global active_disasters, event_history

    definition = DISASTER_DEFS[dtype]

    is_large = random.random() < definition["large_chance"]

    if is_large:
        radius = random.randint(*definition["large_radius"])
        duration = random.randint(*definition["large_duration"])
    else:
        radius = random.randint(*definition["radius"])
        duration = random.randint(*definition["duration"])

    severity_roll = random.random()

    if severity_roll < 0.6:
        severity_name, severity_mult = "약함", 0.5
    elif severity_roll < 0.9:
        severity_name, severity_mult = "보통", 1.0
    else:
        severity_name, severity_mult = "강함", 2.0

    effects = {}

    for resource, (lo, hi) in definition["effects"].items():
        pct = random.uniform(lo, hi) * severity_mult
        pct = max(pct, -0.95)
        effects[resource] = 1 + pct

    global disaster_event_serial
    start_year = year
    # duration=1이면 정확히 그 해 한 번만 지속한다.
    end_year = year + duration - 1
    disaster_event_serial += 1
    main_event_id = disaster_event_serial

    active_disasters.append({
        "event_id": main_event_id,
        "type": dtype, "x": x, "y": y, "radius": radius,
        "start_year": start_year, "end_year": end_year,
        "effects": effects, "severity": severity_name, "large": is_large
    })

    # 산불은 숲 밀도를 즉시 영구적으로 깎음 (연간 회복은 별도 진행)

    if dtype == "fire":

        dmg = random.randint(*definition["density_damage"])

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):

                nx, ny = x + dx, y + dy

                if not (0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT):
                    continue

                if world[ny][nx] != "forest":
                    continue

                if math.hypot(dx, dy) <= radius:
                    old_density = forest_density[ny][nx]
                    new_density = max(0, old_density - dmg)
                    forest_density[ny][nx] = new_density
                    # 산불로 숲 밀도가 줄면 실제 목재량도 함께 감소시킨다.
                    if old_density > 0:
                        wood_map[ny][nx] *= new_density / old_density

    # 홍수 / 화산의 추가 효과 (재해가 끝난 뒤 비옥도 상승)

    if "after_effect" in definition:

        after_duration = random.randint(*definition["after_duration"])

        after_effects = {
            r: 1 + random.uniform(lo, hi)
            for r, (lo, hi) in definition["after_effect"].items()
        }

        disaster_event_serial += 1
        after_start = end_year + 1
        active_disasters.append({
            "event_id": disaster_event_serial,
            "type": dtype + "_after", "x": x, "y": y, "radius": radius,
            "start_year": after_start, "end_year": after_start + after_duration - 1,
            "effects": after_effects, "severity": "", "large": False
        })

    size_label = "대형" if is_large else "일반"

    # 연도와 메시지를 따로 저장 (100년 건너뛰기 요약에서 연도별로 필요)
    event_history.append((
        year,
        f"{definition['name']} 발생 ({size_label}/{severity_name}) - ({x},{y})"
    ))



# ==================================================
# 매년 블록 단위로 재해 확률 굴리기
# ==================================================

def build_disaster_risk_pools():
    """재해 종류/확률별 후보 좌표를 캐시한다.
    기존 방식은 매년 6종 × 40,000칸을 다시 검사해 매우 느렸다.
    """
    global disaster_risk_pools
    pools = {}
    for dtype in DISASTER_TYPES:
        tier_groups = {}
        for y in range(WORLD_HEIGHT):
            for x in range(WORLD_WIDTH):
                p = get_tile_probability(dtype, x, y)
                if p > 0:
                    tier_groups.setdefault(p, []).append((x, y))
        pools[dtype] = list(tier_groups.items())
    disaster_risk_pools = pools


def rebuild_disaster_risk_type(dtype):
    """기후에 실제로 의존하는 재해만 부분 갱신한다. 현재는 산불 위험만 건조도 변화의 영향을 받는다."""
    tier_groups = {}
    for y in range(WORLD_HEIGHT):
        for x in range(WORLD_WIDTH):
            p = get_tile_probability(dtype, x, y)
            if p > 0:
                tier_groups.setdefault(p, []).append((x, y))
    disaster_risk_pools[dtype] = list(tier_groups.items())


def roll_disasters_for_year():
    # 위험 후보는 캐시에서 바로 꺼내므로 연도 진행이 훨씬 빠르다.
    if not disaster_risk_pools:
        build_disaster_risk_pools()

    for dtype in DISASTER_TYPES:
        for prob, tiles in disaster_risk_pools.get(dtype, ()):
            if tiles and random.random() < prob:
                x, y = random.choice(tiles)
                trigger_disaster(dtype, x, y)


# ==================================================
# 활성 재해 효과를 자원 배율 지도에 반영
# ==================================================

def recompute_multipliers():
    """활성 재해가 실제로 건드리는 칸만 저장한다.
    200×200×4 전체 배율맵을 매년 새로 만드는 비용을 없앤다.
    key는 y*WORLD_WIDTH+x 형태의 정수라 tuple보다도 가볍다.
    """
    global multiplier_maps

    multiplier_maps = {
        "food": {},
        "water": {},
        "wood": {},
        "mining": {}
    }

    for d in active_disasters:
        if not (d["start_year"] <= year <= d["end_year"]):
            continue

        cx, cy, radius = d["x"], d["y"], d["radius"]
        r2 = radius * radius

        y0 = max(0, cy - radius)
        y1 = min(WORLD_HEIGHT - 1, cy + radius)
        x0 = max(0, cx - radius)
        x1 = min(WORLD_WIDTH - 1, cx + radius)

        for ny in range(y0, y1 + 1):
            dy = ny - cy
            dy2 = dy * dy
            for nx in range(x0, x1 + 1):
                dx = nx - cx
                if dx * dx + dy2 > r2:
                    continue
                idx = ny * WORLD_WIDTH + nx
                for resource, mult in d["effects"].items():
                    target = multiplier_maps.get(resource)
                    if target is not None:
                        target[idx] = target.get(idx, 1.0) * mult


# ==================================================
# 1년 진행
# ==================================================

def advance_year():
    global year, active_disasters

    year += 1

    # 기후는 매우 느리게 변하므로 매년 4만 칸을 난수 갱신하지 않는다.
    # 여러 해에 한 번만 갱신하여 속도를 높이고, 급격한 잡음성 기후변화도 줄인다.
    if year % CLIMATE_UPDATE_INTERVAL == 0:
        for y in range(WORLD_HEIGHT):
            wrow = world[y]
            drow = dryness_map[y]
            rrow = rainfall_map[y]
            trow = temperature_map[y]
            frow = forest_density[y]
            for x in range(WORLD_WIDTH):
                if wrow[x] == "water":
                    continue
                drow[x] = clamp(drow[x] + random.uniform(-2.0, 2.0), 0, 100)
                rrow[x] = clamp(rrow[x] + random.uniform(-3.0, 3.0), 0, 100)
                trow[x] = clamp(trow[x] + random.uniform(-0.6, 0.6), -10, 45)
                if wrow[x] == "forest" and frow[x] < 100:
                    old = frow[x]
                    frow[x] = min(100, old + random.randint(2, 5))
                    if old > 0:
                        wood_map[y][x] *= frow[x] / old

    # 만료된 재해 제거
    active_disasters[:] = [d for d in active_disasters if d["end_year"] >= year]

    # 기후가 누적 변화한 뒤에만 위험 후보를 갱신한다.
    if year % RISK_REBUILD_INTERVAL == 0:
        rebuild_disaster_risk_type("fire")

    roll_disasters_for_year()
    recompute_multipliers()
    simulate_civilizations()

    # 로그가 끝없이 커져 메모리를 잡아먹지 않도록 제한한다.
    if len(event_history) > MAX_EVENT_HISTORY:
        del event_history[:-MAX_EVENT_HISTORY]


# ==================================================
# 여러 해를 한 번에 건너뛰고, 그동안 있었던 일을 모아서 반환
# ==================================================

def _event_priority(msg):
    if "전쟁" in msg:
        return 0
    if "멸망" in msg:
        return 1
    if "전염병" in msg:
        return 2
    if "무역" in msg:
        return 3
    return 4


def _civilization_snapshot():
    return {
        c["id"]: {
            "name": c["name"],
            "population": c["population"],
            "territory": len(c.get("territory", ())),
            "alive": civ_alive(c),
        }
        for c in civilizations
    }


def skip_years(n):
    start_year = year
    start_snapshot = _civilization_snapshot()
    start_log_index = len(event_history)

    for _ in range(n):
        advance_year()

    # 100년 동안 새로 생긴 로그만 사용한다. 전쟁/멸망/전염병을 재해보다 먼저 보여준다.
    period_events = list(event_history[start_log_index:])
    period_events.sort(key=lambda item: (_event_priority(item[1]), item[0]))

    if not any("전쟁" in msg for _, msg in period_events):
        period_events.insert(0, (year, "[전쟁] 이 기간에는 국가 간 전쟁이 없었습니다."))

    country_changes = []
    for civ in civilizations:
        before = start_snapshot[civ["id"]]
        after_pop = civ["population"]
        after_territory = len(civ.get("territory", ()))
        if before["population"] > 0:
            pop_pct = (after_pop - before["population"]) / before["population"] * 100
        else:
            pop_pct = 0.0
        if not civ_alive(civ):
            line = f"{civ['name']}: 멸망 | 인구 {before['population']:,}→0 | 영토 {before['territory']}→0칸"
        else:
            line = (
                f"{civ['name']}: 인구 {before['population']:,}→{after_pop:,} "
                f"({pop_pct:+.1f}%) | 영토 {before['territory']}→{after_territory}칸"
            )
        country_changes.append(line)

    return {
        "start_year": start_year,
        "end_year": year,
        "events": period_events,
        "countries": country_changes,
    }


# ==================================================
# 재생 자원 생성
# ==================================================

def generate_renewable_resources():

    global food_map, water_map, wood_map, forest_density

    food_map = [[0.0] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]
    water_map = [[0.0] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]
    wood_map = [[0.0] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]
    forest_density = [[0] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]

    for y in range(WORLD_HEIGHT):
        for x in range(WORLD_WIDTH):

            key = get_terrain_key(x, y)
            base = TERRAIN_BASE_RESOURCES[key]

            food_map[y][x] = round(base["food"] * random.uniform(0.7, 1.3), 1)
            water_map[y][x] = round(base["water"] * random.uniform(0.7, 1.3), 1)

            if world[y][x] == "forest":

                density = random.randint(40, 100)
                forest_density[y][x] = density

                wood_map[y][x] = round(
                    base["wood"] * (density / 100) * random.uniform(0.85, 1.15), 1
                )

            else:

                wood_map[y][x] = round(base["wood"] * random.uniform(0.7, 1.3), 1)


def pick_grade(grade_table):

    r = random.random()
    cumulative = 0.0

    for low, high, prob in grade_table:

        cumulative += prob

        if r <= cumulative:
            return random.randint(low, high)

    low, high, _ = grade_table[-1]

    return random.randint(low, high)


def generate_deposit_map(resource_key, count_range, grade_table, allow_water=False):

    deposit_map = [[0] * WORLD_WIDTH for _ in range(WORLD_HEIGHT)]

    coords = []
    weights = []

    for y in range(WORLD_HEIGHT):
        for x in range(WORLD_WIDTH):

            if world[y][x] == "water" and not allow_water:
                continue

            key = get_terrain_key(x, y)
            base = TERRAIN_BASE_RESOURCES[key][resource_key]

            if base > 0:

                if (
                    resource_key in ("iron", "minerals")
                    and world[y][x] == "desert"
                    and desert_near_mountain[y][x]
                ):
                    base *= 2.5

                coords.append((x, y))
                weights.append(base)

    if not coords:
        return deposit_map

    count = random.randint(*count_range)

    raw_picks = random.choices(coords, weights=weights, k=count * 25)

    centers = []

    for x, y in raw_picks:

        if len(centers) >= count:
            break

        too_close = False

        for cx, cy, _ in centers:
            if math.hypot(x - cx, y - cy) < 6:
                too_close = True
                break

        if too_close:
            continue

        reserve = pick_grade(grade_table)

        centers.append((x, y, reserve))

    for cx, cy, reserve in centers:

        radius = max(3, min(9, int(3 + math.log10(max(reserve, 10)) * 1.6)))

        peak = reserve / (radius * radius)

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):

                nx, ny = cx + dx, cy + dy

                if not (0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT):
                    continue

                if world[ny][nx] == "water" and not allow_water:
                    continue

                dist = math.hypot(dx, dy)

                if dist > radius:
                    continue

                falloff = 1 - (dist / radius)

                amount = int(peak * falloff * radius)

                if amount > 0:
                    deposit_map[ny][nx] += amount

    return deposit_map


def generate_resources():

    global iron_map, mineral_map, oil_map, resource_max
    global year, active_disasters, event_history, disaster_event_serial

    compute_coast()
    compute_desert_near_mountain()
    compute_disaster_environment()

    year = 0
    active_disasters = []
    event_history = []
    disaster_event_serial = 0

    generate_renewable_resources()

    iron_map = generate_deposit_map("iron", IRON_ZONE_COUNT, IRON_GRADES, allow_water=False)
    mineral_map = generate_deposit_map("minerals", MINERAL_ZONE_COUNT, MINERAL_GRADES, allow_water=False)
    oil_map = generate_deposit_map("oil", OIL_ZONE_COUNT, OIL_GRADES, allow_water=True)

    def safe_max(grid):
        m = max(max(row) for row in grid)
        return m if m > 0 else 1

    resource_max = {
        "food": safe_max(food_map),
        "water": safe_max(water_map),
        "wood": safe_max(wood_map),
        "iron": safe_max(iron_map),
        "minerals": safe_max(mineral_map),
        "oil": safe_max(oil_map)
    }

    recompute_multipliers()
    build_disaster_risk_pools()
    generate_civilizations()


def get_resource_value(mode, x, y):
    idx = y * WORLD_WIDTH + x

    if mode == "food":
        return round(food_map[y][x] * multiplier_maps["food"].get(idx, 1.0), 1)

    if mode == "water":
        return round(water_map[y][x] * multiplier_maps["water"].get(idx, 1.0), 1)

    if mode == "wood":
        return round(wood_map[y][x] * multiplier_maps["wood"].get(idx, 1.0), 1)

    mining_mult = multiplier_maps["mining"].get(idx, 1.0)

    if mode == "iron":
        return round(iron_map[y][x] * mining_mult)

    if mode == "minerals":
        return round(mineral_map[y][x] * mining_mult)

    if mode == "oil":
        return round(oil_map[y][x] * mining_mult)

    return 0



def lerp_color(c1, c2, t):

    t = clamp(t, 0.0, 1.0)

    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t)
    )


# ==================================================
# 랜덤 세계(지형) 생성
# ==================================================

def generate_world():

    global world
    global elevation_map
    global temperature_map
    global moisture_map
    global seed

    seed = random.randrange(1, 1000000000)

    noise = OpenSimplex(seed=seed)

    world = []
    elevation_map = []
    temperature_map = []
    moisture_map = []


    for y in range(WORLD_HEIGHT):

        terrain_row = []
        elevation_row = []
        temp_row = []
        moisture_row = []


        for x in range(WORLD_WIDTH):

            warp_x = noise.noise2(
                x / WORLD_WIDTH * 3.0 + 3000,
                y / WORLD_HEIGHT * 3.0 + 3000
            ) * 14

            warp_y = noise.noise2(
                x / WORLD_WIDTH * 3.0 + 4000,
                y / WORLD_HEIGHT * 3.0 + 4000
            ) * 10

            wx = x + warp_x
            wy = y + warp_y

            center_x = WORLD_WIDTH / 2
            center_y = WORLD_HEIGHT / 2

            dx = (x - center_x) / (WORLD_WIDTH * 0.50)
            dy = (y - center_y) / (WORLD_HEIGHT * 0.43)

            distance = math.sqrt(dx * dx + dy * dy)

            continent = 0.48 - distance

            large = noise.noise2(
                wx / WORLD_WIDTH * 2.4,
                wy / WORLD_HEIGHT * 2.4
            )

            medium = noise.noise2(
                wx / WORLD_WIDTH * 6.0 + 100,
                wy / WORLD_HEIGHT * 6.0 + 100
            )

            small = noise.noise2(
                wx / WORLD_WIDTH * 14.0 + 200,
                wy / WORLD_HEIGHT * 14.0 + 200
            )

            elevation = (
                continent * 0.72
                + large * 0.42
                + medium * 0.28
                + small * 0.14
            )

            if distance < 0.95 and medium < -0.25 and large < 0.15:
                elevation -= 0.28

            bay_noise = noise.noise2(
                x / WORLD_WIDTH * 2.2 + 700,
                y / WORLD_HEIGHT * 2.2 + 700
            )

            if distance < 0.9 and bay_noise < -0.55:
                elevation -= 0.30

            island_noise = noise.noise2(
                x / WORLD_WIDTH * 9.0 + 500,
                y / WORLD_HEIGHT * 9.0 + 500
            )

            if distance > 0.72 and distance < 1.35 and island_noise > 0.48:
                elevation += 0.42

            elevation_row.append(elevation)

            latitude_ratio = y / (WORLD_HEIGHT - 1)

            base_temperature = 40 - 100 * abs(latitude_ratio - 0.5)

            climate_noise = noise.noise2(
                x / WORLD_WIDTH * 2.5 + 1000,
                y / WORLD_HEIGHT * 2.5 + 1000
            )

            temperature = base_temperature + climate_noise * 10 - elevation * 5
            temperature = max(-10, min(45, temperature))

            temp_row.append(temperature)

            moisture = noise.noise2(
                x / WORLD_WIDTH * 3.5 + 2000,
                y / WORLD_HEIGHT * 3.5 + 2000
            )

            moisture_row.append(moisture)

            mountain_noise = noise.noise2(
                x / WORLD_WIDTH * 3.0 + 1500,
                y / WORLD_HEIGHT * 3.0 + 1500
            )

            if elevation < -0.22:
                terrain = "water"
            elif elevation > 0.18 and mountain_noise > 0.20:
                terrain = "mountain"
            elif temperature > 26 and moisture < -0.15:
                terrain = "desert"
            elif moisture > 0.05:
                terrain = "forest"
            else:
                terrain = "plain"

            terrain_row.append(terrain)

        world.append(terrain_row)
        elevation_map.append(elevation_row)
        temperature_map.append(temp_row)
        moisture_map.append(moisture_row)

    create_rivers()
    generate_resources()


# ==================================================
# 강 생성
# ==================================================

def create_rivers():

    river_count = random.randint(8, 14)

    mountain_candidates = []

    for y in range(5, WORLD_HEIGHT - 5):
        for x in range(5, WORLD_WIDTH - 5):
            if world[y][x] == "mountain" and elevation_map[y][x] > 0.25:
                mountain_candidates.append((x, y))

    if not mountain_candidates:
        return

    random.shuffle(mountain_candidates)

    used_starts = []

    for start in mountain_candidates:

        if len(used_starts) >= river_count:
            break

        sx, sy = start

        too_close = False

        for ux, uy in used_starts:
            if math.sqrt((sx - ux) ** 2 + (sy - uy) ** 2) < 18:
                too_close = True
                break

        if too_close:
            continue

        used_starts.append(start)

        x, y = sx, sy
        visited = set()

        for step in range(400):

            if x < 1 or x >= WORLD_WIDTH - 1 or y < 1 or y >= WORLD_HEIGHT - 1:
                break

            if (x, y) in visited:
                break

            visited.add((x, y))

            if world[y][x] == "water":
                break

            world[y][x] = "river"

            neighbors = []

            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:

                    if dx == 0 and dy == 0:
                        continue

                    nx = x + dx
                    ny = y + dy

                    if nx < 1 or nx >= WORLD_WIDTH - 1 or ny < 1 or ny >= WORLD_HEIGHT - 1:
                        continue

                    if (nx, ny) in visited:
                        continue

                    drop = elevation_map[y][x] - elevation_map[ny][nx]

                    neighbors.append((drop, nx, ny))

            if not neighbors:
                break

            neighbors.sort(reverse=True)

            best_drop = neighbors[0][0]

            if best_drop > 0:
                _, x, y = neighbors[0]
            else:
                choices = neighbors[:min(3, len(neighbors))]
                _, x, y = random.choice(choices)


# ==================================================
# 최초 세계 생성
# ==================================================

generate_world()


# ==================================================
# 카메라
# ==================================================

camera_x = 0
camera_y = 0

zoom = 1.0

MIN_ZOOM = 0.2
MAX_ZOOM = 5.0

dragging = False
last_mouse_pos = None

overlay_mode = None

auto_play = False
last_auto_tick = 0
AUTO_TICK_MS = 16

show_summary = False
summary_entries = []
summary_country_changes = []
summary_range = (0, 0)


# ==================================================
# 글꼴
# ==================================================

font = pygame.font.SysFont("malgungothic", 19)
small_font = pygame.font.SysFont("malgungothic", 14)
title_font = pygame.font.SysFont("malgungothic", 22, bold=True)


def draw_wrapped_text(surface, text, use_font, color, x, y, max_width, line_height=None, max_lines=None):
    """패널 밖으로 글자가 튀어나가지 않도록 한글/공백 기준 자동 줄바꿈."""
    if line_height is None:
        line_height = use_font.get_linesize() + 1
    text = str(text)
    if not text:
        return y + line_height

    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if use_font.size(candidate)[0] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        # 한 단어가 폭보다 긴 경우 글자 단위로 자른다.
        piece = ""
        for ch in word:
            test = piece + ch
            if use_font.size(test)[0] <= max_width:
                piece = test
            else:
                if piece:
                    lines.append(piece)
                piece = ch
        current = piece
    if current:
        lines.append(current)

    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            last = lines[-1]
            while last and use_font.size(last + "…")[0] > max_width:
                last = last[:-1]
            lines[-1] = last + "…"

    for line in lines:
        surface.blit(use_font.render(line, True, color), (x, y))
        y += line_height
    return y


def get_alive_civilizations_sorted():
    alive = [c for c in civilizations if civ_alive(c)]
    alive.sort(key=lambda c: len(c.get("territory", ())), reverse=True)
    return alive


def territory_share_text(civ):
    total = sum(len(c.get("territory", ())) for c in civilizations if civ_alive(c))
    size = len(civ.get("territory", ()))
    pct = (size / total * 100) if total else 0.0
    return f"{size:,}칸 ({pct:.1f}%)"


# ==================================================
# 게임 루프
# ==================================================

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # 요약 화면이 떠 있을 때는 아무 키/클릭이나 누르면 닫기만 함

        elif show_summary and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            show_summary = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_r:
                generate_world()

            elif event.key == pygame.K_t:
                advance_year()

            elif event.key == pygame.K_p:
                auto_play = not auto_play

            elif event.key == pygame.K_f:
                summary = skip_years(100)
                summary_entries = summary["events"]
                summary_country_changes = summary["countries"]
                summary_range = (summary["start_year"], summary["end_year"])
                show_summary = True
                auto_play = False

            elif event.key == pygame.K_0:
                overlay_mode = None

            # 영토 보기: 윗줄 7, 숫자패드 7, G 모두 지원
            elif event.key in (pygame.K_7, pygame.K_KP7, pygame.K_g):
                overlay_mode = "territory"

            elif event.key in OVERLAY_KEYS:
                overlay_mode = OVERLAY_KEYS[event.key]

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:
                dragging = True
                last_mouse_pos = pygame.mouse.get_pos()

        elif event.type == pygame.MOUSEBUTTONUP:

            if event.button == 1:
                dragging = False

        elif event.type == pygame.MOUSEMOTION:

            if dragging:

                mouse_x, mouse_y = pygame.mouse.get_pos()
                old_x, old_y = last_mouse_pos

                camera_x -= (mouse_x - old_x)
                camera_y -= (mouse_y - old_y)

                last_mouse_pos = (mouse_x, mouse_y)

        elif event.type == pygame.MOUSEWHEEL:

            mouse_x, mouse_y = pygame.mouse.get_pos()

            if mouse_x >= MAP_WIDTH:
                continue

            old_tile_size = BASE_TILE_SIZE * zoom

            world_x = (camera_x + mouse_x) / old_tile_size
            world_y = (camera_y + mouse_y) / old_tile_size

            if event.y > 0:
                zoom *= 1.2
            elif event.y < 0:
                zoom /= 1.2

            zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))

            new_tile_size = BASE_TILE_SIZE * zoom

            camera_x = world_x * new_tile_size - mouse_x
            camera_y = world_y * new_tile_size - mouse_y


    if auto_play:
        now = pygame.time.get_ticks()
        if now - last_auto_tick >= AUTO_TICK_MS:
            for _ in range(AUTO_YEARS_PER_TICK):
                advance_year()
            last_auto_tick = now


    keys = pygame.key.get_pressed()
    move_speed = 10 / zoom

    if keys[pygame.K_w] or keys[pygame.K_UP]:
        camera_y -= move_speed
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        camera_y += move_speed
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        camera_x -= move_speed
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        camera_x += move_speed


    tile_size = BASE_TILE_SIZE * zoom

    world_pixel_width = WORLD_WIDTH * tile_size
    world_pixel_height = WORLD_HEIGHT * tile_size

    max_camera_x = max(0, world_pixel_width - MAP_WIDTH)
    max_camera_y = max(0, world_pixel_height - HEIGHT)

    camera_x = max(0, min(camera_x, max_camera_x))
    camera_y = max(0, min(camera_y, max_camera_y))


    mouse_x, mouse_y = pygame.mouse.get_pos()
    hover_tile_x = -1
    hover_tile_y = -1
    hovered_civ = None
    hovered_civ_id = -1
    if 0 <= mouse_x < MAP_WIDTH and 0 <= mouse_y < HEIGHT:
        hover_tile_x = int((camera_x + mouse_x) / tile_size)
        hover_tile_y = int((camera_y + mouse_y) / tile_size)
        if 0 <= hover_tile_x < WORLD_WIDTH and 0 <= hover_tile_y < WORLD_HEIGHT:
            hovered_civ = find_civilization_at(hover_tile_x, hover_tile_y)
            if hovered_civ is not None:
                hovered_civ_id = hovered_civ["id"]


    # 안전장치: 어떤 계산 경로에서든 생존 한계 이하가 된 국가는
    # 다음 화면에 100명/200명짜리 유령 국가로 남지 않게 즉시 정리한다.
    check_extinctions()

    screen.fill((220, 220, 220))


    start_x = max(0, int(camera_x / tile_size))
    end_x = min(WORLD_WIDTH, int((camera_x + MAP_WIDTH) / tile_size) + 1)

    start_y = max(0, int(camera_y / tile_size))
    end_y = min(WORLD_HEIGHT, int((camera_y + HEIGHT) / tile_size) + 1)


    if overlay_mode is None:

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):

                terrain = world[y][x]
                color = TERRAIN_COLORS[terrain]
                owner = territory_owner[y * WORLD_WIDTH + x]
                if 0 <= owner < len(civilizations) and civ_alive(civilizations[owner]):
                    color = lerp_color(color, civilizations[owner]["color"], 0.30)

                screen_x = x * tile_size - camera_x
                screen_y = y * tile_size - camera_y

                pygame.draw.rect(
                    screen, color,
                    (screen_x, screen_y, tile_size + 1, tile_size + 1)
                )

    elif overlay_mode == "territory":

        neutral_land = (95, 95, 100)
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):

                terrain = world[y][x]
                idx = y * WORLD_WIDTH + x
                owner = territory_owner[idx]

                if terrain == "water":
                    color = (32, 74, 155)
                elif owner < 0 or owner >= len(civilizations) or not civ_alive(civilizations[owner]):
                    color = lerp_color(TERRAIN_COLORS[terrain], neutral_land, 0.55)
                else:
                    civ_color = civilizations[owner]["color"]
                    if hovered_civ_id >= 0:
                        if owner == hovered_civ_id:
                            color = lerp_color(TERRAIN_COLORS[terrain], civ_color, 0.96)
                        else:
                            dimmed = lerp_color(TERRAIN_COLORS[terrain], civ_color, 0.55)
                            color = lerp_color(dimmed, (45, 45, 50), 0.45)
                    else:
                        color = lerp_color(TERRAIN_COLORS[terrain], civ_color, 0.94)

                screen_x = x * tile_size - camera_x
                screen_y = y * tile_size - camera_y

                pygame.draw.rect(
                    screen, color,
                    (screen_x, screen_y, tile_size + 1, tile_size + 1)
                )

    else:

        base_low = (35, 35, 40)
        high_color = OVERLAY_COLORS[overlay_mode]
        max_value = resource_max[overlay_mode]

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):

                if world[y][x] == "water" and overlay_mode not in ("food", "oil"):
                    color = (25, 55, 100)
                else:
                    value = get_resource_value(overlay_mode, x, y)
                    t = value / max_value if max_value else 0
                    color = lerp_color(base_low, high_color, t)

                owner = territory_owner[y * WORLD_WIDTH + x]
                if 0 <= owner < len(civilizations) and civ_alive(civilizations[owner]):
                    color = lerp_color(color, civilizations[owner]["color"], 0.18)

                screen_x = x * tile_size - camera_x
                screen_y = y * tile_size - camera_y

                pygame.draw.rect(
                    screen, color,
                    (screen_x, screen_y, tile_size + 1, tile_size + 1)
                )


    # ==================================================
    # 국가 영토 국경선 표시
    # ==================================================
    if tile_size >= 2.5:
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                idx = y * WORLD_WIDTH + x
                owner = territory_owner[idx]
                if owner < 0 or owner >= len(civilizations) or not civ_alive(civilizations[owner]):
                    continue
                sx = x * tile_size - camera_x
                sy = y * tile_size - camera_y
                bc = civilizations[owner]["color"]
                # 이웃 영토와 소유자가 다를 때만 해당 변을 그려 깔끔한 국경 생성.
                if x == 0 or territory_owner[idx - 1] != owner:
                    pygame.draw.line(screen, bc, (sx, sy), (sx, sy + tile_size), 2 if overlay_mode == "territory" else 1)
                if x == WORLD_WIDTH - 1 or territory_owner[idx + 1] != owner:
                    pygame.draw.line(screen, bc, (sx + tile_size, sy), (sx + tile_size, sy + tile_size), 2 if overlay_mode == "territory" else 1)
                if y == 0 or territory_owner[idx - WORLD_WIDTH] != owner:
                    pygame.draw.line(screen, bc, (sx, sy), (sx + tile_size, sy), 2 if overlay_mode == "territory" else 1)
                if y == WORLD_HEIGHT - 1 or territory_owner[idx + WORLD_WIDTH] != owner:
                    pygame.draw.line(screen, bc, (sx, sy + tile_size), (sx + tile_size, sy + tile_size), 2 if overlay_mode == "territory" else 1)


    # 영토 모드가 켜졌는지 화면에서 바로 확인할 수 있는 표시
    if overlay_mode == "territory":
        badge_text = title_font.render("영토 모드 ON  [7 / 숫자패드7 / G]", True, (255, 255, 255))
        badge_w = badge_text.get_width() + 20
        pygame.draw.rect(screen, (25, 25, 30), (12, 12, badge_w, 36))
        pygame.draw.rect(screen, (245, 210, 90), (12, 12, badge_w, 36), 2)
        screen.blit(badge_text, (22, 18))

    # ==================================================
    # 활성 재해 마커 표시 (지도 위에 원으로)
    # ==================================================

    screen.set_clip(pygame.Rect(0, 0, MAP_WIDTH, HEIGHT))

    for d in active_disasters:

        if not (d["start_year"] <= year <= d["end_year"]):
            continue

        if d["type"].endswith("_after"):
            continue

        base_type = d["type"]

        cx = d["x"] * tile_size - camera_x
        cy = d["y"] * tile_size - camera_y
        r_px = d["radius"] * tile_size

        if cx + r_px < 0 or cx - r_px > MAP_WIDTH or cy + r_px < 0 or cy - r_px > HEIGHT:
            continue

        color = DISASTER_DEFS[base_type]["color"]

        pygame.draw.circle(screen, color, (int(cx), int(cy)), max(2, int(r_px)), 2)

        label = small_font.render(DISASTER_DEFS[base_type]["name"], True, color)
        screen.blit(label, (cx - label.get_width() / 2, cy - 8))

    screen.set_clip(None)

    # ==================================================
    # 진행 중인 전쟁 표시
    # ==================================================
    screen.set_clip(pygame.Rect(0, 0, MAP_WIDTH, HEIGHT))
    war_banner_y = 12
    for w in active_wars:
        a = civilizations[w["a"]]
        b = civilizations[w["b"]]
        if not (civ_alive(a) and civ_alive(b)):
            continue
        ax = a["x"] * tile_size - camera_x
        ay = a["y"] * tile_size - camera_y
        bx = b["x"] * tile_size - camera_x
        by = b["y"] * tile_size - camera_y
        pulse = 2 + ((pygame.time.get_ticks() // 280) % 2)
        pygame.draw.line(screen, (230, 55, 55), (int(ax), int(ay)), (int(bx), int(by)), pulse)
        years = year - w["start_year"] + 1
        banner_text = f"⚔ 전쟁 중: {a['name']} vs {b['name']} · {years}년차/{w['max_years']}년"
        banner = small_font.render(banner_text, True, (255, 235, 235))
        bw = banner.get_width() + 16
        pygame.draw.rect(screen, (105, 24, 24), (12, war_banner_y - 3, bw, banner.get_height() + 6))
        pygame.draw.rect(screen, (245, 105, 90), (12, war_banner_y - 3, bw, banner.get_height() + 6), 1)
        screen.blit(banner, (20, war_banner_y))
        war_banner_y += 24
    screen.set_clip(None)

    # ==================================================
    # 문명/국가 본거지 표시
    # ==================================================
    screen.set_clip(pygame.Rect(0, 0, MAP_WIDTH, HEIGHT))
    for civ in civilizations:
        if not civ_alive(civ):
            continue
        cx = civ["x"] * tile_size - camera_x
        cy = civ["y"] * tile_size - camera_y
        if -40 <= cx <= MAP_WIDTH + 40 and -40 <= cy <= HEIGHT + 40:
            stage_id, stage_name = civilization_stage(civ)
            r = max(3, int(tile_size * (0.48 + min(stage_id, 5) * 0.05)))
            pygame.draw.circle(screen, civ["color"], (int(cx), int(cy)), r)
            pygame.draw.circle(screen, (255, 255, 255), (int(cx), int(cy)), r, 1)
            war_flag = "⚔ " if active_war_for_civ(civ) is not None else ""
            display_name = war_flag + civ["name"] + (" 부족" if stage_id < 2 else "")
            display_name += f" · {len(civ.get('territory', ())):,}칸"
            label = small_font.render(display_name, True, (245, 245, 245))
            lx = int(cx - label.get_width() / 2)
            ly = int(cy - r - 19)
            pygame.draw.rect(screen, (35, 35, 40), (lx - 4, ly - 2, label.get_width() + 8, label.get_height() + 4))
            pygame.draw.rect(screen, civ["color"], (lx - 4, ly - 2, label.get_width() + 8, label.get_height() + 4), 1)
            screen.blit(label, (lx, ly))
    screen.set_clip(None)


    # ==================================================
    # 오른쪽 정보 패널
    # ==================================================

    pygame.draw.rect(screen, (245, 245, 245), (MAP_WIDTH, 0, INFO_WIDTH, HEIGHT))
    pygame.draw.line(screen, (100, 100, 100), (MAP_WIDTH, 0), (MAP_WIDTH, HEIGHT), 2)

    title = title_font.render("세계 정보", True, (20, 20, 20))
    screen.blit(title, (MAP_WIDTH + 20, 14))

    seed_text = small_font.render(f"Seed: {seed}   {year}년", True, (70, 70, 70))
    screen.blit(seed_text, (MAP_WIDTH + 20, 44))

    zoom_text = small_font.render(f"확대: {zoom:.2f}x", True, (30, 30, 30))
    screen.blit(zoom_text, (MAP_WIDTH + 20, 62))

    mode_label = "지형" if overlay_mode is None else ("국가 영토" if overlay_mode == "territory" else f"자원: {OVERLAY_NAMES[overlay_mode]}")
    mode_text = font.render(mode_label, True, (20, 20, 90))
    screen.blit(mode_text, (MAP_WIDTH + 20, 82))

    panel_text_width = INFO_WIDTH - 40
    control_y = 106
    control_y = draw_wrapped_text(screen, "WASD/방향키/드래그: 이동 · 휠: 확대 · R: 새 세계", small_font, (60, 60, 60), MAP_WIDTH + 20, control_y, panel_text_width, 17)
    control_y = draw_wrapped_text(screen, "0: 지형 · 1~6: 자원 · 7/숫자패드7/G: 영토 · T: 1년 · P: 자동진행 · F: 100년", small_font, (60, 60, 60), MAP_WIDTH + 20, control_y, panel_text_width, 17)
    active_disaster_count = sum(1 for d in active_disasters if not d['type'].endswith('_after') and d['start_year'] <= year <= d['end_year'])
    control_y = draw_wrapped_text(
        screen,
        f"자동진행: {'ON' if auto_play else 'OFF'} ({AUTO_YEARS_PER_TICK}년/틱) · 활성 재해: {active_disaster_count}개",
        small_font, (30, 90, 30) if auto_play else (90, 30, 30),
        MAP_WIDTH + 20, control_y + 2, panel_text_width, 17
    )


    # ==================================================
    # 범례
    # ==================================================

    legend_y = control_y + 8

    if overlay_mode is None:

        legend_title = font.render("지형", True, (20, 20, 20))
        screen.blit(legend_title, (MAP_WIDTH + 20, legend_y))
        legend_y += 24

        for terrain, color in TERRAIN_COLORS.items():

            pygame.draw.rect(screen, color, (MAP_WIDTH + 20, legend_y, 16, 16))
            pygame.draw.rect(screen, (80, 80, 80), (MAP_WIDTH + 20, legend_y, 16, 16), 1)

            name_text = small_font.render(TERRAIN_NAMES[terrain], True, (30, 30, 30))
            screen.blit(name_text, (MAP_WIDTH + 42, legend_y + 1))

            legend_y += 20

    elif overlay_mode == "territory":

        legend_title = font.render("국가 영토 (7키)", True, (20, 20, 20))
        screen.blit(legend_title, (MAP_WIDTH + 20, legend_y))
        legend_y += 22
        hint_color = (70, 70, 70)
        legend_y = draw_wrapped_text(screen, "영토 모드에서는 각 나라의 실제 점유 지역이 진하게 보입니다. 마우스를 영토 위에 올리면 그 나라를 더 밝게 강조합니다.", small_font, hint_color, MAP_WIDTH + 20, legend_y, INFO_WIDTH - 40, 16, max_lines=3) + 6

        for civ in get_alive_civilizations_sorted():
            if legend_y > 220:
                break
            pygame.draw.rect(screen, civ["color"], (MAP_WIDTH + 20, legend_y, 16, 16))
            pygame.draw.rect(screen, (70, 70, 70), (MAP_WIDTH + 20, legend_y, 16, 16), 1)
            label = f"{civ['name']} - {territory_share_text(civ)}"
            legend_y = draw_wrapped_text(screen, label, small_font, (30, 30, 30), MAP_WIDTH + 42, legend_y + 1, INFO_WIDTH - 64, 16, max_lines=2)
            legend_y += 4

    else:

        legend_title = font.render("자원 (숫자키)", True, (20, 20, 20))
        screen.blit(legend_title, (MAP_WIDTH + 20, legend_y))
        legend_y += 24

        for i, key in enumerate(["food", "water", "wood", "iron", "minerals", "oil"], start=1):

            active = (key == overlay_mode)
            box_color = OVERLAY_COLORS[key]

            pygame.draw.rect(screen, box_color, (MAP_WIDTH + 20, legend_y, 16, 16))

            border_color = (0, 0, 0) if active else (120, 120, 120)
            pygame.draw.rect(screen, border_color, (MAP_WIDTH + 20, legend_y, 16, 16), 2 if active else 1)

            label = f"{i}. {OVERLAY_NAMES[key]}"
            name_text = small_font.render(label, True, (30, 30, 30))
            screen.blit(name_text, (MAP_WIDTH + 42, legend_y + 1))

            legend_y += 20


    # ==================================================
    # 최근 재해 로그
    # ==================================================

    log_title = font.render("최근 사건 (최신순)", True, (20, 20, 20))
    screen.blit(log_title, (MAP_WIDTH + 20, legend_y + 6))

    log_y = legend_y + 30

    for yr, msg in reversed(event_history[-4:]):
        log_y = draw_wrapped_text(
            screen, f"{yr}년: {msg}", small_font, (90, 40, 40),
            MAP_WIDTH + 20, log_y, INFO_WIDTH - 40, 16, max_lines=2
        ) + 2


    # ==================================================
    # 마우스 위치 정보
    # ==================================================

    mouse_x, mouse_y = pygame.mouse.get_pos()

    if 0 <= mouse_x < MAP_WIDTH and 0 <= mouse_y < HEIGHT:

        tile_x = int((camera_x + mouse_x) / tile_size)
        tile_y = int((camera_y + mouse_y) / tile_size)

        if 0 <= tile_x < WORLD_WIDTH and 0 <= tile_y < WORLD_HEIGHT:

            terrain = world[tile_y][tile_x]
            tag = " (해안)" if is_coast[tile_y][tile_x] else ""

            if terrain == "desert" and desert_near_mountain[tile_y][tile_x]:
                tag += " (산기슭 광맥벨트)"

            if terrain == "mountain" and is_volcano[tile_y][tile_x]:
                tag += " (화산)"

            if earthquake_risk_tier[tile_y][tile_x] == 2:
                tag += " (지진 고위험)"
            elif earthquake_risk_tier[tile_y][tile_x] == 1:
                tag += " (지진 위험)"

            box_x = MAP_WIDTH + 12
            box_y = 235
            box_w = INFO_WIDTH - 24
            box_h = HEIGHT - box_y - 10

            pygame.draw.rect(screen, (225, 230, 235), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(screen, (100, 100, 100), (box_x, box_y, box_w, box_h), 1)

            info_title = font.render("현재 위치", True, (20, 20, 20))
            screen.blit(info_title, (box_x + 10, box_y + 7))

            civ = find_civilization_at(tile_x, tile_y)
            lines = [
                f"좌표: ({tile_x}, {tile_y}) · 지형: {TERRAIN_NAMES[terrain]}",
                tag if tag else "특이사항 없음",
                f"식량: {get_resource_value('food', tile_x, tile_y)} · 물: {get_resource_value('water', tile_x, tile_y)}",
                f"목재: {get_resource_value('wood', tile_x, tile_y)}" + (
                    f" · 숲 밀도 {forest_density[tile_y][tile_x]}" if terrain == "forest" else ""
                ),
                f"철: {get_resource_value('iron', tile_x, tile_y)} · 광물: {get_resource_value('minerals', tile_x, tile_y)}",
                f"석유: {get_resource_value('oil', tile_x, tile_y)}",
                f"건조도: {dryness_map[tile_y][tile_x]:.0f} · 기온: {temperature_map[tile_y][tile_x]:.1f}°C"
            ]

            owner_here = find_civilization_at(tile_x, tile_y)
            if owner_here is not None:
                lines.append(f"영토 주인: {owner_here['name']} · 규모 {territory_share_text(owner_here)}")

            old_clip = screen.get_clip()
            screen.set_clip(pygame.Rect(box_x + 6, box_y + 30, box_w - 12, box_h - 36))
            line_y = box_y + 34
            for line in lines:
                line_y = draw_wrapped_text(screen, line, small_font, (30, 30, 30), box_x + 10, line_y, box_w - 20, 17, max_lines=2)

            if civ is not None:
                line_y += 4
                civ_title = font.render(f"문명: {civ['name']}", True, civ["color"])
                screen.blit(civ_title, (box_x + 10, line_y))
                line_y += 25
                for line in get_civilization_stats_text(civ):
                    if line_y > box_y + box_h - 18:
                        break
                    line_y = draw_wrapped_text(screen, line, small_font, (30, 30, 30), box_x + 10, line_y, box_w - 20, 17, max_lines=2)
            screen.set_clip(old_clip)



    # ==================================================
    # 100년 건너뛰기 요약 화면 (맨 위에 덮어서 표시)
    # ==================================================

    if show_summary:

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(240)
        overlay.fill((25, 25, 30))
        screen.blit(overlay, (0, 0))

        header = title_font.render(
            f"{summary_range[0]}년 → {summary_range[1]}년 동안 있었던 일",
            True, (255, 255, 255)
        )
        screen.blit(header, (45, 28))

        hint = small_font.render("아무 키나 누르거나 클릭하면 닫힙니다", True, (180, 180, 180))
        screen.blit(hint, (45, 60))

        left_x = 45
        right_x = 620
        left_w = 535
        right_w = WIDTH - right_x - 45

        screen.blit(font.render("주요 사건", True, (245, 215, 120)), (left_x, 92))
        screen.blit(font.render("나라별 100년 변화", True, (130, 205, 255)), (right_x, 92))

        y_left = 122
        if not summary_entries:
            y_left = draw_wrapped_text(screen, "이 기간 동안 기록할 만한 사건이 없었습니다.", small_font, (210, 210, 210), left_x, y_left, left_w, 18)
        else:
            shown = 0
            for yr, msg in summary_entries:
                if y_left > HEIGHT - 48 or shown >= 22:
                    break
                if "전쟁" in msg:
                    color = (255, 155, 135)
                elif "멸망" in msg:
                    color = (255, 120, 120)
                elif "전염병" in msg:
                    color = (220, 175, 255)
                elif "무역" in msg:
                    color = (145, 225, 170)
                else:
                    color = (215, 215, 215)
                y_left = draw_wrapped_text(screen, f"{yr}년 - {msg}", small_font, color, left_x, y_left, left_w, 17, max_lines=2) + 3
                shown += 1
            if len(summary_entries) > shown:
                screen.blit(small_font.render(f"... 그 외 {len(summary_entries) - shown}건 더", True, (165, 165, 165)), (left_x, min(y_left + 2, HEIGHT - 28)))

        y_right = 122
        for line in summary_country_changes:
            if y_right > HEIGHT - 45:
                break
            y_right = draw_wrapped_text(screen, line, small_font, (225, 235, 245), right_x, y_right, right_w, 18, max_lines=2) + 8


    pygame.display.flip()
    clock.tick(60)


pygame.quit()
