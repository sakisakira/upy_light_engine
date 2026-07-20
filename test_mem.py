import gc
import micropython
print('GC free:', gc.mem_free(), 'allocated:', gc.mem_alloc())
micropython.mem_info()
try:
    import lightengine
    print('OS heap free:', lightengine.get_free_heap())
except:
    pass
