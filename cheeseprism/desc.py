class updict(dict):
    """
    A descriptor that updates it's internal represention on set, and
    returns the dictionary to original state on deletion.
    """
    
    def __init__(self, *args, **kw):
        super(updict, self).__init__(*args, **kw)
        self.default = self.copy()

    def __get__(self, obj, objtype):
        return self

    def __set__(self, val):
        self.update(val)

    def __delete__(self, obj):
        self.clear()
        self.update(self.default)
