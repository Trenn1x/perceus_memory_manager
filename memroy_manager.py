import sys
import threading
from collections import defaultdict

class RefCounter:
    def __init__(self):
        self.references = {}          # Store reference counts keyed by object id
        self.objects = {}             # Store actual objects keyed by object id
        self.memory_pool = defaultdict(list)  # Smart pool for reusable objects categorized by type and size
        self.lock = threading.Lock()  # For thread safety
        self.memory_usage = 0         # Track memory usage

    def allocate(self, obj):
        """Allocate memory for an object and initialize reference count."""
        obj_id = id(obj)
        with self.lock:
            # Track memory usage
            obj_size = sys.getsizeof(obj)
            self.memory_usage += obj_size

            # Store reference and object
            self.references[obj_id] = 1
            self.objects[obj_id] = obj
            self._log(f"Allocated object with ID {obj_id}: {obj} with ref count {self.references[obj_id]}, size: {obj_size} bytes")

    def increase_ref(self, obj):
        """Increase reference count for an object."""
        obj_id = id(obj)
        with self.lock:
            if obj_id in self.references:
                self.references[obj_id] += 1
                self._log(f"Increased ref count for object ID {obj_id} to {self.references[obj_id]}")
            else:
                self._log(f"Object {obj} not allocated.")

    def decrease_ref(self, obj):
        """Decrease reference count for an object; drop if count reaches zero."""
        obj_id = id(obj)
        with self.lock:
            if obj_id in self.references:
                self.references[obj_id] -= 1
                self._log(f"Decreased ref count for object ID {obj_id} to {self.references[obj_id]}")

                if self.references[obj_id] == 0:
                    self.drop(obj)
            else:
                self._log(f"Object {obj} not allocated.")

    def drop(self, obj):
        """Drop the object and add it to the memory pool for reuse, categorized by type and size."""
        obj_id = id(obj)
        with self.lock:
            if obj_id in self.references:
                obj_size = sys.getsizeof(obj)
                obj_type = type(obj).__name__
                self._log(f"Dropping object with ID {obj_id} of size {obj_size} bytes, type {obj_type}")
                
                # Adjust memory usage
                self.memory_usage -= obj_size
                del self.references[obj_id]
                del self.objects[obj_id]
                
                # Add to memory pool categorized by type and size range
                size_category = (obj_type, self._size_category(obj_size))
                self.memory_pool[size_category].append(obj)
                
    def reuse(self, desired_type=None, min_size=0):
        """Reuse an object from the memory pool if available and matches criteria."""
        with self.lock:
            size_category = self._size_category(min_size)
            type_name = desired_type.__name__ if desired_type else None

            for (obj_type, category_size), pool in self.memory_pool.items():
                if (desired_type is None or obj_type == type_name) and category_size >= size_category:
                    if pool:
                        reused_obj = pool.pop()
                        self.allocate(reused_obj)
                        obj_id = id(reused_obj)
                        self._log(f"Reused object with ID {obj_id}, size: {sys.getsizeof(reused_obj)} bytes, type {obj_type}")
                        return reused_obj

            self._log("No suitable objects available for reuse.")
            return None

    def get_memory_usage(self):
        """Get the current memory usage."""
        with self.lock:
            self._log(f"Current memory usage: {self.memory_usage} bytes")
            return self.memory_usage

    def _size_category(self, size):
        """Categorize size into ranges (e.g., small, medium, large) for efficient pooling."""
        if size < 100:
            return "small"
        elif size < 1000:
            return "medium"
        else:
            return "large"

    def _log(self, message):
        """Log details of memory management actions."""
        print(f"[LOG]: {message}")

# Usage Example
if __name__ == "__main__":
    manager = RefCounter()

    # Allocate an object
    obj1 = {"data": "example"}
    manager.allocate(obj1)

    # Increase reference
    manager.increase_ref(obj1)

    # Decrease reference
    manager.decrease_ref(obj1)
    manager.decrease_ref(obj1)  # This should drop the object and add it to the memory pool

    # Check memory usage
    manager.get_memory_usage()

    # Attempt to reuse an object from the memory pool
    reused_obj = manager.reuse(desired_type=dict, min_size=50)  # Specify type and size requirements
    manager.get_memory_usage()

