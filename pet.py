import random
import sqlite3
from datetime import datetime
from pathlib import Path


PET_DB_PATH = Path("pet.db")
PET_TYPES = {"猫": "猫咪", "狗": "小狗", "兔": "兔子", "龙": "小龙"}


class PetService:
    """独立的电子宠物服务，数据保存在 pet.db。"""

    def __init__(self):
        self._init_db()

    def _connect(self):
        return sqlite3.connect(PET_DB_PATH)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pet (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    level INTEGER NOT NULL DEFAULT 1,
                    exp INTEGER NOT NULL DEFAULT 0,
                    coins INTEGER NOT NULL DEFAULT 50,
                    hunger INTEGER NOT NULL DEFAULT 80,
                    happiness INTEGER NOT NULL DEFAULT 80,
                    energy INTEGER NOT NULL DEFAULT 80,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _get(self):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM pet WHERE id = 1").fetchone()
        return dict(row) if row else None

    def has_pet(self):
        return self._get() is not None

    def chat_context(self):
        pet = self._get()
        if not pet:
            return None
        return (
            f"名字：{pet['name']}；种类：{pet['kind']}；等级：{pet['level']}；"
            f"饥饿：{pet['hunger']}/100；心情：{pet['happiness']}/100；"
            f"体力：{pet['energy']}/100；金币：{pet['coins']}"
        )

    def _update(self, **changes):
        changes["updated_at"] = datetime.now().isoformat(timespec="seconds")
        fields = ", ".join(f"{key} = ?" for key in changes)
        values = list(changes.values())
        with self._connect() as conn:
            conn.execute(f"UPDATE pet SET {fields} WHERE id = 1", values)
            conn.commit()

    def handle(self, text: str) -> str:
        command = text.strip()
        args = command[4:].strip() if command.startswith("/pet") else ""
        pet = self._get()

        if pet is None:
            if not args or args.lower() in {"start", "开始"}:
                return "想养什么小宠物？请输入：猫、狗、兔或龙"
            kind = next((PET_TYPES[key] for key in PET_TYPES if key in args), None)
            if kind is None:
                return "请选择：猫、狗、兔或龙。例：/pet 猫"
            name = args.replace(kind, "").strip() or kind
            now = datetime.now().isoformat(timespec="seconds")
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO pet
                        (id, name, kind, created_at, updated_at)
                    VALUES (1, ?, ?, ?, ?)
                    """,
                    (name[:12], kind, now, now),
                )
                conn.commit()
            return f"欢迎你，{name}！你的{kind}出生了，初始金币 50。输入 /pet status 查看状态。"

        if not args or args.lower() in {"status", "状态"}:
            return self._status(pet)
        if args in {"feed", "喂", "喂食"}:
            return self._feed(pet)
        if args in {"play", "玩", "玩耍"}:
            return self._play(pet)
        if args in {"work", "工作", "挣钱", "赚钱"}:
            return self._work(pet)
        if args in {"shop", "商店"}:
            return "宠物商店：/pet buy 小鱼干（10金币，饥饿+15）\n/pet buy 彩球（15金币，心情+15）\n/pet buy 能量罐（20金币，体力+20）"
        if args.startswith("buy ") or args.startswith("购买 "):
            item = args.split(" ", 1)[1].strip()
            return self._buy(pet, item)
        if args.startswith("rename ") or args.startswith("改名 "):
            new_name = args.split(" ", 1)[1].strip()[:12]
            if not new_name:
                return "用法：/pet rename 新名字"
            self._update(name=new_name)
            return f"好呀，以后就叫我{new_name}！"
        if args in {"off", "退出", "关闭"}:
            return "已退出宠物操作，普通文字会继续交给聊天助手。"

    def _status(self, pet):
        return (
            f"{pet['name']}（{pet['kind']}） Lv.{pet['level']}\n"
            f"饥饿：{pet['hunger']}/100，心情：{pet['happiness']}/100，"
            f"体力：{pet['energy']}/100\n"
            f"经验：{pet['exp']}，金币：{pet['coins']}"
        )

    def _feed(self, pet):
        if pet["coins"] < 5:
            return "金币不够买食物了，先让宠物去工作吧。"
        self._update(coins=pet["coins"] - 5, hunger=min(100, pet["hunger"] + 20))
        return f"{pet['name']} 吃得很开心！花费 5 金币，饥饿度提高了。"

    def _play(self, pet):
        if pet["energy"] < 15:
            return f"{pet['name']} 有点累了，先休息或喂饱它吧。"
        gain = random.randint(8, 15)
        self._update(
            happiness=min(100, pet["happiness"] + gain),
            energy=max(0, pet["energy"] - 15),
            hunger=max(0, pet["hunger"] - 5),
            exp=pet["exp"] + 5,
        )
        return f"和{pet['name']}玩了一会儿！心情增加，获得 5 点经验。"

    def _work(self, pet):
        if pet["energy"] < 20:
            return f"{pet['name']} 没体力工作了，先玩或休息一下吧。"
        coins = random.randint(8, 20)
        exp = pet["exp"] + 8
        level = pet["level"]
        if exp >= level * 50:
            level += 1
            result = f"还升到了 Lv.{level}！"
        else:
            result = ""
        self._update(
            coins=pet["coins"] + coins,
            energy=max(0, pet["energy"] - 20),
            hunger=max(0, pet["hunger"] - 10),
            exp=exp,
            level=level,
        )
        return f"{pet['name']} 工作赚到 {coins} 金币，获得 8 点经验！{result}"

    def _buy(self, pet, item):
        items = {
            "小鱼干": (10, {"hunger": min(100, pet["hunger"] + 15)}, "吃得津津有味"),
            "彩球": (15, {"happiness": min(100, pet["happiness"] + 15)}, "玩得特别开心"),
            "能量罐": (20, {"energy": min(100, pet["energy"] + 20)}, "恢复了不少体力"),
        }
        selected = items.get(item)
        if selected is None:
            return "可购买：小鱼干、彩球、能量罐。例：/pet buy 小鱼干"
        price, changes, effect = selected
        if pet["coins"] < price:
            return f"金币不够，需要 {price} 金币；可以输入 /pet work 让宠物工作。"
        changes["coins"] = pet["coins"] - price
        self._update(**changes)
        return f"购买成功！{pet['name']}{effect}，花费 {price} 金币。"
