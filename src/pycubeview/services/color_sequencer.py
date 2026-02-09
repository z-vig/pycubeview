from typing import TypeVar, Generic
from cmap import Colormap, Color

T = TypeVar("T")


class ListSequencer(Generic[T]):
    def __init__(self, list_items: list[T]):
        self.idx = 0
        self.master_list: list[T] = list_items
        self._pulled: list[T] = []

    def next(self) -> T:
        # When the index is at the end of the list, pull from deleted items.
        if self.idx == len(self.master_list):
            deleted_items = [
                i for i in self.master_list if i not in self._pulled
            ]
            if len(deleted_items) == 0:
                return self.master_list[-1]
            self._pulled.append(deleted_items[0])
            return deleted_items[0]

        # Regulatr behavior, pull the next index.
        pull = self.master_list[self.idx]
        self._pulled.append(pull)
        self.idx += 1
        return pull

    def delete(self, item: T) -> None:
        self._pulled.remove(item)

    def reset(self):
        self._pulled = []


class ColorSequencer(ListSequencer[Color]):
    def __init__(self, cmap: Colormap):
        list_items = [cmap(i) for i in range(cmap.num_colors)]
        super().__init__(list_items)
