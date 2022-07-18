from __future__ import annotations

import os
import shutil
import datetime as dt
from datetime import datetime
from typing import Optional


def _date_to_str(date: datetime) -> str:
    return f"{date.year}-{date.month}-{date.day}"


def _get_today() -> datetime:
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    return today


def _get_today_str() -> str:
    return _date_to_str(_get_today())


class Card:

    _SEP = "-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-"

    @staticmethod
    def _find_date_str(category: str, card_id: str) -> str:
        date_str = None
        date_dirs = os.listdir(category)
        for this_date_str in date_dirs:
            if os.path.isdir(f"{category}/{this_date_str}"):
                card_ids = os.listdir(f"{category}/{this_date_str}")
                if card_id in card_ids:
                    assert date_str is None  # Otherwise there are more than 1 file with this id. (BUG)
                    date_str = this_date_str
        assert date_str is not None  # Otherwise there is no such card.
        return date_str

    @staticmethod
    def _read_card(category: str, card_id: str, date_str: Optional[str] = None) -> tuple[int, str, str]:

        if date_str is None:
            date_str = Card._find_date_str(category, card_id)

        with open(f"{category}/{date_str}/{card_id}", "r") as f:
            lines = f.read().splitlines()

        assert lines[1] == Card._SEP
        second_sep_idx = len(lines) - lines[::-1].index(Card._SEP) - 1
        assert second_sep_idx != 1 and second_sep_idx != 2

        level = int(lines[0])
        front = "\n".join(lines[2: second_sep_idx])
        back = "\n".join(lines[second_sep_idx + 1:])
        return level, front, back

    @staticmethod
    def _write_card(category: str, front: str, back: str, card_id: str, level: int, date_str: Optional[str] = None) -> None:

        if date_str is None:
            date_str = _get_today_str()

        with open(f"{category}/{date_str}/{card_id}", "w") as f:
            f.write(str(level) + "\n")
            f.write(Card._SEP + "\n")
            f.write(front + "\n")
            f.write(Card._SEP + "\n")
            f.write(back + "\n")

    @staticmethod
    def create(category: str, front: str, back: str) -> Card:
        card_id = str(int(Category(category).get_latest_card_id()) + 1)
        level = 0
        date_str = _get_today_str()
        return Card(category, front, back, card_id, level, date_str)

    @staticmethod
    def find(category: str, card_id: str, date_str: Optional[str] = None) -> Card:
        if date_str is None:
            date_str = Card._find_date_str(category, card_id)
        level, front, back = Card._read_card(category, card_id)
        return Card(category, front, back, card_id, level, date_str)

    def __init__(self, category: str, front: str, back: str, card_id: str, level: int, date_str: str):
        assert os.path.exists(category)

        self._category = category
        self._front = front
        self._back = back
        self._card_id = card_id
        self._level = level
        self._date_str = date_str
        # TODO: We can add notes.

    def get_category(self) -> str:
        return self._category

    def get_front(self) -> str:
        return self._front

    def get_back(self) -> str:
        return self._back

    def get_card_id(self) -> str:
        return self._card_id

    def get_level(self) -> int:
        return self._level

    def get_date_str(self) -> str:
        return self._date_str

    def add(self) -> None:
        date_path = f"{self._category}/{self._date_str}"
        if not os.path.exists(date_path):
            os.mkdir(date_path)

        Card._write_card(self._category, self._front, self._back, self._card_id, self._level, self._date_str)
        Category(self._category).update_latest_card_id(self._card_id)

    def remove(self) -> None:
        card_path = f"{self._category}/{self._date_str}/{self._card_id}"
        assert os.path.exists(card_path)
        os.remove(card_path)

        date_path = f"{self._category}/{self._date_str}"
        if len(os.listdir(date_path)) == 0:
            os.rmdir(date_path)

    def update(self, new_front: Optional[str] = None, new_back: Optional[str] = None, new_level: Optional[int] = None, new_date_str: Optional[str] = None) -> None:
        prev_date_str = self._date_str

        if new_front is not None:
            self._front = new_front
        if new_back is not None:
            self._back = new_back
        if new_level is not None:
            self._level = new_level
        if new_date_str is not None:
            self._date_str = new_date_str

        date_path = f"{self._category}/{self._date_str}"
        if not os.path.exists(date_path):
            os.mkdir(date_path)
        Card._write_card(self._category, self._front, self._back, self._card_id, self._level, self._date_str)

        if self._date_str != prev_date_str:
            # We need to remove the existing file
            os.remove(f"{self._category}/{prev_date_str}/{self._card_id}")
            date_dir_path = os.path.dirname(f"{self._category}/{prev_date_str}")
            if len(os.listdir(date_dir_path)) == 0:
                os.rmdir(date_dir_path)


class Category:

    @staticmethod
    def create(category: str) -> Category:
        assert not os.path.exists(category)
        os.mkdir(category)
        with open(f"{category}/id", "w") as f:
            f.write("0")
        return Category(category)

    @staticmethod
    def find(category: str) -> Category:
        return Category(category)

    def __init__(self, category: str):
        assert os.path.exists(category), f"Please create the category first: Category.create('{category}')"
        self._category = category

    def get_num_cards(self) -> int:
        assert os.path.exists(self._category)
        num_cards = 0
        date_dirs = os.listdir(self._category)
        for date_dir in date_dirs:
            if os.path.isdir(date_dir):
                card_files = os.listdir(f"{self._category}/{date_dir}")
                num_cards += len(card_files)
        return num_cards

    def remove(self, prompt: bool = True) -> None:
        assert os.path.exists(self._category)
        num_cards = self.get_num_cards()

        if prompt:
            choice = input(f"The category '{self._category}' with {num_cards} cards will be removed. Proceed? (y/N) ").lower()
            if choice == "y":
                shutil.rmtree(self._category)
                print("The category is removed.")
            else:
                print("The program is terminating.")
                exit(1)
        else:
            shutil.rmtree(self._category)

    def get_latest_card_id(self) -> str:
        with open(f"{self._category}/id", "r") as f:
            return f.read()

    def update_latest_card_id(self, new_card_id: str) -> None:
        latest_card_id = self.get_latest_card_id()
        assert new_card_id == str(int(latest_card_id) + 1)
        with open(f"{self._category}/id", "w") as f:
            f.write(str(new_card_id))

    def get_all_cards(self, date_strs: Optional[list[str]] = None) -> list[Card]:
        assert os.path.exists(self._category)
        if date_strs is None:
            date_strs = os.listdir(self._category)

        cards = []
        for date_str in date_strs:
            if os.path.isdir(f"{self._category}/{date_str}"):
                card_ids = os.listdir(f"{self._category}/{date_str}")
                for card_id in card_ids:
                    card = Card.find(self._category, card_id, date_str)
                    cards.append(card)
        return cards


class SpacedRepetition:

    """
    Simple scheduler:

             Number of days
    Level 0: 0
    Level 1: 1
    Level 2: 2
    Level 3: 4
    Level 4: 8
    Level 5: 16
    Level 6: 32
    Level 7: 64
    Level 8: 128
    Level 9: 256
    ...

    True --> Next level
    False --> Prev level (Level 0 is the first possible level.)
    """

    def __init__(self, multiplier: int = 2):
        self.multiplier = multiplier

    def _schedule(self, current_level: int, is_success: bool) -> tuple[int, datetime]:
        if is_success:
            new_level = current_level + 1
        else:
            new_level = max(0, current_level - 1)

        if new_level == 0:
            num_days = 0
        else:
            num_days = self.multiplier ** (new_level - 1)

        today = _get_today()
        new_date = today + dt.timedelta(days=num_days)
        return new_level, new_date

    def review_card(self, card: Card, is_success: bool):
        new_level, new_date = self._schedule(card.get_level(), is_success)
        card.update(new_level=new_level, new_date_str=_date_to_str(new_date))

    @staticmethod
    def get_cards_to_review(category: str) -> list[Card]:
        date_strs = os.listdir(category)
        dates = [datetime(*map(int, date_str.split("-"))) for date_str in date_strs if date_str != "id"]
        today = _get_today()
        dates.sort()
        old_dates = [date for date in dates if date <= today]
        old_date_strs = [_date_to_str(old_date) for old_date in old_dates]
        return Category(category).get_all_cards(date_strs=old_date_strs)
