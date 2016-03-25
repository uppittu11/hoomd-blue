## \package hpmc.data
# \brief HPMC data structures

from . import _hpmc
from hoomd_script import globals
import hoomd_plugins.hpmc
import numpy

## Manages shape parameters
#
# The parameters for all hpmc integrator shapes are specified using this class. Parameters are
# specified per particle type. Every HPMC integrator has a member shape_param that is of type _param and is used
# to set the parameters of the shapes.
class param_dict(dict):
    def __init__(self, mc):
        dict.__init__(self);
        self.mc = mc;

    def __getitem__(self, key):
        ntypes = globals.system_definition.getParticleData().getNTypes();
        type_names = [ globals.system_definition.getParticleData().getNameByType(i) for i in range(0,ntypes) ];
        if not key in type_names:
            raise RuntimeError("{} is not a known particle type".format(key));
        elif not key in self.keys():
            self.mc.initialize_shape_params(); # add any extra parameters in that exist at this time.
            if not key in self.keys():
                raise RuntimeError("could not create proxy for type {}".format(key));
        return super(param_dict, self).__getitem__(key);

    ## Sets parameters for particle type(s)
    # \param type Particle type (string) or list of types
    # \param params Named parameters (see below for examples)
    # \returns nothing
    #
    # Calling set() results in one or more parameters being set for a shape. Types are identified
    # by name, and parameters are also added by name. Which parameters you need to specify depends on the hpmc
    # integrator you are setting these coefficients for, see the corresponding documentation.
    #
    # All possible particle types types defined in the simulation box must be specified before executing run().
    # You will receive an error if you fail to do so. It is an error to specify coefficients for
    # particle types that do not exist in the simulation.
    #
    # To set the same parameters for many particle types, provide a list of type names instead of a single
    # one. All types in the list will be set to the same parameters. A convenient wildcard that lists all types
    # of particles in the simulation can be gotten from a saved `sysdef` from the init command.
    #
    # \b Quick Examples:
    # \code
    # mc.shape_param.set('A', diameter=1.0)
    # mc.shape_param.set('B', diameter=2.0)
    # mc.shape_param.set(['A', 'B'], diameter=2.0)
    # \endcode
    #
    # \note Single parameters can not be updated. If both *diameter* and *length* are requred for a particle type,
    # then executing coeff.set('A', diameter=1.5) will fail one must call coeff.set('A', diameter=1.5, length=2.0)
    #
    def set(self, types, **params):
        # util.print_status_line();

        # listify the input
        if isinstance(types, str):
            types = [types];

        for typei in types:
            self.__getitem__(typei).set(**params);


class _param(object):
    def __init__(self, mc, typid):
        self.__dict__.update(dict(_keys=['ignore_statistics', 'ignore_overlaps'], mc=mc, typid=typid, make_fn=None, is_set=False));

    def ensure_list(self, li):
        if(type(li) == numpy.ndarray):
            return li.tolist();
        else:
            return list(li);

    def get_metadata(self):
        data = {}
        for key in self._keys:
            data[key] = getattr(self, key);
        return data;

    def __setattr__(self, name, value):
        if not hasattr(self, name):
            raise AttributeError('{} instance has no attribute {!r}'.format(type(self).__name__, name));
        super(_param, self).__setattr__(name, value);

    def set(self, **params):
        self.is_set = True;
        self.mc.cpp_integrator.setParam(self.typid, self.make_param(**params));

class sphere_params(_hpmc.sphere_param_proxy, _param):
    def __init__(self, mc, index):
        _hpmc.sphere_param_proxy.__init__(self, mc.cpp_integrator, index);
        _param.__init__(self, mc, index);
        self._keys += ['diameter'];
        self.make_fn = _hpmc.make_sph_params;

    def __str__(self):
        # should we put this in the c++ side?
        return "sphere(r = {})".format(self.diameter)

    def make_param(self, diameter, ignore_overlaps=False, ignore_statistics=False):
        return self.make_fn(float(diameter)/2.0,
                            ignore_statistics,
                            ignore_overlaps);

class convex_polygon_params(_hpmc.convex_polygon_param_proxy, _param):
    def __init__(self, mc, index):
        _hpmc.convex_polygon_param_proxy.__init__(self, mc.cpp_integrator, index);
        _param.__init__(self, mc, index);
        self._keys += ['vertices'];
        self.make_fn = _hpmc.make_poly2d_verts;

    def __str__(self):
        # should we put this in the c++ side?
        string = "convex polygon(vertices = {})".format(self.vertices);
        return string;

    def make_param(self, vertices, ignore_overlaps=False, ignore_statistics=False):
        return self.make_fn(self.ensure_list(vertices),
                            float(0.0),
                            ignore_statistics,
                            ignore_overlaps);

class convex_spheropolygon_params(_hpmc.convex_spheropolygon_param_proxy, _param):
    def __init__(self, mc, index):
        _hpmc.convex_spheropolygon_param_proxy.__init__(self, mc.cpp_integrator, index);
        _param.__init__(self, mc, index);
        self._keys += ['vertices', 'sweep_radius'];
        self.make_fn = _hpmc.make_poly2d_verts;

    def __str__(self):
        # should we put this in the c++ side?
        string = "convex spheropolygon(sweep radius = {}, , vertices = {})".format(self.sweep_radius, self.vertices);
        return string;

    def make_param(self, vertices, sweep_radius = 0.0, ignore_overlaps=False, ignore_statistics=False):
        return self.make_fn(self.ensure_list(vertices),
                            float(sweep_radius),
                            ignore_statistics,
                            ignore_overlaps);

class simple_polygon_params(_hpmc.simple_polygon_param_proxy, _param):
    def __init__(self, mc, index):
        _hpmc.simple_polygon_param_proxy.__init__(self, mc.cpp_integrator, index);
        _param.__init__(self, mc, index);
        self._keys += ['vertices'];
        self.make_fn = _hpmc.make_poly2d_verts;

    def __str__(self):
        # should we put this in the c++ side?
        string = "simple polygon(vertices = {})".format(self.vertices);
        return string;

    def make_param(self, vertices, ignore_overlaps=False, ignore_statistics=False):
        return self.make_fn(self.ensure_list(vertices),
                            float(0),
                            ignore_statistics,
                            ignore_overlaps);

class convex_polyhedron_params(_param):
    def __init__(self, mc, index):
        self.cpp_class.__init__(self, mc.cpp_integrator, index); # we will add this base class later becuase of the size template.
        _param.__init__(self, mc, index);
        self._keys += ['vertices'];
        self.make_fn = hoomd_plugins.hpmc.integrate._get_sized_entry("make_poly3d_verts", self.mc.max_verts);

    def __str__(self):
        # should we put this in the c++ side?
        string = "convex polyhedron(vertices = {})".format(self.vertices);
        return string;

    @classmethod
    def get_sized_class(cls, max_verts):
        sized_class = hoomd_plugins.hpmc.integrate._get_sized_entry("convex_polyhedron_param_proxy", max_verts);
        return type(cls.__name__ + str(max_verts), (cls, sized_class), dict(cpp_class=sized_class)); # cpp_class is jusr for easeir refernce to call the constructor

    def make_param(self, vertices, ignore_overlaps=False, ignore_statistics=False):
        if self.mc.max_verts < len(vertices):
            raise RuntimeError("max_verts param expects up to %d vertices, but %d are provided"%(self.mc.max_verts,len(vertices)));
        return self.make_fn(self.ensure_list(vertices),
                            float(0),
                            ignore_statistics,
                            ignore_overlaps);

class convex_spheropolyhedron_params(_param):
    def __init__(self, mc, index):
        self.cpp_class.__init__(self, mc.cpp_integrator, index); # we will add this base class later becuase of the size template.
        _param.__init__(self, mc, index);
        self._keys += ['vertices', 'sweep_radius'];
        self.make_fn = hoomd_plugins.hpmc.integrate._get_sized_entry("make_poly3d_verts", self.mc.max_verts);

    def __str__(self):
        # should we put this in the c++ side?
        string = "convex spheropolyhedron(sweep radius = {}, vertices = {})".format(self.sweep_radius, self.vertices);
        return string;

    @classmethod
    def get_sized_class(cls, max_verts):
        sized_class = hoomd_plugins.hpmc.integrate._get_sized_entry("convex_spheropolyhedron_param_proxy", max_verts);
        return type(cls.__name__ + str(max_verts), (cls, sized_class), dict(cpp_class=sized_class)); # cpp_class is jusr for easeir refernce to call the constructor

    def make_param(self, vertices, sweep_radius = 0.0, ignore_overlaps=False, ignore_statistics=False):
        if self.mc.max_verts < len(vertices):
            raise RuntimeError("max_verts param expects up to %d vertices, but %d are provided"%(self.mc.max_verts,len(vertices)));

        return self.make_fn(self.ensure_list(vertices),
                            float(sweep_radius),
                            ignore_statistics,
                            ignore_overlaps);

class polyhedron_params(_hpmc.polyhedron_param_proxy, _param):
    def __init__(self, mc, index):
        _hpmc.polyhedron_param_proxy.__init__(self, mc.cpp_integrator, index);
        _param.__init__(self, mc, index);
        self._keys += ['vertices', 'faces', 'edges'];
        self.make_fn = _hpmc.make_poly3d_data;

    def __str__(self):
        # should we put this in the c++ side?
        string = "polyhedron(vertices = {}, faces = {}, edges = {})".format(self.vertices, self.faces, self.edges);
        return string;

    def make_param(self, vertices, faces, ignore_overlaps=False, ignore_statistics=False):
        return self.make_fn(self.ensure_list(vertices),
                            self.ensure_list(faces),
                            ignore_statistics,
                            ignore_overlaps);

class faceted_sphere_params(_hpmc.faceted_sphere_param_proxy, _param):
    def __init__(self, mc, index):
        _hpmc.faceted_sphere_param_proxy.__init__(self, mc.cpp_integrator, index);
        _param.__init__(self, mc, index);
        self._keys += ['vertices', 'normals', 'offsets', 'diameter', 'origin'];
        self.make_fn = _hpmc.make_faceted_sphere;

    def __str__(self):
        # should we put this in the c++ side?
        string = "faceted sphere(vertices = {}, normals = {}, offsets = {})".format(self.vertices, self.normals, self.offsets);
        return string;

    def make_param(self, normals, offsets, vertices, diameter, origin=(0.0, 0.0, 0.0), ignore_overlaps=False, ignore_statistics=False):
        return self.make_fn(self.ensure_list(normals),
                            self.ensure_list(offsets),
                            self.ensure_list(vertices),
                            float(diameter),
                            tuple(origin),
                            bool(ignore_statistics),
                            bool(ignore_overlaps));

class sphinx_params(_hpmc.sphinx3d_param_proxy, _param):
    def __init__(self, mc, index):
        _hpmc.sphinx3d_param_proxy.__init__(self, mc.cpp_integrator, index);
        _param.__init__(self, mc, index);
        self.__dict__.update(dict(colors=None));
        self._keys += ['diameters', 'centers', 'diameter', 'colors'];
        self.make_fn = _hpmc.make_sphinx3d_params;

    def __str__(self):
        # should we put this in the c++ side?
        string = "sphinx(centers = {}, diameters = {}, diameter = {})".format(self.centers, self.diameters, self.diameter);
        return string;

    def make_param(self, diameters, centers, ignore_overlaps=False, ignore_statistics=False, colors=None):
        self.colors = None if colors is None else self.ensure_list(colors);
        return self.make_fn(self.ensure_list(diameters),
                            self.ensure_list(centers),
                            ignore_statistics,
                            ignore_overlaps);

class ellipsoid_params(_hpmc.ell_param_proxy, _param):
    def __init__(self, mc, index):
        _hpmc.ell_param_proxy.__init__(self, mc.cpp_integrator, index);
        _param.__init__(self, mc, index);
        self._keys += ['a', 'b', 'c'];
        self.make_fn = _hpmc.make_ell_params;

    def __str__(self):
        # should we put this in the c++ side?
        return "ellipsoid(a = {}, b = {}, c = {})".format(self.a, self.b, self.c)

    def make_param(self, a, b, c, ignore_overlaps=False, ignore_statistics=False):
        return self.make_fn(float(a),
                            float(b),
                            float(c),
                            ignore_statistics,
                            ignore_overlaps);

class sphere_union_params(_hpmc.sphere_union_param_proxy, _param):
    def __init__(self, mc, index):
        _hpmc.sphere_union_param_proxy.__init__(self, mc.cpp_integrator, index);
        _param.__init__(self, mc, index);
        self.__dict__.update(dict(colors=None));
        self._keys += ['diameters', 'centers', 'orientations', 'diameter', 'colors'];
        self.make_fn = _hpmc.make_sphere_union_params;

    def __str__(self):
        # should we put this in the c++ side?
        string = "sphere union(centers = {}, orientations = {}, diameter = {})\n".format(self.centers, self.orientations, self.diameter);
        ct = 0;
        members = self.members;
        for m in members:
            end = "\n" if ct < (len(members)-1) else "";
            string+="sphere-{}(r = {}){}".format(ct, m.radius, end)
            ct+=1
        return string;

    def get_metadata(self):
        data = {}
        for key in self._keys:
            if key == 'diameters':
                val = [ 2.0*m.radius for m in self.members ];
            else:
                val = getattr(self, key);
            data[key] = val;
        return data;

    def make_param(self, diameters, centers, ignore_overlaps=False, ignore_statistics=False, colors=None):
        members = [_hpmc.make_sph_params(float(d)/2.0, False, False) for d in diameters];
        N = len(diameters)
        if len(centers) != N:
            raise RuntimeError("Lists of constituent particle parameters and centers must be equal length.")
        self.colors = None if colors is None else self.ensure_list(colors);
        return self.make_fn(self.ensure_list(members),
                            self.ensure_list(centers),
                            self.ensure_list([[1,0,0,0] for i in range(N)]),
                            ignore_statistics,
                            ignore_overlaps);
