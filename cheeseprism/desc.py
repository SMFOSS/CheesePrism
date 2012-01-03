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

    def __set__(self, obj, val):
        self.update(val)

    def __delete__(self, obj):
        self.clear()
        self.update(self.default)


class template(object):
    """
    A little descriptor for returning templates from jinja env.
    """
    env_method = 'template_env'
    def __init__(self, name):
        self.name = name

    def get_env(self, obj):
        return getattr(obj, self.env_method, None)

    def __get__(self, obj, objtype):
        env = self.get_env(obj)
        return env.get_template(self.name)
