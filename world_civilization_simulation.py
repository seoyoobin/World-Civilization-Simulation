import pygame
from opensimplex import OpenSimplex
import random
import math
import heapq

pygame.init()


# ==================================================
# 화면
# ==================================================

# 모니터 크기에 맞춰 가능한 한 크게 띄우되 작업표시줄/창 테두리 공간은 남긴다.
desktop_info = pygame.display.Info()
WIDTH = min(1600, max(1000, desktop_info.current_w - 70))
HEIGHT = min(900, max(650, desktop_info.current_h - 100))

# 오른쪽 정보창은 꼭 필요한 정보만 남겨 지도 영역을 넓힌다.
INFO_WIDTH = 360
MAP_WIDTH = WIDTH - INFO_WIDTH

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("세계 시뮬레이션 - 문명·국가 발전 v19")

clock = pygame.time.Clock()


# ==================================================
# 세계 크기
# ==================================================

WORLD_WIDTH = 240
WORLD_HEIGHT = 240

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

IRON_ZONE_COUNT = (43, 100)
MINERAL_ZONE_COUNT = (29, 72)
OIL_ZONE_COUNT = (14, 43)


OVERLAY_COLORS = {

    "food": (80, 220, 95),
    "water": (65, 190, 255),
    "wood": (205, 135, 60),
    "iron": (245, 130, 45),
    "minerals": (205, 95, 245),
    # 석유는 검정색이면 바다/어두운 배경에서 안 보여서 밝은 황금색으로 표시한다.
    "oil": (255, 195, 45)

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
# 객체 모델: Event / City / Country / World
# 기존 시뮬레이션 함수와 호환되도록 Country는 dict를 상속한다.
# ==================================================

class Event:
    def __init__(self, event_year, event_type, text, country_ids=None, x=None, y=None, data=None):
        self.year = int(event_year)
        self.type = str(event_type)
        self.text = str(text)
        self.country_ids = tuple(country_ids or ())
        self.x = x
        self.y = y
        self.data = data or {}

    def __repr__(self):
        return f"Event({self.year}, {self.type!r}, {self.text!r})"


class City:
    STAGE_NAMES = {0: "정착지", 1: "마을", 2: "도시", 3: "대도시"}
    STAGE_SYMBOLS = {0: "", 1: "·", 2: "●", 3: "◎"}

    def __init__(self, city_id, country_id, x, y, founded_year, score, capital=False, stage=0, specialization="일반"):
        self.id = city_id
        self.country_id = country_id
        self.x = int(x)
        self.y = int(y)
        self.founded_year = int(founded_year)
        self.score = float(score)
        self.capital = bool(capital)
        self.stage = int(stage)
        self.specialization = specialization
        self.population = 0
        self.last_upgrade_year = int(founded_year)
        self.alive = True

    @property
    def symbol(self):
        return "★" if self.capital else self.STAGE_SYMBOLS.get(self.stage, "·")

    @property
    def stage_name(self):
        return self.STAGE_NAMES.get(self.stage, "마을")


class Country(dict):
    """기존 civ['population'] 방식과 새 객체 속성 방식을 동시에 지원한다."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value

    def ensure_history(self):
        if "history" not in self:
            self["history"] = {
                "year": [], "population": [], "wealth": [], "food": [],
                "medical": [], "intelligence": [], "territory": [], "cities": [],
                "power": [], "collapse": [], "rank": []
            }
        self.setdefault("events", [])
        self.setdefault("cities", [])
        self.setdefault("rank_history", [])
        self.setdefault("dead", False)
        return self["history"]


class EventLog(list):
    """기존 event_history.append(...) 호출을 유지하면서 객체형 세계/국가 역사에도 자동 기록."""
    def append(self, item):
        super().append(item)
        wm = globals().get("world_state")
        if wm is not None:
            try:
                wm.capture_legacy_event(item)
            except Exception:
                # 역사 기록 오류가 시뮬레이션 자체를 멈추게 하지는 않는다.
                pass


class World:
    def __init__(self):
        self.events = []
        self.ranking_history = []
        self.last_ranks = {}
        self.last_leader_id = None
        self.city_serial = 0
        self.successor_serial = 0

    def reset(self):
        self.events.clear()
        self.ranking_history.clear()
        self.last_ranks.clear()
        self.last_leader_id = None
        self.city_serial = 0
        self.successor_serial = 0

    def infer_event_type(self, text):
        table = (
            ("전쟁 시작", "war_start"), ("전쟁 종결", "peace"), ("전쟁 종료", "peace"),
            ("멸망", "collapse"), ("붕괴", "collapse"), ("건국", "country_create"),
            ("무역", "trade"), ("전염병", "epidemic"),
            ("홍수", "flood"), ("가뭄", "drought"), ("화산", "volcano"),
            ("지진", "earthquake"), ("폭풍", "storm"), ("산불", "fire"),
            ("대도시", "metropolis"), ("도시", "city"), ("마을", "village"),
            ("수도 이전", "capital_move"), ("광산", "resource"), ("석유", "resource"),
            ("1위", "ranking"),
        )
        for keyword, event_type in table:
            if keyword in text:
                return event_type
        return "world"

    def capture_legacy_event(self, item):
        if not isinstance(item, (tuple, list)) or len(item) < 2:
            return
        ey, text = item[0], str(item[1])
        countries = globals().get("civilizations", [])
        ids = [c["id"] for c in countries if c.get("name") and c["name"] in text]
        ev = Event(ey, self.infer_event_type(text), text, ids)
        self.events.append(ev)
        for cid in ids:
            if 0 <= cid < len(countries):
                c = countries[cid]
                if isinstance(c, Country):
                    c.ensure_history()
                c.setdefault("events", []).append(ev)

    def record_year(self):
        # 순위는 한 해에 딱 한 번만 계산한다. 기존에는 국가마다 전체 랭킹을 다시 계산했다.
        countries = globals().get("civilizations", [])
        ranking = compute_world_ranking()
        score_by_id = {c["id"]: score for c, score in ranking}

        # 매년 국가별 시계열 데이터 저장
        for c in countries:
            if not isinstance(c, Country):
                continue
            hist = c.ensure_history()
            # 멸망한 국가는 멸망 연도까지만 기록하고 이후 0 값으로 그래프가 길게 늘어지지 않게 한다.
            if c.get("dead", False) and hist["year"] and hist["year"][-1] >= c.get("death_year", year):
                continue
            hist["year"].append(year)
            hist["population"].append(int(c.get("population", 0)))
            hist["wealth"].append(float(c.get("wealth", 0)))
            hist["food"].append(float(c.get("food", 0)))
            hist["medical"].append(float(c.get("medical", 0)))
            hist["intelligence"].append(float(c.get("intelligence", 0)))
            hist["territory"].append(len(c.get("territory", ())))
            hist["cities"].append(sum(1 for city in c.get("cities", []) if city.alive and city.stage >= 1))
            hist["power"].append(float(score_by_id.get(c["id"], 0.0)))
            hist["collapse"].append(float(c.get("collapse_score", 0)))

        self.ranking_history.append((year, [(c["id"], score) for c, score in ranking]))
        for i, (c, score) in enumerate(ranking):
            rank = i + 1
            c.ensure_history()["rank"].append(rank)
            prev = self.last_ranks.get(c["id"])
            c.setdefault("rank_history", []).append((year, rank, score))
            if rank == 1 and self.last_leader_id != c["id"] and year > 0:
                event_history.append((year, f"{c['name']} 세계 국력 1위 달성"))
                self.last_leader_id = c["id"]
            if prev is not None:
                c["rank_change"] = prev - rank
            self.last_ranks[c["id"]] = rank

    def simulate_year(self):
        _advance_year_core()
        self.record_year()


world_state = World()

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

# 자원 원형 오버레이 캐시. 1~3번은 일정 구역을 묶은 총량, 4~6번은 실제 매장지 덩어리 총량을 저장한다.
resource_bubbles = {}
resource_bubble_max = {}
RESOURCE_BUBBLE_BLOCK = 10

# ===== 문명 속도 조절 =====
# 의료는 2000년 전후에 100에 가까워지도록 역사적 상한을 둔다.
MEDICAL_TARGET_YEAR = 2000
DIPLOMACY_INTERVAL = 2
TERRITORY_EXPANSION_INTERVAL = 1
ENV_CACHE_INTERVAL = 3
# 영토-인구 비례 조절. 한 칸당 적정 인구가 지나치게 넓게 흔들리지 않게 한다.
BASE_PEOPLE_PER_TILE = 1500.0
TERRITORY_TARGET_FILL = 0.80       # 적정 영토에서 수용력의 약 80% 정도를 목표로 함
TERRITORY_MAX_EXPAND_PER_YEAR = 16 # 인구 증가에 맞춰 연결된 영토를 조금 더 빠르게 확장
TERRITORY_SHRINK_START = 1.65     # 적정 영토의 1.65배보다 넓고 인구가 적으면 변두리 일부 포기
NEARBY_COLONY_MAX_GAP = 7         # 섬 확장은 기존 영토에서 최대 6칸 이내의 가까운 해안만 허용
NEARBY_COLONY_INTERVAL = 25       # 원거리 점프가 아니라 드문 근거리 해안 정착만 허용
EXTINCTION_POPULATION = 100  # 이 인구 이하로 떨어지면 즉시 완전 멸망
MIN_WAR_CORE_TILES = 18      # 패전해도 핵심 영토를 더 많이 보존해 연쇄 멸망 방지

# ===== 전쟁 빈도 / 거리 / 시대 제한 =====
WAR_START_YEAR = 600          # 충분히 성장한 뒤부터 전쟁 가능
WAR_CHECK_INTERVAL = 8        # 전쟁 후보는 8년에 한 번만 검사
GLOBAL_WAR_GAP_MIN = 80       # 세계 전체 새 전쟁 최소 간격
GLOBAL_WAR_GAP_MAX = 125
WAR_MIN_DURATION = 5          # 전쟁은 최소 5년
WAR_MAX_DURATION = 20         # 최대 20년
WAR_TRUCE_MIN = 45            # 종전 후 같은 상대와 바로 재전쟁 방지
WAR_TRUCE_MAX = 80
next_global_war_year = WAR_START_YEAR


def war_era_chance_multiplier():
    """후대로 갈수록 전쟁이 빠르게 줄어든다.
    특히 2000년 이후에는 전쟁이 완전히 0은 아니지만 매우 드물다.
    """
    if year < 900:
        return 0.48
    if year < 1400:
        return 0.56
    if year < 1700:
        return 0.42
    if year < 1900:
        return 0.24
    if year < 2000:
        return 0.09
    if year < 2050:
        return 0.018
    if year < 2100:
        return 0.004
    return 0.0015


def global_war_gap_range():
    """세계 전체 전쟁 사이 간격. 근현대로 갈수록 매우 길어진다."""
    alive_count = sum(1 for c in civilizations if civ_alive(c))
    if year < 1000:
        lo, hi = 80, 125
    elif year < 1500:
        lo, hi = 110, 170
    elif year < 1800:
        lo, hi = 150, 230
    elif year < 2000:
        lo, hi = 230, 360
    else:
        lo, hi = 450, 800

    # 살아 있는 국가가 줄수록 추가 정복전쟁을 더 강하게 억제한다.
    if alive_count <= 6:
        lo = int(lo * 1.25)
        hi = int(hi * 1.35)
    if alive_count <= 5:
        lo = int(lo * 1.45)
        hi = int(hi * 1.55)
    if alive_count <= 4:
        lo = int(lo * 1.80)
        hi = int(hi * 2.00)
    return lo, hi


def survivor_war_multiplier():
    """몇 개 국가만 남았을 때 한 나라가 전부 정복하는 흐름을 막는다."""
    alive_count = sum(1 for c in civilizations if civ_alive(c))
    if alive_count >= 8:
        return 1.0
    if alive_count == 7:
        return 0.88
    if alive_count == 6:
        return 0.62
    if alive_count == 5:
        return 0.32
    if alive_count == 4:
        return 0.10
    return 0.0


_NEIGHBORS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# ===== 최적화 캐시 =====
# 영토가 바뀔 때 revision만 올리고, 비싼 국경/연결성 검사는 같은 상태에서 재사용한다.
_border_cache = {}
_multiplier_signature = None


def _territory_revision(civ):
    return civ.get("territory_revision", 0)


def _touch_territory(civ):
    """영토 변경 표시. 게임 규칙은 건드리지 않고 캐시만 무효화한다."""
    civ["territory_revision"] = civ.get("territory_revision", 0) + 1
    civ["env_cache_year"] = -999999
    civ.pop("_component_cache", None)
    civ.pop("_territory_sample_cache", None)
    # revision이 key에 들어가므로 오래된 값은 안전하지만, 메모리 누적은 제한한다.
    if len(_border_cache) > 2048:
        _border_cache.clear()


def _sample_territory_indices(civ, max_samples):
    """영토가 바뀌지 않는 동안 동일한 균등 표본을 재사용한다."""
    tiles = civ.get("territory") or set()
    if not tiles:
        return ()
    rev = _territory_revision(civ)
    cache = civ.setdefault("_territory_sample_cache", {})
    key = (rev, max_samples)
    cached = cache.get(key)
    if cached is not None:
        return cached
    if len(tiles) <= max_samples:
        sample = tuple(tiles)
    else:
        arr = tuple(tiles)
        step = len(arr) / max_samples
        sample = tuple(arr[int(i * step)] for i in range(max_samples))
    # 오래된 revision 표본은 버린다.
    if len(cache) > 6:
        cache.clear()
    cache[key] = sample
    return sample


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
        return 22
    if stage == 3:
        return 54
    if stage == 4:
        return 108
    return 240


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
        and civ["population"] >= 8_000
        and civ["intelligence"] >= 38
        and civ["wealth"] >= 12_000
        and development_level(civ) >= 38
    )


def war_range(civ):
    """비접경 국가와 싸울 수 있는 최대 '영토 사이 간격'.

    240x240 지도에서도 먼 나라끼리 갑자기 싸우지 않도록 상대적 거리를 유지한다.
    이제 초중기에는 아주 가까운 나라만, 후기로 가도 지도 반대편과는 싸울 수 없다.
    """
    dev = development_level(civ)
    if year < 800:
        era_cap = 17.0
    elif year < 1300:
        era_cap = 24.0
    else:
        era_cap = 34.0
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
        sample = _sample_territory_indices(civ, max_samples)
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
        if all((x-c["x"])**2 + (y-c["y"])**2 >= 24**2 for c in civilizations):
            return x, y
    return random.choice(candidates)


def _refresh_frontier_for(civ):
    frontier = set()
    owner_map = territory_owner
    world_local = world
    width = WORLD_WIDTH
    height = WORLD_HEIGHT
    for idx in civ["territory"]:
        y, x = divmod(idx, width)
        for dx, dy in _NEIGHBORS4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                nidx = ny * width + nx
                if world_local[ny][nx] != "water" and owner_map[nidx] == -1:
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
    _touch_territory(civ)
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

    return Country({
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
        "territory_revision": 0,
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
        "demographic_shock": 0.0,
        "cities": [],
        "events": [],
        "history": {
            "year": [], "population": [], "wealth": [], "food": [],
            "medical": [], "intelligence": [], "territory": [], "cities": [],
            "power": [], "collapse": [], "rank": []
        },
        "rank_history": [],
        "dead": False,
        "collapse_score": 0.0,
        "collapse_state": "안정",
        "last_city_year": -999999,
        "last_capital_move_year": -999999,
    })


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
        initial_target = int(clamp(round(civ["population"] / 900), 4, 8))
        while len(civ["territory"]) < initial_target:
            valid = [idx for idx in civ["frontier"] if territory_owner[idx] == -1]
            if not valid:
                break
            env = get_civ_environment(civ)
            best = max(random.sample(valid, min(len(valid), 12)), key=lambda idx: expansion_tile_score(civ, idx, env))
            if not claim_tile(civ, best):
                break
        _refresh_frontier_for(civ)

    for civ in civilizations:
        event_history.append((year, f"🏴 {civ['name']} 건국"))


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

    sample = _sample_territory_indices(civ, max_samples)

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
    # 전염병은 국가 전체에 장기간 충격을 주도록 강화한다.
    # 의료가 낮으면 10~18년, 의료가 매우 높으면 대체로 3~7년 정도 지속한다.
    duration = int(round(16 - civ["medical"] * 0.115 + random.uniform(-2, 2)))
    duration = int(clamp(duration, 3, 18))
    # 전염병마다 기본 강도가 조금 다르다. 1.0 근처가 보통, 1.35 이상이면 대유행.
    epidemic_strength = random.uniform(0.85, 1.35)
    if random.random() < 0.12:
        epidemic_strength *= random.uniform(1.15, 1.35)
    active_epidemics.append({
        "civ_id": civ["id"],
        "start_year": year,
        "end_year": year + duration - 1,
        "imported": imported,
        "strength": epidemic_strength,
        "start_population": civ["population"],
    })
    civ["status"] = "전염병"
    civ["demographic_shock"] = max(civ.get("demographic_shock", 0.0), 18.0)
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
        strength = e.get("strength", 1.0)
        # 기존보다 전염병 자체의 인구 피해를 크게 한다. 의료는 피해를 줄이지만 완전히 지우지는 못한다.
        severity = random.uniform(0.025, 0.070) * strength
        medical_protection = 1.0 - 0.68 * civ["medical"] / 100
        mortality = clamp(severity * medical_protection, 0.004, 0.085)
        old = civ["population"]
        civ["population"] = max(0, int(civ["population"] * (1 - mortality)))
        civ["last_population_change"] += civ["population"] - old
        # 노동력·교역·수송까지 흔들리므로 재산과 식량에도 강한 손실을 준다.
        civ["wealth"] *= 1 - clamp(0.028 + mortality * 1.8, 0.025, 0.14)
        civ["food"] *= 1 - clamp(0.020 + mortality * 1.25, 0.018, 0.11)
        # 유행이 끝난 직후 인구가 폭발적으로 반등하지 않도록 인구 충격을 누적한다.
        shock_add = clamp(mortality * 520.0, 2.0, 22.0)
        civ["demographic_shock"] = clamp(civ.get("demographic_shock", 0.0) + shock_add, 0, 100)
        start_pop = max(e.get("start_population", old), 1)
        if civ["population"] < start_pop * 0.45:
            civ["status"] = "대유행·인구 붕괴"
            civ["famine_years"] = max(civ.get("famine_years", 0), 4)
            civ["poverty_years"] = max(civ.get("poverty_years", 0), 6)
        survivors.append(e)
    active_epidemics[:] = survivors


def countries_border(a, b):
    if not a["territory"] or not b["territory"]:
        return False

    aid, bid = a["id"], b["id"]
    ar, br = _territory_revision(a), _territory_revision(b)
    if aid <= bid:
        cache_key = (aid, bid, ar, br)
    else:
        cache_key = (bid, aid, br, ar)
    cached = _border_cache.get(cache_key)
    if cached is not None:
        return cached

    # 작은 쪽의 영토만 검사.
    small = a if len(a["territory"]) <= len(b["territory"]) else b
    other_id = b["id"] if small is a else a["id"]
    owner_map = territory_owner
    width = WORLD_WIDTH
    height = WORLD_HEIGHT
    result = False
    for idx in small["territory"]:
        y, x = divmod(idx, width)
        if x > 0 and owner_map[idx - 1] == other_id:
            result = True; break
        if x + 1 < width and owner_map[idx + 1] == other_id:
            result = True; break
        if y > 0 and owner_map[idx - width] == other_id:
            result = True; break
        if y + 1 < height and owner_map[idx + width] == other_id:
            result = True; break

    _border_cache[cache_key] = result
    return result


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
    if civ["population"] < 8_000:
        reasons.append(f"인구 {civ['population']:,}/8,000")
    if civ["intelligence"] < 38:
        reasons.append(f"지능 {civ['intelligence']:.1f}/38")
    if civ["wealth"] < 12_000:
        reasons.append(f"재산 {civ['wealth']:,.0f}/12,000")
    dev = development_level(civ)
    if dev < 38:
        reasons.append(f"발달도 {dev:.1f}/38")
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
    return clamp(density, 1000.0, 2800.0)


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
    return clamp(capacity, 1200.0, 60_000_000.0)


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
    score = food * wf + water * ww + wood * 0.12 + iron * wi + minerals * wm + oil * wo

    # 도시와 가까운 곳, 기존 영토에 단단히 붙는 곳을 우선해 자연스러운 형태를 만든다.
    city_bonus = 0.0
    if civ.get("cities"):
        nearest = min(math.hypot(city.x - x, city.y - y) for city in civ["cities"] if city.alive)
        city_bonus = clamp(28 - nearest * 2.0, 0, 28)
    neighbor_owned = _same_owner_neighbor_count(civ, idx) if civ.get("territory") else 0
    cohesion_bonus = neighbor_owned * 8.0

    terrain_penalty = {"mountain": 16, "desert": 13, "forest": 4}.get(world[y][x], 0)
    disaster_penalty = earthquake_risk_tier[y][x] * 6 + (8 if is_volcano[y][x] else 0) + (5 if dryness_map[y][x] > 85 else 0)
    competition_penalty = 0
    for dx, dy in _NEIGHBORS4:
        nx, ny = x + dx, y + dy
        if 0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT:
            owner = territory_owner[ny * WORLD_WIDTH + nx]
            if owner >= 0 and owner != civ["id"]:
                competition_penalty += 12

    return score + city_bonus + cohesion_bonus - terrain_penalty - disaster_penalty - competition_penalty + random.random() * 5


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
    _touch_territory(civ)
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
        _touch_territory(civ)
        _refresh_frontier_for(civ)
    return removed


def _remove_tiny_territory_fragments(civ, min_size=4):
    """버그/점령 계산으로 생긴 1~3칸짜리 고립 점 영토를 자동 정리한다.
    영토가 전혀 바뀌지 않았다면 이전 검사 결과가 그대로이므로 재검사를 생략한다.
    """
    rev = _territory_revision(civ)
    cleanup_key = (rev, min_size)
    if civ.get("_fragment_cleanup_key") == cleanup_key:
        return 0
    civ["_fragment_cleanup_key"] = cleanup_key
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
        _touch_territory(civ)
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
    chance = 0.28 + max(rel["relation"], 0) / 520
    if complement:
        chance += 0.26
    if year >= 1500:
        chance += 0.10
    if year >= 1900:
        chance += 0.15
    if random.random() >= min(chance, 0.86):
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
    change_relation(a, b, 2.6 if year < 1800 else 3.4)
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
        0.003
        + 0.020 * pressure
        + 0.014 * target_richness
        + 0.018 * crowding
        + 0.038 * hostility
        + 0.025 * advantage
        + (0.008 if border else 0.0)
    ) * distance_factor

    # 강대국이 약소국을 노리는 경우 약간 올라가지만 너무 자주 발생하지 않게 제한한다.
    if power_a >= power_b * 1.35:
        war_chance += 0.008
    if power_a >= power_b * 1.70:
        war_chance += 0.006

    # 우호 관계일수록 확률을 크게 낮춘다.
    if rel["relation"] >= 60:
        war_chance *= 0.025
    elif rel["relation"] >= 30:
        war_chance *= 0.12
    elif rel["relation"] >= 10:
        war_chance *= 0.38

    # 후대로 갈수록 전쟁은 급격히 드물어진다. 국가 수가 적을 때도 연쇄 정복을 막는다.
    war_chance *= war_era_chance_multiplier()
    war_chance *= survivor_war_multiplier()

    if random.random() >= clamp(war_chance, 0, 0.050):
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
        "start_population_a": attacker["population"],
        "start_population_b": defender["population"],
    })
    change_relation(attacker, defender, random.uniform(-40, -65))
    attacker["status"] = "전쟁"
    defender["status"] = "전쟁"

    # 후대로 갈수록 새 전쟁 사이 간격이 크게 늘어난다.
    gap_lo, gap_hi = global_war_gap_range()
    next_global_war_year = year + random.randint(gap_lo, gap_hi)

    contact = "접경전쟁" if border else f"근거리전쟁/영토간격 {territory_gap:.0f}칸"
    event_history.append((year, f"{attacker['name']}와 {defender['name']} 전쟁 시작 ({attacker['name']} 공격 · {contact} · 최대 {max_years}년)"))
    return True


def transfer_border_territory(winner, loser, amount, allow_elimination=False):
    """실제 접경선에서만 영토를 덩어리로 점령한다.

    비접경 전쟁은 인구/경제 피해는 줄 수 있지만, 지도 반대편에 1칸짜리 점령지가
    갑자기 생기지는 않는다. 영토 이동은 두 나라 영토가 맞닿았을 때만 발생한다.
    """
    if amount <= 0 or not loser.get("territory") or not winner.get("territory"):
        return 0

    if not allow_elimination:
        max_take = max(0, len(loser["territory"]) - MIN_WAR_CORE_TILES)
        amount = min(amount, max_take)
        if amount <= 0:
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
        _touch_territory(winner)
        _touch_territory(loser)
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
        # 직접 전투 사망은 너무 과도하지 않게 낮추고, 장기적인 식량·경제 붕괴가 더 큰 역할을 하게 한다.
        loss_a = random.uniform(0.0012, 0.0038) * (0.55 + b_share * 1.55)
        loss_b = random.uniform(0.0012, 0.0038) * (0.55 + a_share * 1.55)
        if w["large"]:
            loss_a *= 1.18
            loss_b *= 1.18
        # 압도적인 전력 차이면 약한 쪽 피해를 더 크게 만든다.
        if pa > pb * 1.45:
            loss_b *= 1.35
            loss_a *= 0.82
        elif pb > pa * 1.45:
            loss_a *= 1.35
            loss_b *= 0.82
        loss_a = clamp(loss_a, 0.0008, 0.012)
        loss_b = clamp(loss_b, 0.0008, 0.012)

        # 후대 전쟁은 드물고, 의료/물류 발달로 인구 직접 손실도 상대적으로 작아진다.
        if year >= 1900:
            loss_a *= 0.68
            loss_b *= 0.68
        if year >= 2000:
            loss_a *= 0.48
            loss_b *= 0.48

        old_a, old_b = a["population"], b["population"]
        a["population"] = max(0, int(a["population"] * (1 - loss_a)))
        b["population"] = max(0, int(b["population"] * (1 - loss_b)))
        da = old_a - a["population"]
        db = old_b - b["population"]
        a["last_population_change"] -= da
        b["last_population_change"] -= db
        w["casualties_a"] += da
        w["casualties_b"] += db
        # 전쟁으로 큰 인구 손실을 입은 국가는 평화가 와도 즉시 고성장하지 못한다.
        shock_a = (da / max(old_a, 1)) * 480.0
        shock_b = (db / max(old_b, 1)) * 480.0
        a["demographic_shock"] = clamp(a.get("demographic_shock", 0.0) + shock_a, 0, 100)
        b["demographic_shock"] = clamp(b.get("demographic_shock", 0.0) + shock_b, 0, 100)

        # 전쟁은 농지·보급·교역·산업을 파괴한다. 식량과 재산 손실을 크게 줘서
        # 이후 몇 년간 기근/빈곤으로 추가 인구 감소가 이어질 수 있다.
        food_rate_a = clamp(random.uniform(0.040, 0.085) * (0.75 + b_share) * (1 + a["war_fatigue"] / 220), 0.025, 0.13)
        food_rate_b = clamp(random.uniform(0.040, 0.085) * (0.75 + a_share) * (1 + b["war_fatigue"] / 220), 0.025, 0.13)
        wealth_rate_a = clamp(random.uniform(0.018, 0.045) * (0.75 + b_share), 0.012, 0.075)
        wealth_rate_b = clamp(random.uniform(0.018, 0.045) * (0.75 + a_share), 0.012, 0.075)

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
            fraction = 0.002 + advantage * (0.008 if w["large"] else 0.005)
            amount = max(1, int(len(loser["territory"]) * fraction))
            amount = min(amount, 10 if w["large"] else 6)
            transfer_border_territory(winner, loser, amount)

        # 생존선 이하/영토 소멸이면 즉시 국가 멸망. 접경 중이면 일부 영토가 넘어가고,
        # 비접경 전쟁이면 점 영토를 만들지 않기 위해 멀리 있는 영토는 합병하지 않는다.
        if a["population"] <= EXTINCTION_POPULATION or b["population"] <= EXTINCTION_POPULATION:
            winner, loser = (b, a) if a["population"] <= EXTINCTION_POPULATION else (a, b)
            transfer_border_territory(winner, loser, len(loser.get("territory", ())), allow_elimination=True)
            loser["population"] = 0
            event_history.append((year, f"{winner['name']}가 {loser['name']}를 장기전 끝에 붕괴시킴"))
            continue

        if not a["territory"] or not b["territory"]:
            winner, loser = (b, a) if not a["territory"] else (a, b)
            transfer_border_territory(winner, loser, len(loser.get("territory", ())), allow_elimination=True)
            loser["population"] = 0
            event_history.append((year, f"{loser['name']}가 모든 영토를 잃어 {winner['name']}에 흡수"))
            continue

        # 전쟁 때문에 국가 인구 기반 자체가 무너졌다면 수천 명짜리 국가가 비정상적으로 고성장하게 두지 않는다.
        # 시작 인구의 15% 미만이면서 4천 명 미만, 또는 1,200명 미만이면 국가 붕괴로 넘긴다.
        start_a = max(w.get("start_population_a", old_a), 1)
        start_b = max(w.get("start_population_b", old_b), 1)
        a_devastated = a["population"] < 1_200 or (a["population"] < 4_000 and a["population"] < start_a * 0.15)
        b_devastated = b["population"] < 1_200 or (b["population"] < 4_000 and b["population"] < start_b * 0.15)
        if a_devastated != b_devastated:
            loser = a if a_devastated else b
            winner = b if a_devastated else a
            # 이 정도로 인구 기반이 파괴된 국가는 이름만 바꾼 계승국으로 즉시 부활시키지 않는다.
            # 접경 중이면 승전국이 가능한 범위의 영토를 넘겨받고, 나머지는 무주지가 된다.
            transfer_border_territory(winner, loser, len(loser.get("territory", ())), allow_elimination=True)
            loser["population"] = 0
            loser["status"] = "전쟁으로 붕괴"
            event_history.append((year, f"{loser['name']}가 전쟁으로 인구 기반을 상실하여 멸망"))
            continue

        # 최소 기간 전에는 아무리 우세해도 종전하지 않는다. 최대 20년에는 반드시 끝난다.
        decisive = years >= w.get("min_years", WAR_MIN_DURATION) and abs(w["score"]) >= 1.65
        if years >= w["max_years"] or decisive:
            if abs(w["score"]) < 0.12:
                # 거의 무승부면 점령을 최소화한다.
                winner = a if pa >= pb else b
                loser = b if winner is a else a
                frac = 0.018
                result_label = "근소한 승리"
            else:
                winner, loser = (a, b) if w["score"] >= 0 else (b, a)
                margin = abs(w["score"])
                if margin < 0.55:
                    frac = 0.025
                    result_label = "승리"
                elif margin < 1.15:
                    frac = 0.050
                    result_label = "대승"
                else:
                    frac = 0.080
                    result_label = "압도적 승리"
            extra = max(1, int(len(loser["territory"]) * frac))
            transfer_border_territory(winner, loser, min(extra, 36))

            rel = get_diplomacy(a, b)
            rel["truce_until"] = year + random.randint(WAR_TRUCE_MIN, WAR_TRUCE_MAX)
            a["war_cooldown_until"] = year + random.randint(40, 70)
            b["war_cooldown_until"] = year + random.randint(40, 70)
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
    military_scores = {c["id"]: military_power(c) for c in alive}

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

            # 초기에는 중립적으로 흔들리지만, 후대로 갈수록 장기 평화/교역이 관계를 안정시킨다.
            if year < 1500:
                change_relation(a, b, random.uniform(-0.08, 0.10))
            elif year < 1900:
                change_relation(a, b, random.uniform(0.00, 0.16))
            else:
                change_relation(a, b, random.uniform(0.10, 0.34))

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
                or military_scores[a["id"]] > military_scores[b["id"]] * 1.35
                or military_scores[b["id"]] > military_scores[a["id"]] * 1.35
            )
            if year >= WAR_START_YEAR and year % WAR_CHECK_INTERVAL == 0 and ((not traded) or hostile_or_stressed):
                maybe_start_war(a, b, envs[a["id"]], envs[b["id"]])
                if not at_war(a, b):
                    maybe_start_war(b, a, envs[b["id"]], envs[a["id"]])



# ==================================================
# 도시 / 역사 / 붕괴 / 세계 순위 시스템
# ==================================================

def _city_event(civ, text):
    event_history.append((year, text))


def city_site_score(civ, idx, ideal_density=None, living_cities=None):
    """사용자가 정한 입지 규칙을 0~100 근처 점수로 환산."""
    if idx not in civ.get("territory", ()):
        return -999.0
    y, x = divmod(idx, WORLD_WIDTH)
    terrain = world[y][x]
    key = get_terrain_key(x, y)
    terrain_score = {
        "river": 40, "coast": 30, "plain": 25,
        "forest": 10, "mountain": 5, "desert": 2, "water": -100
    }.get(key, 0)
    if terrain == "water":
        return -999.0

    water = get_resource_value_fast("water", x, y)
    food = get_resource_value_fast("food", x, y)
    wood = get_resource_value_fast("wood", x, y)
    iron = get_resource_value_fast("iron", x, y)
    minerals = get_resource_value_fast("minerals", x, y)
    oil = get_resource_value_fast("oil", x, y)

    water_access = clamp(water / 150.0 * 20.0, 0, 20)
    food_score = clamp(food / 120.0 * 20.0, 0, 20)
    resource_score = clamp((wood / 100 + iron / 350 + minerals / 450 + oil / 700) * 5.0, 0, 15)

    # 주변 인구는 국가 평균 밀도를 이용한 근사치. 도시가 이미 가까이 있으면 집적 효과가 조금 생긴다.
    avg_density = civ["population"] / max(len(civ.get("territory", ())), 1)
    if ideal_density is None:
        ideal_density = ideal_people_per_tile(civ)
    pop_score = clamp(avg_density / max(ideal_density, 1) * 12.0, 0, 15)
    nearest_city = 999.0
    city_iter = living_cities if living_cities is not None else civ.get("cities", [])
    for city in city_iter:
        if city.alive:
            dx = city.x - x
            dy = city.y - y
            d2 = dx * dx + dy * dy
            if d2 < nearest_city * nearest_city:
                nearest_city = math.sqrt(d2)
    transport = 0.0
    if key == "river":
        transport += 10
    elif key == "coast":
        transport += 8
    elif terrain == "plain":
        transport += 5
    if nearest_city < 12:
        transport += clamp((12 - nearest_city) * 0.35, 0, 4)
    transport = clamp(transport, 0, 10)

    difficulty = {"mountain": 18, "desert": 16, "forest": 7}.get(terrain, 0)
    water_shortage = 0
    if water < 8:
        water_shortage = 30
    elif water < 20:
        water_shortage = 18
    elif water < 35:
        water_shortage = 8

    disaster_risk = 0
    if is_volcano[y][x]:
        disaster_risk += 9
    disaster_risk += earthquake_risk_tier[y][x] * 4
    if dryness_map[y][x] > 85:
        disaster_risk += 5
    if terrain == "river":
        disaster_risk += 2
    disaster_risk = min(disaster_risk, 15)

    return clamp(
        terrain_score + water_access + food_score + resource_score + pop_score + transport
        - difficulty - water_shortage - disaster_risk,
        0, 100
    )


def city_specialization(x, y):
    key = get_terrain_key(x, y)
    iron = get_resource_value_fast("iron", x, y)
    minerals = get_resource_value_fast("minerals", x, y)
    food = get_resource_value_fast("food", x, y)
    wood = get_resource_value_fast("wood", x, y)
    if key == "coast":
        return "⚓ 항구도시"
    if world[y][x] == "mountain" and iron + minerals > 80:
        return "⛏️ 광업도시"
    if key == "river":
        return "🌾 강변 농업·교통도시"
    if world[y][x] == "forest" and wood > 45:
        return "🌲 목재도시"
    if world[y][x] == "plain" and food > 65:
        return "🌾 농업도시"
    return "일반도시"


def _new_city(civ, idx, capital=False, stage=0):
    y, x = divmod(idx, WORLD_WIDTH)
    world_state.city_serial += 1
    score = city_site_score(civ, idx)
    city = City(
        world_state.city_serial, civ["id"], x, y, year,
        score=score, capital=capital, stage=stage,
        specialization=city_specialization(x, y)
    )
    civ.setdefault("cities", []).append(city)
    civ["last_city_year"] = year
    return city


def _best_city_candidate(civ, ideal_density=None, living_cities=None):
    tiles = list(civ.get("territory", ()))
    if not tiles:
        return None, -999
    # 너무 큰 나라에서도 속도를 유지하도록 표본 사용.
    if len(tiles) > 180:
        tiles = random.sample(tiles, 180)
    best_idx = None
    best_score = -999
    cities_for_check = living_cities if living_cities is not None else [city for city in civ.get("cities", []) if city.alive]
    for idx in tiles:
        y, x = divmod(idx, WORLD_WIDTH)
        too_close = False
        for city in cities_for_check:
            dx = city.x - x
            dy = city.y - y
            if dx * dx + dy * dy < 36:
                too_close = True
                break
        if too_close:
            continue
        score = city_site_score(civ, idx, ideal_density, cities_for_check)
        if score > best_score:
            best_idx, best_score = idx, score
    return best_idx, best_score


def update_cities():
    for civ in civilizations:
        if not civ_alive(civ):
            continue
        civ.setdefault("cities", [])
        pop = civ["population"]
        env_for_city = get_civ_environment(civ)
        ideal_density = ideal_people_per_tile(civ, env_for_city)
        living = [city for city in civ["cities"] if city.alive]

        # 최초 수도 정착. 수도는 도시 단계와 무관하게 ★로 표시한다.
        if not civ["cities"] and pop >= 1_000:
            idx = civ["y"] * WORLD_WIDTH + civ["x"]
            score = city_site_score(civ, idx, ideal_density, living)
            stage = 1 if score >= 30 else 0
            city = _new_city(civ, idx, capital=True, stage=stage)
            if stage >= 1:
                _city_event(civ, f"· {civ['name']} 최초의 마을 건설 (수도, 입지 {score:.0f})")

        # 인구와 영토에 맞춰 도시 개수를 천천히 늘린다. 한 해에 하나만 새 정착 가능.
        if pop >= 1_000:
            territory_limit = max(1, len(civ.get("territory", ())) // 22 + 1)
            population_limit = 1 + int(pop / 12_000)
            target_count = int(clamp(min(territory_limit, population_limit), 1, 16))
            living_count = len(living)
            if living_count < target_count and year - civ.get("last_city_year", -999999) >= 8:
                idx, score = _best_city_candidate(civ, ideal_density, living)
                if idx is not None and score >= 30:
                    _new_city(civ, idx, capital=False, stage=0)
                    y, x = divmod(idx, WORLD_WIDTH)
                    _city_event(civ, f"{civ['name']} 새 정착 시작 ({x},{y}, 입지 {score:.0f})")

        living = [city for city in civ["cities"] if city.alive]
        if not living:
            continue

        weights = [max(10.0, city.score + (25 if city.capital else 0)) for city in living]
        total_weight = max(sum(weights), 1.0)
        for city, weight in zip(living, weights):
            city.population = int(pop * weight / total_weight)
            city.score = city_site_score(civ, city.y * WORLD_WIDTH + city.x, ideal_density, living)
            city.specialization = city_specialization(city.x, city.y)
            age = year - city.founded_year
            since_upgrade = year - city.last_upgrade_year

            if city.stage == 0 and age >= 3 and city.score >= 30:
                city.stage = 1
                city.last_upgrade_year = year
                _city_event(civ, f"· {civ['name']} 마을 탄생 ({city.x},{city.y})")
            elif city.stage == 1 and pop >= 3_000 and city.population >= 2_200 and city.score >= 50 and since_upgrade >= 5:
                city.stage = 2
                city.last_upgrade_year = year
                _city_event(civ, f"● {civ['name']} 도시 성장 ({city.specialization}, {city.x},{city.y})")
            elif city.stage == 2 and pop >= 10_000 and city.population >= 7_500 and city.score >= 65 and since_upgrade >= 8:
                city.stage = 3
                city.last_upgrade_year = year
                _city_event(civ, f"◎ {civ['name']} 대도시 탄생 ({city.specialization}, {city.x},{city.y})")

        # 수도 타일을 잃었거나 매우 부적합해졌으면 살아남은 주요 도시로 수도 이전.
        capitals = [city for city in living if city.capital]
        capital = capitals[0] if capitals else None
        capital_owned = False
        if capital is not None:
            cidx = capital.y * WORLD_WIDTH + capital.x
            capital_owned = territory_owner[cidx] == civ["id"]
        if capital is None or not capital_owned:
            candidates = [city for city in living if territory_owner[city.y * WORLD_WIDTH + city.x] == civ["id"]]
            if candidates:
                new_capital = max(candidates, key=lambda c: (c.stage, c.score, c.population))
                for city in living:
                    city.capital = False
                new_capital.capital = True
                civ["x"], civ["y"] = new_capital.x, new_capital.y
                civ["last_capital_move_year"] = year
                _city_event(civ, f"👑 {civ['name']} 수도 이전 → ({new_capital.x},{new_capital.y})")


def _territory_component_count(civ, stop_after=3):
    rev = _territory_revision(civ)
    cache_key = (rev, stop_after)
    cache = civ.get("_component_cache")
    if cache is not None and cache[0] == cache_key:
        return cache[1]

    tiles = set(civ.get("territory", ()))
    count = 0
    width = WORLD_WIDTH
    height = WORLD_HEIGHT
    while tiles:
        count += 1
        if count >= stop_after:
            civ["_component_cache"] = (cache_key, count)
            return count
        seed = tiles.pop()
        queue = [seed]
        pos = 0
        while pos < len(queue):
            idx = queue[pos]
            pos += 1
            y, x = divmod(idx, width)
            if x > 0:
                nidx = idx - 1
                if nidx in tiles:
                    tiles.remove(nidx); queue.append(nidx)
            if x + 1 < width:
                nidx = idx + 1
                if nidx in tiles:
                    tiles.remove(nidx); queue.append(nidx)
            if y > 0:
                nidx = idx - width
                if nidx in tiles:
                    tiles.remove(nidx); queue.append(nidx)
            if y + 1 < height:
                nidx = idx + width
                if nidx in tiles:
                    tiles.remove(nidx); queue.append(nidx)
    civ["_component_cache"] = (cache_key, count)
    return count


def calculate_collapse_score(civ):
    if not civ_alive(civ):
        return 100.0
    score = 0.0
    pop = civ["population"]
    if pop < 1_000:
        score += 20
    if pop < 500:
        score += 20
    annual_consumption = max(civ.get("last_food_consumption", pop), pop)
    if civ["food"] < annual_consumption * 0.20:
        score += 20
    env = get_civ_environment(civ)
    if env["water"] < 18:
        score += 15
    if civ["wealth"] < 2_000:
        score += 10
    if active_war_for_civ(civ) is not None:
        score += 15
    capital_idx = civ["y"] * WORLD_WIDTH + civ["x"]
    if not (0 <= capital_idx < len(territory_owner)) or territory_owner[capital_idx] != civ["id"]:
        score += 30
    if _territory_component_count(civ) >= 2:
        score += 10
    for d in active_disasters:
        if d.get("type", "").endswith("_after") or not d.get("large"):
            continue
        if disaster_overlap_fraction(civ, d, max_samples=50) >= 0.08:
            score += 10
            break
    if epidemic_for(civ["id"]) is not None:
        score += 10
    return clamp(score, 0, 120)


def collapse_state_label(score):
    if score < 20:
        return "안정"
    if score < 40:
        return "불안"
    if score < 60:
        return "위기"
    if score < 80:
        return "붕괴 위험"
    return "붕괴 가능"


def _random_country_color():
    return tuple(random.randint(65, 225) for _ in range(3))


def _successor_name(parent, suffix=None):
    world_state.successor_serial += 1
    if suffix:
        return f"{parent['name']} {suffix}"
    return f"신 {parent['name']} {world_state.successor_serial}"


def _country_from_parent(parent, name, tiles, population):
    tiles = set(tiles)
    if not tiles:
        return None
    xs = [idx % WORLD_WIDTH for idx in tiles]
    ys = [idx // WORLD_WIDTH for idx in tiles]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    capital_idx = min(tiles, key=lambda idx: (idx % WORLD_WIDTH - cx) ** 2 + (idx // WORLD_WIDTH - cy) ** 2)
    y, x = divmod(capital_idx, WORLD_WIDTH)
    new_id = len(civilizations)
    new_civ = Country({
        "id": new_id, "name": name, "color": _random_country_color(), "x": x, "y": y,
        "population": max(350, int(population)),
        "intelligence": clamp(parent["intelligence"] + random.uniform(-4, 2), 0, 100),
        "medical": clamp(parent["medical"] + random.uniform(-5, 1), 0, 100),
        "wealth": max(1000.0, parent["wealth"] * min(0.55, len(tiles) / max(len(parent.get("territory", ())), 1))),
        "food": max(1000.0, parent["food"] * min(0.55, len(tiles) / max(len(parent.get("territory", ())), 1))),
        "alive": True, "dead": False, "territory": set(tiles), "territory_revision": 0, "frontier": set(),
        "env_cache": None, "env_cache_year": -999999,
        "trade_bonus": {"food": 0.0, "wood": 0.0, "iron": 0.0, "minerals": 0.0, "oil": 0.0},
        "last_food_production": 0.0, "last_food_consumption": 0.0, "last_wealth_change": 0.0,
        "last_population_change": 0, "status": "신생국", "applied_disasters": set(),
        "war_cooldown_until": year + 30, "war_fatigue": 15.0, "poverty_years": 0,
        "famine_years": 0, "peace_years": 0, "last_war_damage": 0.0,
        "demographic_shock": 20.0,
        "cities": [], "events": [], "rank_history": [], "collapse_score": 0.0,
        "collapse_state": "불안", "collapse_risk_years": 0,
        "last_city_year": -999999, "last_capital_move_year": -999999,
        "resource_discovered": set(), "resource_depleted": set(),
        "history": {"year": [], "population": [], "wealth": [], "food": [], "medical": [],
                    "intelligence": [], "territory": [], "cities": [], "power": [], "collapse": [], "rank": []},
    })
    civilizations.append(new_civ)
    for idx in tiles:
        territory_owner[idx] = new_id
    _touch_territory(new_civ)
    _refresh_frontier_for(new_civ)
    event_history.append((year, f"🏴 {new_civ['name']} 건국 ({parent['name']} 붕괴 후 계승국)"))
    return new_civ


def _finalize_old_country(civ, reason):
    # 영토는 결과 처리 함수가 이미 재배분한 뒤 호출된다.
    civ["territory"].clear()
    civ["frontier"].clear()
    _touch_territory(civ)
    civ["former_cities"] = list(civ.get("cities", []))
    civ["cities"] = []
    extinct_civilization(civ, reason)
    civ["dead"] = True
    civ["death_year"] = year


def collapse_country(civ, forced=False):
    if not civ.get("alive", False):
        return
    old_tiles = set(civ.get("territory", ()))
    if not old_tiles:
        _finalize_old_country(civ, "영토 소멸")
        return
    others = [c for c in civilizations if c["id"] != civ["id"] and civ_alive(c)]
    neighbors = bordering_countries(civ)

    # 인구가 극단적으로 적을 때는 유령 successor를 만들지 않고 흡수/분할을 우선한다.
    if forced and civ["population"] <= EXTINCTION_POPULATION:
        outcome = "absorb" if neighbors else ("partition" if others else "successor")
    else:
        choices = ["successor"]
        if len(old_tiles) >= 14 and civ["population"] >= 1_200:
            choices += ["split"]
        if neighbors:
            choices += ["absorb"]
        if len(neighbors) >= 2:
            choices += ["partition"]
        outcome = random.choice(choices)

    parent_pop = max(civ["population"], 0)
    parent_wealth = civ["wealth"]
    parent_food = civ["food"]

    if outcome == "absorb" and (neighbors or others):
        candidates = neighbors or sorted(others, key=lambda c: math.hypot(c["x"]-civ["x"], c["y"]-civ["y"]))[:2]
        winner = max(candidates, key=lambda c: national_power_score(c))
        for idx in old_tiles:
            territory_owner[idx] = winner["id"]
            winner["territory"].add(idx)
        _touch_territory(winner)
        winner["population"] += int(parent_pop * 0.35)
        winner["wealth"] += parent_wealth * 0.30
        winner["food"] += parent_food * 0.25
        _refresh_frontier_for(winner)
        civ["territory"].clear()
        event_history.append((year, f"🏳️ {civ['name']} 붕괴 → {winner['name']}에 흡수"))
        _finalize_old_country(civ, "국가 붕괴·흡수")
        return

    if outcome == "partition" and len(neighbors) >= 2:
        receivers = sorted(neighbors, key=lambda c: national_power_score(c), reverse=True)[:3]
        counts = {r["id"]: 0 for r in receivers}
        for idx in old_tiles:
            y, x = divmod(idx, WORLD_WIDTH)
            r = min(receivers, key=lambda c: (c["x"]-x)**2 + (c["y"]-y)**2)
            territory_owner[idx] = r["id"]
            r["territory"].add(idx)
            counts[r["id"]] += 1
        for r in receivers:
            frac = counts[r["id"]] / max(len(old_tiles), 1)
            r["population"] += int(parent_pop * frac * 0.28)
            r["wealth"] += parent_wealth * frac * 0.25
            _touch_territory(r)
            _refresh_frontier_for(r)
        civ["territory"].clear()
        event_history.append((year, f"🏳️ {civ['name']} 붕괴 → 주변 {len(receivers)}개국이 영토 분할"))
        _finalize_old_country(civ, "국가 붕괴·영토 분할")
        return

    if outcome == "split" and len(old_tiles) >= 14:
        xs = [idx % WORLD_WIDTH for idx in old_tiles]
        ys = [idx // WORLD_WIDTH for idx in old_tiles]
        split_x = (max(xs)-min(xs)) >= (max(ys)-min(ys))
        ordered = sorted(old_tiles, key=lambda idx: (idx % WORLD_WIDTH) if split_x else (idx // WORLD_WIDTH))
        mid = len(ordered)//2
        part_a, part_b = set(ordered[:mid]), set(ordered[mid:])
        if len(part_a) >= 4 and len(part_b) >= 4:
            # 구 객체 영토를 먼저 비워 id 충돌 없이 successor가 소유권을 다시 기록.
            civ["territory"].clear()
            _touch_territory(civ)
            a = _country_from_parent(civ, _successor_name(civ, "동부국"), part_a, parent_pop * len(part_a)/len(old_tiles))
            b = _country_from_parent(civ, _successor_name(civ, "서부국"), part_b, parent_pop * len(part_b)/len(old_tiles))
            event_history.append((year, f"🏳️ {civ['name']} 붕괴 → {a['name']}·{b['name']}로 분열"))
            _finalize_old_country(civ, "국가 붕괴·분열")
            return

    # 기본: 기존 국가가 사라지고 하나의 계승국이 등장.
    civ["territory"].clear()
    _touch_territory(civ)
    successor = _country_from_parent(civ, _successor_name(civ), old_tiles, max(parent_pop * 0.65, 500))
    event_history.append((year, f"🏳️ {civ['name']} 붕괴 → {successor['name']} 성립"))
    _finalize_old_country(civ, "국가 붕괴·정권 교체")


def update_collapse_system():
    for civ in list(civilizations):
        if not civ_alive(civ):
            continue
        score = calculate_collapse_score(civ)
        civ["collapse_score"] = score
        civ["collapse_state"] = collapse_state_label(score)
        if score >= 80:
            civ["collapse_risk_years"] = civ.get("collapse_risk_years", 0) + 1
        else:
            civ["collapse_risk_years"] = max(0, civ.get("collapse_risk_years", 0) - 1)

        if civ["population"] <= EXTINCTION_POPULATION:
            extinct_civilization(civ, "인구 기반 소멸")
            continue
        if not civ.get("territory"):
            extinct_civilization(civ, "영토 소멸")
            continue
        if score >= 80 and civ.get("collapse_risk_years", 0) >= 2:
            collapse_probability = min(0.8, score / 100.0)
            if random.random() < collapse_probability:
                collapse_country(civ)


def compute_world_ranking():
    alive = [c for c in civilizations if civ_alive(c)]
    if not alive:
        return []
    max_pop = max(c["population"] for c in alive) or 1
    max_wealth = max(c["wealth"] for c in alive) or 1
    max_territory = max(len(c.get("territory", ())) for c in alive) or 1
    result = []
    for c in alive:
        pop_n = c["population"] / max_pop * 100
        wealth_n = c["wealth"] / max_wealth * 100
        food_n = clamp(c["food"] / max(c["population"] * 4.0, 1) * 100, 0, 100)
        territory_n = len(c.get("territory", ())) / max_territory * 100
        score = (
            pop_n * 0.30 + wealth_n * 0.25 + food_n * 0.15
            + c["medical"] * 0.10 + c["intelligence"] * 0.10 + territory_n * 0.10
        )
        result.append((c, score))
    result.sort(key=lambda item: item[1], reverse=True)
    return result


def national_power_score(civ):
    if not civ_alive(civ):
        return 0.0
    for c, score in compute_world_ranking():
        if c["id"] == civ["id"]:
            return score
    return 0.0


def update_resource_discovery_and_extraction():
    """비재생 자원은 아주 천천히 줄고, 최초 발견/고갈을 역사에 남긴다.
    같은 영토 표본을 철/광물/석유별로 세 번 훑지 않고 한 번에 모은다.
    """
    if year % 5 != 0:
        return
    resources = (("iron", iron_map, "철광산", 220, 20),
                 ("minerals", mineral_map, "광물지대", 300, 30),
                 ("oil", oil_map, "유전", 700, 70))

    for civ in civilizations:
        if not civ_alive(civ) or not civ.get("territory"):
            continue
        civ.setdefault("resource_discovered", set())
        civ.setdefault("resource_depleted", set())
        tiles = list(civ["territory"])
        if len(tiles) > 220:
            tiles = random.sample(tiles, 220)

        rich_by_key = {key: [] for key, *_ in resources}
        max_by_key = {key: 0 for key, *_ in resources}
        for idx in tiles:
            y, x = divmod(idx, WORLD_WIDTH)
            for key, grid, _label, _discover, _depleted in resources:
                val = grid[y][x]
                if val > 0:
                    if val > max_by_key[key]:
                        max_by_key[key] = val
                    rich_by_key[key].append((val, x, y))

        can_extract = development_level(civ) >= 35
        extraction = int(clamp(civ["population"] * (0.00004 + civ["intelligence"] * 0.0000005), 1, 80)) if can_extract else 0

        for key, grid, label, discover_threshold, depleted_threshold in resources:
            rich = rich_by_key[key]
            max_val = max_by_key[key]
            if max_val >= discover_threshold and key not in civ["resource_discovered"]:
                civ["resource_discovered"].add(key)
                best = max(rich) if rich else (0, civ["x"], civ["y"])
                event_history.append((year, f"⛏️ {civ['name']} {label} 발견 ({best[1]},{best[2]})"))

            if rich and can_extract:
                # 전체 정렬 대신 상위 후보만 필요하지만 표본이 최대 220이라 nlargest가 더 가볍다.
                top_rich = heapq.nlargest(8, rich)
                left = extraction
                for val, x, y in top_rich:
                    if left <= 0:
                        break
                    take = min(grid[y][x], max(1, left // 2))
                    grid[y][x] -= take
                    left -= take

            if key in civ["resource_discovered"] and max_val <= depleted_threshold and key not in civ["resource_depleted"]:
                civ["resource_depleted"].add(key)
                event_history.append((year, f"⛏️ {civ['name']} {label} 주요 매장지 고갈"))


def extinct_civilization(civ, reason="인구 붕괴"):
    """문명이 생존 한계 이하로 내려가면 흔적 없이 게임 시스템에서 제거한다.

    civilizations 리스트의 슬롯 자체는 territory_owner의 국가 ID 인덱스를 보존하기 위해
    남겨 두지만, 살아 있는 국가로는 절대 취급되지 않는다.
    """
    if not civ.get("alive", True):
        return

    civ["alive"] = False
    civ["dead"] = True
    civ["death_year"] = year
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
    _touch_territory(civ)

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
    """극단적 저인구는 계승국 없이 완전 멸망 처리한다.

    보통의 정치·경제 붕괴는 collapse_country()가 분열/흡수/계승을 만들 수 있지만,
    인구가 생존선 이하까지 내려간 경우에는 즉시 새 국가가 생겨 폭발적으로 재성장하는 현상을 막는다.
    """
    for civ in list(civilizations):
        if not civ.get("alive", True):
            continue
        if civ["population"] <= EXTINCTION_POPULATION:
            extinct_civilization(civ, "인구 기반 소멸")
        elif not civ.get("territory"):
            extinct_civilization(civ, "영토 소멸")


def simulate_civilizations():
    # 같은 해에 active_wars를 국가마다 반복 탐색하지 않는다.
    war_by_civ = {}
    for w in active_wars:
        war_by_civ[w["a"]] = w
        war_by_civ[w["b"]] = w

    # 연간 변화량 초기화 + 전쟁 후유증 회복
    for civ in civilizations:
        civ["last_population_change"] = 0
        civ["last_wealth_change"] = 0.0
        civ["last_war_damage"] = 0.0
        # 전쟁/전염병의 인구 충격은 수십 년에 걸쳐 천천히 회복된다.
        civ["demographic_shock"] = max(0.0, civ.get("demographic_shock", 0.0) - random.uniform(1.2, 2.2))
        if civ_alive(civ):
            current_war = war_by_civ.get(civ["id"])
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

    # 전염병 갱신 후 현재 상태를 한 번만 인덱싱한다.
    epidemic_by_civ = {e["civ_id"]: e for e in active_epidemics}
    droughts = [d for d in active_disasters if d["type"] == "drought"]

    for civ in civilizations:
        if not civ_alive(civ):
            continue

        env = get_civ_environment(civ)
        pop = civ["population"]
        intel = civ["intelligence"]
        medical = civ["medical"]
        war = war_by_civ.get(civ["id"])
        epidemic = epidemic_by_civ.get(civ["id"])
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

        # 전염병 중에는 노동력·운송·도시 활동이 동시에 위축된다.
        epidemic_prod_mult = 1.0
        if epidemic is not None:
            epidemic_prod_mult = clamp(0.82 - epidemic.get("strength", 1.0) * 0.07, 0.68, 0.80)

        food_production = pop * food_per_person * war_prod_mult * epidemic_prod_mult
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

        storage_capacity = pop * (16.0 + civ["intelligence"] * 0.16)
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
        if epidemic is not None:
            production *= clamp(0.78 - epidemic.get("strength", 1.0) * 0.06, 0.62, 0.74)
            maintenance *= 1.10

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
        # 평화롭고 식량/의료/경제가 안정적이면 인구가 눈에 띄게 증가한다.
        growth = 0.0028 + 0.0058 * food_security + 0.0036 * (civ["medical"] / 100) + 0.0024 * wealth_security
        if war is None and civ.get("peace_years", 0) >= 20:
            growth += 0.0018
        if war is None and civ.get("peace_years", 0) >= 60:
            growth += 0.0012
        if war is None and civ.get("peace_years", 0) >= 120:
            growth += 0.0008

        if war is not None:
            growth -= 0.010 + fatigue * 0.000065
        if epidemic is not None:
            # 전염병 피해를 받은 같은 해에 저밀도/평화 보너스로 인구가 다시 늘어나는 모순을 차단한다.
            growth -= 0.012 + epidemic.get("strength", 1.0) * 0.005
        if civ["food"] < pop * 1.5:
            growth -= 0.007
        if civ["food"] < pop * 0.6:
            growth -= 0.020
        if civ["food"] < pop * 0.2:
            growth -= 0.035
        if civ["poverty_years"] > 8:
            growth -= 0.006

        for d in droughts:
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
        if density_ratio > 0.78:
            growth -= 0.0026 * ((density_ratio - 0.78) / 0.22)
        if density_ratio > 0.94:
            growth -= 0.008 * ((density_ratio - 0.94) / 0.06)
        if density_ratio > 1.0:
            growth -= 0.035 * min(density_ratio - 1.0, 1.5)
        if density_ratio > 1.20:
            growth -= 0.025 * min(density_ratio - 1.20, 1.2)

        # 반대로 영토만 지나치게 넓고 인구가 너무 적을 때는 약한 회복 여지를 주되,
        # 최근 전쟁/전염병 충격이 남아 있으면 이 보너스를 주지 않는다.
        demographic_shock = civ.get("demographic_shock", 0.0)
        if density_ratio < 0.62 and food_security > 0.65 and wealth_security > 0.45 and war is None and epidemic is None and demographic_shock < 12:
            growth += 0.0012

        # 큰 인구 충격 뒤의 비현실적인 폭발적 반등을 제한한다.
        if demographic_shock >= 60:
            growth = min(growth, 0.0010)
        elif demographic_shock >= 40:
            growth = min(growth, 0.0025)
        elif demographic_shock >= 20:
            growth = min(growth, 0.0050)
        elif demographic_shock >= 10:
            growth = min(growth, 0.0080)

        # 전염병이 진행 중인 해에는 전체 인구가 절대로 증가하지 않는다.
        if epidemic is not None:
            growth = min(growth, -0.003)

        growth = clamp(growth, -0.070, 0.0180)
        old = civ["population"]
        civ["population"] = max(0, int(civ["population"] * (1 + growth)))
        civ["last_population_change"] += civ["population"] - old

    check_extinctions()
    expand_territories()
    update_interactions()
    update_wars()
    # 전쟁/재난 결과를 반영한 뒤 붕괴를 판정하고, 살아남은 나라에서 도시/자원 시스템을 갱신한다.
    update_collapse_system()
    update_cities()
    update_resource_discovery_and_extraction()
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
        f"도시: {sum(1 for city in civ.get('cities', []) if city.alive and city.stage >= 1)}개 · 붕괴: {civ.get('collapse_state', '안정')} ({civ.get('collapse_score', 0):.0f})",
        f"세계 국력: {national_power_score(civ):.1f}점",
        f"인구 밀도: {civ['population'] / max(len(civ.get('territory', ())), 1):,.0f}명/칸 · 적정 {ideal_people_per_tile(civ):,.0f}명/칸",
        f"인구 수용력: 약 {estimated_carrying_capacity(civ):,.0f}명",
        f"군사력: {military_power(civ):.1f}/100 · 자원력: {territory_resource_strength(civ):.2f}",
        f"접경국: {len(bordering_countries(civ))}개",
        f"전쟁 조건: {war_lock_reason(civ)}",
        f"전쟁 범위: 약 {war_range(civ):.0f}칸 · 시대 전쟁계수 {war_era_chance_multiplier():.2f}",
        f"식량 생산/소비: {civ['last_food_production']:,.0f}/{civ['last_food_consumption']:,.0f}",
        f"빈곤 누적: {civ.get('poverty_years', 0)}년 · 기근 누적: {civ.get('famine_years', 0)}년",
        f"인구 충격: {civ.get('demographic_shock', 0):.0f}/100",
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
    활성 재해 구성이 전년도와 같으면 배율 지도도 완전히 같으므로 재계산하지 않는다.
    """
    global multiplier_maps, _multiplier_signature

    active_effects = [d for d in active_disasters if d["start_year"] <= year <= d["end_year"]]
    signature = tuple(d.get("event_id", id(d)) for d in active_effects)
    if _multiplier_signature == signature and "multiplier_maps" in globals():
        return
    _multiplier_signature = signature

    multiplier_maps = {
        "food": {},
        "water": {},
        "wood": {},
        "mining": {}
    }

    width = WORLD_WIDTH
    height = WORLD_HEIGHT
    maps = multiplier_maps
    for d in active_effects:
        cx, cy, radius = d["x"], d["y"], d["radius"]
        r2 = radius * radius
        y0 = max(0, cy - radius)
        y1 = min(height - 1, cy + radius)
        x0 = max(0, cx - radius)
        x1 = min(width - 1, cx + radius)
        effects = d["effects"].items()

        for ny in range(y0, y1 + 1):
            dy = ny - cy
            dy2 = dy * dy
            row_base = ny * width
            for nx in range(x0, x1 + 1):
                dx = nx - cx
                if dx * dx + dy2 > r2:
                    continue
                idx = row_base + nx
                for resource, mult in effects:
                    target = maps.get(resource)
                    if target is not None:
                        target[idx] = target.get(idx, 1.0) * mult


# ==================================================
# 1년 진행
# ==================================================

def _advance_year_core():
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


def advance_year():
    """외부에서 호출하는 1년 진행 진입점. World.simulate_year()이 전체 순서를 관리한다."""
    world_state.simulate_year()


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
        before = start_snapshot.get(civ["id"])
        after_pop = civ["population"]
        after_territory = len(civ.get("territory", ()))
        if before is None:
            if civ_alive(civ):
                country_changes.append(f"{civ['name']}: 이 기간 중 건국 | 인구 {after_pop:,} | 영토 {after_territory}칸")
            continue
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



def _compact_amount(value):
    value = float(value)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    if value >= 100:
        return f"{value:.0f}"
    return f"{value:.1f}"


def _build_block_bubbles(mode, grid, block=RESOURCE_BUBBLE_BLOCK):
    """식량/물/목재처럼 넓게 퍼지는 자원은 작은 타일을 전부 칠하지 않고
    block×block 구역을 하나의 원으로 묶어 위치와 총량을 보여준다.
    """
    bubbles = []
    # 너무 미세한 곳까지 원이 가득 차는 걸 막기 위한 약한 하한선.
    grid_peak = max(max(row) for row in grid) if grid else 1
    threshold_per_tile = grid_peak * (0.10 if mode in ("food", "water") else 0.07)

    for y0 in range(0, WORLD_HEIGHT, block):
        for x0 in range(0, WORLD_WIDTH, block):
            total = 0.0
            weighted_x = 0.0
            weighted_y = 0.0
            count = 0
            local_peak = 0.0
            for y in range(y0, min(y0 + block, WORLD_HEIGHT)):
                row = grid[y]
                for x in range(x0, min(x0 + block, WORLD_WIDTH)):
                    v = float(row[x])
                    if v <= 0:
                        continue
                    total += v
                    weighted_x += (x + 0.5) * v
                    weighted_y += (y + 0.5) * v
                    local_peak = max(local_peak, v)
                    count += 1
            if count == 0 or total <= 0:
                continue
            avg = total / max(count, 1)
            if avg < threshold_per_tile:
                continue
            cx = weighted_x / total
            cy = weighted_y / total
            bubbles.append({
                "x": cx,
                "y": cy,
                "value": total,
                "peak": local_peak,
                "tiles": count,
                "kind": "area",
            })
    return bubbles


def _build_deposit_bubbles(grid):
    """철/광물/석유는 서로 이어진 양수 타일을 하나의 실제 매장지로 묶는다."""
    visited = bytearray(WORLD_WIDTH * WORLD_HEIGHT)
    bubbles = []
    neighbors = ((1, 0), (-1, 0), (0, 1), (0, -1))

    for y0 in range(WORLD_HEIGHT):
        for x0 in range(WORLD_WIDTH):
            start_idx = y0 * WORLD_WIDTH + x0
            if visited[start_idx] or grid[y0][x0] <= 0:
                continue

            queue = [start_idx]
            visited[start_idx] = 1
            pos = 0
            total = 0.0
            wx = 0.0
            wy = 0.0
            peak = 0.0
            tiles = 0

            while pos < len(queue):
                idx = queue[pos]
                pos += 1
                y, x = divmod(idx, WORLD_WIDTH)
                v = float(grid[y][x])
                if v <= 0:
                    continue
                total += v
                wx += (x + 0.5) * v
                wy += (y + 0.5) * v
                peak = max(peak, v)
                tiles += 1

                for dx, dy in neighbors:
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < WORLD_WIDTH and 0 <= ny < WORLD_HEIGHT):
                        continue
                    nidx = ny * WORLD_WIDTH + nx
                    if not visited[nidx] and grid[ny][nx] > 0:
                        visited[nidx] = 1
                        queue.append(nidx)

            if total > 0 and tiles > 0:
                bubbles.append({
                    "x": wx / total,
                    "y": wy / total,
                    "value": total,
                    "peak": peak,
                    "tiles": tiles,
                    "kind": "deposit",
                })
    return bubbles


def build_resource_bubbles():
    """1~6 자원을 모두 원 크기로 비교할 수 있도록 표시용 데이터를 미리 만든다."""
    global resource_bubbles, resource_bubble_max
    resource_bubbles = {
        "food": _build_block_bubbles("food", food_map),
        "water": _build_block_bubbles("water", water_map),
        "wood": _build_block_bubbles("wood", wood_map),
        "iron": _build_deposit_bubbles(iron_map),
        "minerals": _build_deposit_bubbles(mineral_map),
        "oil": _build_deposit_bubbles(oil_map),
    }
    resource_bubble_max = {
        key: max((b["value"] for b in bubbles), default=1.0)
        for key, bubbles in resource_bubbles.items()
    }


def draw_resource_bubbles(surface, mode, tile_size, camera_x, camera_y):
    """현재 자원 모드의 원형 분포도를 그린다.
    원의 위치=자원 위치, 원의 크기=해당 구역/매장지 총량, 숫자=총량.
    """
    bubbles = resource_bubbles.get(mode, ())
    if not bubbles:
        return

    color = OVERLAY_COLORS[mode]
    max_value = max(resource_bubble_max.get(mode, 1.0), 1.0)
    layer = pygame.Surface((MAP_WIDTH, HEIGHT), pygame.SRCALPHA)

    # 화면에 보이는 원만 그린다.
    for b in bubbles:
        sx = b["x"] * tile_size - camera_x
        sy = b["y"] * tile_size - camera_y
        t = clamp(math.sqrt(max(b["value"], 0.0) / max_value), 0.0, 1.0)

        # 확대/축소해도 너무 작거나 거대해지지 않는 화면 기준 반지름.
        zoom_factor = clamp(0.72 + zoom * 0.28, 0.72, 1.35)
        radius = int((4.0 + 19.0 * t) * zoom_factor)
        radius = int(clamp(radius, 4, 30))

        if sx + radius < 0 or sx - radius > MAP_WIDTH or sy + radius < 0 or sy - radius > HEIGHT:
            continue

        center = (int(sx), int(sy))
        # 반투명 내부 + 밝은 테두리 + 흰색 바깥선으로 어두운 지형에서도 잘 보이게 한다.
        pygame.draw.circle(layer, (*color, 105), center, radius)
        pygame.draw.circle(layer, (*color, 235), center, radius, max(2, radius // 6))
        pygame.draw.circle(layer, (255, 255, 255, 210), center, radius + 1, 1)

        # 큰 원은 수치를 바로 표시. 축소 상태에서는 숫자 과밀을 방지한다.
        if radius >= 10 and zoom >= 0.45:
            label = small_font.render(_compact_amount(b["value"]), True, (255, 255, 255))
            lx = int(sx - label.get_width() / 2)
            ly = int(sy - label.get_height() / 2)
            bg = pygame.Surface((label.get_width() + 4, label.get_height() + 2), pygame.SRCALPHA)
            bg.fill((20, 20, 25, 150))
            layer.blit(bg, (lx - 2, ly - 1))
            layer.blit(label, (lx, ly))

    surface.blit(layer, (0, 0))

def generate_resources():

    global iron_map, mineral_map, oil_map, resource_max
    global year, active_disasters, event_history, disaster_event_serial, _multiplier_signature

    compute_coast()
    compute_desert_near_mountain()
    compute_disaster_environment()

    year = 0
    active_disasters = []
    _multiplier_signature = None
    event_history = EventLog()
    world_state.reset()
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

    # 자원 지도는 생성 직후 한 번만 묶어서 계산한다. 화면에서는 이 캐시만 사용하므로 빠르다.
    build_resource_bubbles()

    recompute_multipliers()
    build_disaster_risk_pools()
    generate_civilizations()
    update_cities()
    world_state.record_year()


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

    river_count = random.randint(10, 18)

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

show_world_history = False
show_ranking = False
selected_country_id = None
country_graph_metric = "population"


# ==================================================
# 글꼴
# ==================================================

font = pygame.font.SysFont("malgungothic", 19)
small_font = pygame.font.SysFont("malgungothic", 14)
title_font = pygame.font.SysFont("malgungothic", 23, bold=True)


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


def _event_icon(event_type):
    return {
        "country_create": "🏴", "collapse": "🏳", "city": "●", "village": "·", "metropolis": "◎",
        "capital_move": "👑", "trade": "🤝", "war_start": "⚔", "peace": "🕊", "flood": "🌧",
        "drought": "🌵", "volcano": "🌋", "earthquake": "🌎", "storm": "🌪", "fire": "🔥",
        "epidemic": "🦠", "resource": "⛏", "ranking": "🏆"
    }.get(event_type, "•")


def draw_country_history_graph(surface, civ, metric, rect):
    hist = civ.get("history", {})
    years = hist.get("year", [])
    values = hist.get(metric, [])
    pygame.draw.rect(surface, (38, 40, 48), rect)
    pygame.draw.rect(surface, (120, 125, 140), rect, 1)
    if len(years) < 2 or len(values) < 2:
        msg = small_font.render("아직 그래프 데이터가 부족합니다.", True, (210, 210, 215))
        surface.blit(msg, (rect.x + 14, rect.y + 14))
        return

    # 화면 폭보다 데이터가 많으면 균등 표본. 원본 history는 전부 보존한다.
    max_points = max(80, rect.w - 25)
    if len(years) > max_points:
        step = len(years) / max_points
        idxs = [min(len(years)-1, int(i * step)) for i in range(max_points)]
    else:
        idxs = list(range(len(years)))
    ys = [years[i] for i in idxs]
    vs = [values[i] for i in idxs]
    vmin, vmax = min(vs), max(vs)
    if vmax <= vmin:
        vmax = vmin + 1
    xmin, xmax = ys[0], ys[-1]
    if xmax <= xmin:
        xmax = xmin + 1

    points = []
    for yy, vv in zip(ys, vs):
        px = rect.x + 8 + (yy - xmin) / (xmax - xmin) * (rect.w - 16)
        py = rect.bottom - 8 - (vv - vmin) / (vmax - vmin) * (rect.h - 20)
        points.append((int(px), int(py)))

    # 전쟁/재난/전염병/붕괴 이벤트를 세로선으로 표시한다.
    for ev in civ.get("events", []):
        if ev.year < xmin or ev.year > xmax:
            continue
        if ev.type not in ("war_start", "collapse", "epidemic", "flood", "drought", "volcano", "earthquake", "storm", "fire"):
            continue
        ex = int(rect.x + 8 + (ev.year - xmin) / (xmax - xmin) * (rect.w - 16))
        pygame.draw.line(surface, (105, 78, 82), (ex, rect.y + 4), (ex, rect.bottom - 4), 1)

    if len(points) >= 2:
        pygame.draw.lines(surface, (125, 205, 245), False, points, 2)
    surface.blit(small_font.render(f"{xmin}년", True, (170, 175, 185)), (rect.x + 6, rect.bottom - 19))
    right_label = small_font.render(f"{xmax}년", True, (170, 175, 185))
    surface.blit(right_label, (rect.right - right_label.get_width() - 6, rect.bottom - 19))
    surface.blit(small_font.render(f"최소 {vmin:,.0f} / 최대 {vmax:,.0f}", True, (185, 190, 200)), (rect.x + 8, rect.y + 5))


def draw_country_dashboard(surface, civ, metric):
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shade.fill((12, 14, 20, 225))
    surface.blit(shade, (0, 0))
    x, y, w, h = 55, 35, WIDTH - 110, HEIGHT - 70
    pygame.draw.rect(surface, (30, 33, 42), (x, y, w, h))
    pygame.draw.rect(surface, civ.get("color", (180,180,180)), (x, y, w, h), 2)
    title = title_font.render(f"🏛 {civ['name']} 국가 기록", True, (245, 245, 250))
    surface.blit(title, (x + 20, y + 16))
    status = f"현재: {'존속' if civ_alive(civ) else '멸망'} · 인구 {civ.get('population',0):,} · 영토 {len(civ.get('territory',())):,}칸 · 도시 {sum(1 for c in civ.get('cities',[]) if c.alive and c.stage>=1)}개"
    draw_wrapped_text(surface, status, small_font, (205, 210, 220), x+20, y+49, w-40, 18, 2)

    labels = {"population":"인구", "wealth":"재산", "food":"식량", "territory":"영토", "medical":"의료", "intelligence":"지능"}
    keys = [("1","population"),("2","wealth"),("3","food"),("4","territory"),("5","medical"),("6","intelligence")]
    selector = "   ".join(f"[{k} {labels[m]}]" + (" ◀" if m == metric else "") for k,m in keys)
    surface.blit(small_font.render(selector, True, (230, 220, 150)), (x+20, y+79))
    surface.blit(font.render(f"{labels.get(metric, metric)} 변화", True, (150, 215, 255)), (x+20, y+105))
    graph_rect = pygame.Rect(x+20, y+135, int(w*0.62), h-175)
    draw_country_history_graph(surface, civ, metric, graph_rect)

    hx = graph_rect.right + 22
    hy = y + 108
    surface.blit(font.render("주요 국가 역사", True, (245, 205, 125)), (hx, hy))
    hy += 30
    events = civ.get("events", [])[-16:]
    if not events:
        surface.blit(small_font.render("기록된 사건이 없습니다.", True, (180,180,185)), (hx, hy))
    else:
        for ev in reversed(events):
            if hy > y+h-58:
                break
            line = f"{_event_icon(ev.type)} {ev.year}년  {ev.text}"
            hy = draw_wrapped_text(surface, line, small_font, (215,218,225), hx, hy, x+w-hx-18, 17, 2) + 3
    surface.blit(small_font.render("1~6: 그래프 변경 · ESC/우클릭: 닫기", True, (155,160,170)), (x+20, y+h-27))


def draw_world_history_overlay(surface):
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shade.fill((10, 12, 18, 235))
    surface.blit(shade, (0, 0))
    surface.blit(title_font.render("━━━━━━━━ 세계 연대기 ━━━━━━━━", True, (245,220,145)), (55, 28))
    y = 72
    for ev in reversed(world_state.events[-30:]):
        if y > HEIGHT - 38:
            break
        line = f"{ev.year:>4}년  {_event_icon(ev.type)} {ev.text}"
        y = draw_wrapped_text(surface, line, small_font, (225,228,235), 60, y, WIDTH-120, 18, 2) + 3
    surface.blit(small_font.render("H 또는 ESC: 닫기", True, (160,165,175)), (WIDTH-180, 30))


def draw_ranking_overlay(surface):
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shade.fill((10, 12, 18, 235))
    surface.blit(shade, (0, 0))
    surface.blit(title_font.render("🏆 WORLD RANKING", True, (250,215,105)), (65, 35))
    ranking = compute_world_ranking()
    y = 90
    for i, (civ, score) in enumerate(ranking, start=1):
        change = civ.get("rank_change", 0)
        arrow = f" ↑{change}" if change > 0 else (f" ↓{-change}" if change < 0 else "")
        line = f"{i:>2}   {civ['name']:<14}  {score:5.1f}점{arrow}   인구 {civ['population']:,}   영토 {len(civ.get('territory',())):,}"
        surface.blit(font.render(line, True, civ.get("color", (230,230,230))), (75, y))
        y += 42
    surface.blit(small_font.render("Q 또는 ESC: 닫기", True, (160,165,175)), (WIDTH-180, 38))


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

            if event.key == pygame.K_ESCAPE:
                show_world_history = False
                show_ranking = False
                selected_country_id = None
                show_summary = False

            elif selected_country_id is not None:
                metric_keys = {
                    pygame.K_1: "population", pygame.K_2: "wealth", pygame.K_3: "food",
                    pygame.K_4: "territory", pygame.K_5: "medical", pygame.K_6: "intelligence"
                }
                if event.key in metric_keys:
                    country_graph_metric = metric_keys[event.key]

            elif show_world_history:
                if event.key == pygame.K_h:
                    show_world_history = False

            elif show_ranking:
                if event.key == pygame.K_q:
                    show_ranking = False

            elif event.key == pygame.K_h:
                show_world_history = True
                show_ranking = False
                auto_play = False

            elif event.key == pygame.K_q:
                show_ranking = True
                show_world_history = False
                auto_play = False

            elif event.key == pygame.K_r:
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

            if event.button == 3:
                # 우클릭: 국가 기록/그래프 열기. 이미 열려 있으면 닫기.
                if selected_country_id is not None:
                    selected_country_id = None
                elif not (show_world_history or show_ranking):
                    mx, my = pygame.mouse.get_pos()
                    if 0 <= mx < MAP_WIDTH and 0 <= my < HEIGHT:
                        ts = BASE_TILE_SIZE * zoom
                        tx = int((camera_x + mx) / ts)
                        ty = int((camera_y + my) / ts)
                        civ = find_civilization_at(tx, ty) if 0 <= tx < WORLD_WIDTH and 0 <= ty < WORLD_HEIGHT else None
                        if civ is not None:
                            selected_country_id = civ["id"]
                            country_graph_metric = "population"
                            auto_play = False

            elif event.button == 1 and not (show_world_history or show_ranking or selected_country_id is not None):
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
    ui_modal_open = show_world_history or show_ranking or selected_country_id is not None or show_summary

    if not ui_modal_open and (keys[pygame.K_w] or keys[pygame.K_UP]):
        camera_y -= move_speed
    if not ui_modal_open and (keys[pygame.K_s] or keys[pygame.K_DOWN]):
        camera_y += move_speed
    if not ui_modal_open and (keys[pygame.K_a] or keys[pygame.K_LEFT]):
        camera_x -= move_speed
    if not ui_modal_open and (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
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

        # 자원 모드는 지형을 옅게 남기고, 자원량은 원의 크기로 표시한다.
        # 예전 히트맵보다 위치/규모를 한눈에 비교하기 쉽고 석유도 밝게 보인다.
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                terrain = world[y][x]
                if terrain == "water":
                    color = (38, 72, 115)
                else:
                    color = lerp_color(TERRAIN_COLORS[terrain], (55, 58, 62), 0.62)

                screen_x = x * tile_size - camera_x
                screen_y = y * tile_size - camera_y
                pygame.draw.rect(
                    screen, color,
                    (screen_x, screen_y, tile_size + 1, tile_size + 1)
                )

        draw_resource_bubbles(screen, overlay_mode, tile_size, camera_x, camera_y)


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

    # 도시 표시: · 마을 / ● 도시 / ◎ 대도시 / ★ 수도
    for civ in civilizations:
        if not civ_alive(civ):
            continue
        for city in civ.get("cities", []):
            if not city.alive or (city.stage < 1 and not city.capital):
                continue
            sx = city.x * tile_size - camera_x
            sy = city.y * tile_size - camera_y
            if not (-20 <= sx <= MAP_WIDTH + 20 and -20 <= sy <= HEIGHT + 20):
                continue
            symbol = city.symbol
            if not symbol:
                continue
            city_font = font if (city.capital or city.stage >= 3) else small_font
            # 검은 그림자 후 밝은 기호를 올려 어떤 지형에서도 잘 보이게 한다.
            shadow = city_font.render(symbol, True, (20, 20, 24))
            glyph = city_font.render(symbol, True, (255, 245, 215) if city.capital else (245, 245, 245))
            screen.blit(shadow, (int(sx - shadow.get_width()/2 + 1), int(sy - shadow.get_height()/2 + 1)))
            screen.blit(glyph, (int(sx - glyph.get_width()/2), int(sy - glyph.get_height()/2)))
            if tile_size >= 10 and city.stage >= 2 and not city.capital:
                city_label = small_font.render(city.stage_name, True, (245,245,245))
                screen.blit(city_label, (int(sx + 6), int(sy - 14)))
    screen.set_clip(None)


    # ==================================================
    # 오른쪽 정보 패널 - 핵심 정보만 표시
    # ==================================================

    pygame.draw.rect(screen, (245, 245, 245), (MAP_WIDTH, 0, INFO_WIDTH, HEIGHT))
    pygame.draw.line(screen, (105, 105, 105), (MAP_WIDTH, 0), (MAP_WIDTH, HEIGHT), 2)

    panel_x = MAP_WIDTH + 16
    panel_w = INFO_WIDTH - 32

    # 상단: 연도 / 현재 보기 모드 / 세계 전체 핵심 수치
    mode_label = "지형" if overlay_mode is None else ("국가 영토" if overlay_mode == "territory" else OVERLAY_NAMES[overlay_mode])
    screen.blit(title_font.render(f"{year}년 · {mode_label}", True, (20, 20, 25)), (panel_x, 14))

    alive_now = [c for c in civilizations if civ_alive(c)]
    total_population_now = sum(c["population"] for c in alive_now)
    auto_label = "자동 ON" if auto_play else "자동 OFF"
    top_line = f"{auto_label} · 국가 {len(alive_now)}개 · 인구 {total_population_now:,}명"
    screen.blit(small_font.render(top_line, True, (55, 70, 85)), (panel_x, 45))

    # 조작법은 두 줄만 유지한다.
    y_cursor = 70
    y_cursor = draw_wrapped_text(
        screen, "이동 WASD/방향키/드래그 · 휠 확대 · T 1년 · P 자동 · F 100년",
        small_font, (70, 70, 70), panel_x, y_cursor, panel_w, 16, max_lines=2
    )
    y_cursor = draw_wrapped_text(
        screen, "0 지형 · 1~6 자원 · 7/G 영토 · H 연대기 · Q 순위 · 우클릭 국가그래프",
        small_font, (70, 70, 70), panel_x, y_cursor, panel_w, 16, max_lines=2
    ) + 6

    # 영토 모드에서만 국가 색 범례를 표시한다.
    if overlay_mode == "territory":
        screen.blit(font.render("국가 영토", True, (25, 25, 30)), (panel_x, y_cursor))
        y_cursor += 24
        alive_territory_civs = get_alive_civilizations_sorted()
        col_gap = 8
        col_w = (panel_w - col_gap) // 2
        row_h = 34
        for i, civ in enumerate(alive_territory_civs):
            col = i % 2
            row = i // 2
            x0 = panel_x + col * (col_w + col_gap)
            y0 = y_cursor + row * row_h
            pygame.draw.rect(screen, civ["color"], (x0, y0 + 2, 13, 13))
            pygame.draw.rect(screen, (70, 70, 70), (x0, y0 + 2, 13, 13), 1)
            label = f"{civ['name']} {len(civ.get('territory', ())):,}칸"
            draw_wrapped_text(screen, label, small_font, (30, 30, 30), x0 + 18, y0, col_w - 20, 15, max_lines=2)
        rows = (len(alive_territory_civs) + 1) // 2
        y_cursor += rows * row_h + 6
    elif overlay_mode is not None:
        rc = OVERLAY_COLORS[overlay_mode]
        pygame.draw.circle(screen, rc, (panel_x + 8, y_cursor + 8), 7)
        pygame.draw.circle(screen, (70, 70, 70), (panel_x + 8, y_cursor + 8), 7, 1)
        screen.blit(small_font.render(f"{OVERLAY_NAMES[overlay_mode]} · 원이 클수록 자원량 많음", True, (45, 55, 95)), (panel_x + 20, y_cursor))
        y_cursor += 18
        desc = "숫자=구역 총량" if overlay_mode in ("food", "water", "wood") else "숫자=매장지 총 매장량"
        screen.blit(small_font.render(desc, True, (85, 85, 90)), (panel_x + 20, y_cursor))
        y_cursor += 22

    # 전쟁이 진행 중일 때만 한 줄 알림을 보여준다.
    current_wars = [w for w in active_wars if not w.get("ended")]
    if current_wars:
        w = current_wars[0]
        a = civilizations[w["a"]] if 0 <= w["a"] < len(civilizations) else None
        b = civilizations[w["b"]] if 0 <= w["b"] < len(civilizations) else None
        if a is not None and b is not None:
            y_cursor = draw_wrapped_text(
                screen, f"⚔ 전쟁 중: {a['name']} ↔ {b['name']}", small_font, (150, 45, 40),
                panel_x, y_cursor, panel_w, 16, max_lines=2
            ) + 4

    # ==================================================
    # 마우스 위치 / 국가 정보 - 남는 공간 전체 사용
    # ==================================================

    mouse_x, mouse_y = pygame.mouse.get_pos()
    info_box_y = y_cursor + 4
    info_box_h = max(150, HEIGHT - info_box_y - 12)
    box_x = MAP_WIDTH + 10
    box_w = INFO_WIDTH - 20

    pygame.draw.rect(screen, (228, 232, 236), (box_x, info_box_y, box_w, info_box_h))
    pygame.draw.rect(screen, (120, 120, 120), (box_x, info_box_y, box_w, info_box_h), 1)

    if 0 <= mouse_x < MAP_WIDTH and 0 <= mouse_y < HEIGHT:
        tile_x = int((camera_x + mouse_x) / tile_size)
        tile_y = int((camera_y + mouse_y) / tile_size)

        if 0 <= tile_x < WORLD_WIDTH and 0 <= tile_y < WORLD_HEIGHT:
            terrain = world[tile_y][tile_x]
            civ = find_civilization_at(tile_x, tile_y)
            screen.blit(font.render("현재 위치", True, (25, 25, 30)), (box_x + 10, info_box_y + 8))

            old_clip = screen.get_clip()
            screen.set_clip(pygame.Rect(box_x + 7, info_box_y + 32, box_w - 14, info_box_h - 38))
            line_y = info_box_y + 36

            location_lines = [
                f"({tile_x}, {tile_y}) · {TERRAIN_NAMES[terrain]}",
                f"식량 {get_resource_value('food', tile_x, tile_y)} · 물 {get_resource_value('water', tile_x, tile_y)}",
                f"철 {get_resource_value('iron', tile_x, tile_y)} · 광물 {get_resource_value('minerals', tile_x, tile_y)} · 석유 {get_resource_value('oil', tile_x, tile_y)}",
                f"기온 {temperature_map[tile_y][tile_x]:.1f}°C · 건조도 {dryness_map[tile_y][tile_x]:.0f}",
            ]
            for line in location_lines:
                line_y = draw_wrapped_text(screen, line, small_font, (35, 35, 35), box_x + 10, line_y, box_w - 20, 16, max_lines=2)

            city_here = None
            if civ is not None:
                city_here = next((city for city in civ.get("cities", []) if city.alive and city.x == tile_x and city.y == tile_y), None)

            if city_here is not None:
                line_y = draw_wrapped_text(
                    screen, f"도시: {'수도' if city_here.capital else city_here.stage_name} · {city_here.specialization}",
                    small_font, (65, 55, 25), box_x + 10, line_y + 2, box_w - 20, 16, max_lines=2
                )

            if civ is not None and line_y < info_box_y + info_box_h - 80:
                line_y += 6
                screen.blit(font.render(civ["name"], True, civ["color"]), (box_x + 10, line_y))
                line_y += 25

                compact_country_lines = [
                    f"인구 {civ['population']:,}명 · 영토 {len(civ.get('territory', ())):,}칸",
                    f"도시 {sum(1 for city in civ.get('cities', []) if city.alive and city.stage >= 1)}개 · 재산 {civ['wealth']:,.0f}",
                    f"의료 {civ['medical']:.1f} · 지능 {civ['intelligence']:.1f}",
                    f"국력 {national_power_score(civ):.1f} · 군사력 {military_power(civ):.1f}",
                    f"상태 {civ.get('status', '안정')} · {civ.get('collapse_state', '안정')}",
                ]
                war = active_war_for_civ(civ)
                if war:
                    opponent = war_opponent(civ, war)
                    if opponent is not None:
                        compact_country_lines.append(f"⚔ {opponent['name']}와 전쟁 중")

                for line in compact_country_lines:
                    if line_y > info_box_y + info_box_h - 20:
                        break
                    line_y = draw_wrapped_text(screen, line, small_font, (30, 30, 30), box_x + 10, line_y, box_w - 20, 16, max_lines=2)

            screen.set_clip(old_clip)
    else:
        screen.blit(font.render("지도에 마우스를 올리세요", True, (85, 85, 85)), (box_x + 12, info_box_y + 12))


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
        column_gap = 35
        left_w = (WIDTH - 45 - 45 - column_gap) // 2
        right_x = left_x + left_w + column_gap
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

    if show_world_history:
        draw_world_history_overlay(screen)

    if show_ranking:
        draw_ranking_overlay(screen)

    if selected_country_id is not None and 0 <= selected_country_id < len(civilizations):
        draw_country_dashboard(screen, civilizations[selected_country_id], country_graph_metric)


    pygame.display.flip()
    clock.tick(60)


pygame.quit()