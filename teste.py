from core.memory_manager import MemoryManager
m = MemoryManager("aria")
m.record_interaction("user", "Olá!")
m.record_interaction("assistant", "Oi, como posso ajudar?")
print(m.get_all())
print(m.get_recent())