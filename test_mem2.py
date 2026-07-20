try:
    import _lightengine
    print('OS heap free:', _lightengine.get_free_heap())
except Exception as e:
    print(e)
