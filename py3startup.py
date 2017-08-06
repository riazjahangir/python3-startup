def reload(path='/Users/riaz', scope=None, updateinstances=True):
    """Reloads modules and classes in use during an interactive session

    :param str path: Only modules at or below this path will be reloaded
    :param scope: Bindings of names to modules and classes.
                  Use scope=None during an interactive session to default to the caller's locals.
    :type scope: dict or None
    :param bool updateinstances: If True, update instances of reloaded classes to reflect the new class definitions
    """
    import importlib
    import inspect
    import sys
    from types import ModuleType

    # If scope not given, take caller's locals. This is usually what we want to do if the function
    # is called from an interactive session.
    if scope is None:
        scope = inspect.stack()[1][0].f_locals

    class ClassInfo:
        def __init__(self, classobj):
            self.classobj = classobj
            self.modulename = classobj.__module__
            self.instances = []

        def __hash__(self):
            return hash(self.classobj)

        def __eq__(self, other):
            return type(other) == ClassInfo and self.classobj == other.classobj

    # Get module aliases from my workspace
    mymodules = set([m for m in scope if isinstance(scope[m], ModuleType) and
                 hasattr(scope[m], '__file__') and scope[m].__file__.startswith(path)])
    # Get aliases for my loaded classes as a dict of alias to ClassInfo
    myclasses = {c: ClassInfo(scope[c]) for c in scope if type(scope[c]) == type and
                    hasattr(scope[c], '__module__') and
                    hasattr(sys.modules[scope[c].__module__], '__file__') and
                    sys.modules[scope[c].__module__].__file__.startswith(path)}
    # Get distinct classes by qualified name
    classinfos = {'{0}.{1}'.format(ci.modulename, ci.classobj.__name__): ci for ci in myclasses.values()}

    # Get instances of my workspace classes
    def findinstances(iterable, visited=set()):
        for var in iterable:
            if id(var) in visited:
                continue
            visited.add(id(var))
            varclassname = '{0}.{1}'.format(var.__class__.__module__, var.__class__.__name__)
            if varclassname in classinfos:
                classinfos[varclassname].instances.append(var)
            if hasattr(var, '__iter__'):
                findinstances(var, visited)
    findinstances(scope.values())

    # Reload modules
    def reloadmodule(module, text=None):
        importlib.reload(module)
        print('Reloaded', module.__name__, text)
    importlib.invalidate_caches()
    for m in mymodules:
        reloadmodule(scope[m], 'as {0}'.format(m))
    for cimodulename in set([ci.modulename for ci in classinfos.values()]):
        reloadmodule(sys.modules[cimodulename], 'classes')
    # Reload classes
    for c in myclasses:
        myclasses[c].classobj = getattr(sys.modules[myclasses[c].modulename], myclasses[c].classobj.__name__)
        scope[c] = myclasses[c].classobj
    # Update instances of my classes to the reloaded definition
    if updateinstances:
        count = 0
        for ci in classinfos.values():
            for obj in ci.instances:
                count += 1
                obj.__class__ = ci.classobj
        print('Updated class definitions for', count, 'objects')
