import sys
import threading

class RefCounter:
    def __init__(self):
        self.references = {}      # Store reference counts keyed by object id
        self.objects = {}         # Store actual objects keyed by object id
        self.memory_pool = []     # Pool of reusable objects
        self.lock = threading.Lock()  # For thread safety
        self.memory_usage = 0     # Track memory usage

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
            print(f"Allocated object with ID {obj_id}: {obj} with ref count {self.references[obj_id]}, size: {obj_size} bytes")

    def increase_ref(self, obj):
        """Increase reference count for an object."""
        obj_id = id(obj)
        with self.lock:
            if obj_id in self.references:
                self.references[obj_id] += 1
                print(f"Increased ref count for object ID {obj_id} to {self.references[obj_id]}")
            else:
                print(f"Object {obj} not allocated.")

    def decrease_ref(self, obj):
        """Decrease reference count for an object; drop if count reaches zero."""
        obj_id = id(obj)
        with self.lock:
            if obj_id in self.references:
                self.references[obj_id] -= 1
                print(f"Decreased ref count for object ID {obj_id} to {self.references[obj_id]}")

                if self.references[obj_id] == 0:
                    self.drop(obj)
            else:
                print(f"Object {obj} not allocated.")

    def drop(self, obj):
        """Drop the object and add it to the memory pool for reuse, if size matches."""
        obj_id = id(obj)
        with self.lock:
            if obj_id in self.references:
                obj_size = sys.getsizeof(obj)
                print(f"Dropping object with ID {obj_id} of size {obj_size} bytes")
                
                # Adjust memory usage
                self.memory_usage -= obj_size
                del self.references[obj_id]
                del self.objects[obj_id]
                self.memory_pool.append((obj_size, obj))

    def reuse(self, desired_type=None, min_size=0):
        """Reuse an object from the memory pool if available and matches criteria."""
        with self.lock:
            for i, (obj_size, obj) in enumerate(self.memory_pool):
                if (desired_type is None or isinstance(obj, desired_type)) and obj_size >= min_size:
                    self.memory_pool.pop(i)
                    obj_id = id(obj)
                    self.allocate(obj)
                    print(f"Reused object: {obj} with ID {obj_id}, size: {obj_size} bytes")
                    return obj
            print("No suitable objects available for reuse.")
            return None

    def get_memory_usage(self):
        """Get the current memory usage."""
        with self.lock:
            print(f"Current memory usage: {self.memory_usage} bytes")
            return self.memory_usage

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

