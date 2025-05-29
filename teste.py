from core.memory_manager import MemoryManager
m = MemoryManager("aria")
for i in range(1, 300):
    m.record_interaction("user", f"msg {i}")
    m.record_interaction("assistant", f"resp {i}")
print(m.get_all())
print(m.get_recent())