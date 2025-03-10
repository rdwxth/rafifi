from typing import List, TypeVar, Generic
from heapq import heappush, heappop
from datetime import datetime
from models import Flashcard

T = TypeVar('T')

class PriorityQueue(Generic[T]):
    """Priority queue implementation using a heap"""
    def __init__(self):
        self._heap = []
    
    def push(self, item: T, priority: int):
        """Add item with priority (higher priority = served first)"""
        # Negate priority because heapq is min-heap
        heappush(self._heap, (-priority, item))
    
    def pop(self) -> T:
        """Remove and return highest priority item"""
        if not self._heap:
            raise IndexError("Queue is empty")
        return heappop(self._heap)[1]
    
    def peek(self) -> T:
        """Return highest priority item without removing"""
        if not self._heap:
            raise IndexError("Queue is empty")
        return self._heap[0][1]
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self._heap) == 0
    
    def size(self) -> int:
        """Return number of items in queue"""
        return len(self._heap)

def merge_sort(flashcards: List[Flashcard]) -> List[Flashcard]:
    """Sort flashcards by priority using merge sort"""
    if len(flashcards) <= 1:
        return flashcards
    
    # Divide
    mid = len(flashcards) // 2
    left = merge_sort(flashcards[:mid])
    right = merge_sort(flashcards[mid:])
    
    # Merge
    merged = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        # Compare priorities (higher priority comes first)
        if left[i].priority >= right[j].priority:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    
    # Add remaining elements
    merged.extend(left[i:])
    merged.extend(right[j:])
    
    return merged

def create_test_queue(flashcards: List[Flashcard], min_priority: int = None) -> PriorityQueue[Flashcard]:
    """Create a priority queue of flashcards for testing"""
    queue = PriorityQueue()
    
    # Update priorities based on incorrect attempts and time since last review
    for card in flashcards:
        card.update_priority()
        
        # Only add cards meeting minimum priority requirement
        if min_priority is None or card.priority >= min_priority:
            queue.push(card, card.priority)
    
    return queue

def merge_flashcard_sets(sets: List[List[Flashcard]]) -> List[Flashcard]:
    """Merge multiple flashcard sets into a single sorted list by priority"""
    # First, sort each individual set
    sorted_sets = [merge_sort(set_cards) for set_cards in sets]
    
    # Create a priority queue for merging
    merge_queue = PriorityQueue()
    
    # Initialize with first card from each set
    for i, sorted_set in enumerate(sorted_sets):
        if sorted_set:  # Only add non-empty sets
            merge_queue.push((sorted_set[0], i, 0), sorted_set[0].priority)
    
    merged = []
    
    # Merge sets using priority queue
    while not merge_queue.is_empty():
        card, set_index, card_index = merge_queue.pop()
        merged.append(card)
        
        # Add next card from the same set if available
        if card_index + 1 < len(sorted_sets[set_index]):
            next_card = sorted_sets[set_index][card_index + 1]
            merge_queue.push(
                (next_card, set_index, card_index + 1),
                next_card.priority
            )
    
    return merged
