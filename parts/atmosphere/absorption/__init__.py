"""
Absorption
==========

"""
from parts.atmosphere.atmospheric_quantity \
    import AtmosphericQuantity, extend_dimensions

from parts.arts_object import ArtsObject, arts_property
from parts.jacobian    import JacobianBase
from parts.retrieval   import RetrievalBase, RetrievalQuantity

import numpy as np
from typhon.arts.workspace import arts_agenda

class Jacobian(JacobianBase, ArtsObject):

    @arts_property("Numeric")
    def perturbation(self):
        return 0.01

    def __init__(self, quantity, index):

        JacobianBase.__init__(self, quantity, index)
        ArtsObject.__init__(self)

        self.p_grid   = None
        self.lat_grid = None
        self.lon_grid = None

        self.unit = "vmr"
        self.method = "analytical"
        self.for_species_tag = 1
        self.dx = 0.001

    def _make_setup_kwargs(self, ws):

        if self.p_grid is None:
            g1 = ws.p_grid
        else:
            g1 = self.p_grid

        if self.lat_grid is None:
            g2 = ws.lat_grid
        else:
            g2 = self.lat_grid

        if self.lon_grid is None:
            g3 = ws.lon_grid
        else:
            g3 = self.lon_grid

        kwargs = {"g1" : g1, "g2" : g2, "g3" : g3,
                    "species" : self.quantity.get_tag_string(),
                    "method" : self.method,
                    "unit" : self.unit,
                    "for_species_tag" : self.for_species_tag,
                    "dx" : self.dx}

        return kwargs

    def setup(self, ws):
        kwargs = self._make_setup_kwargs(ws)
        print(kwargs)
        ws.jacobianAddAbsSpecies(**kwargs)

class Retrieval(RetrievalBase, Jacobian):

    def __init__(self, quantity, index):
        super().__init__(quantity, index)

    def add(self, ws):
        ws.retrievalAddAbsSpecies(**self._make_setup_kwargs(ws))


class AbsorptionSpecies(AtmosphericQuantity, RetrievalQuantity):

    def __init__(self,
                 name,
                 catalog = None,
                 cia = None,
                 frequency_range = None,
                 isotopologues = None,
                 model = None,
                 on_the_fly = True,
                 zeeman = False):

        AtmosphericQuantity.__init__(self,
                                     name,
                                     (0, 0, 0))
        RetrievalQuantity.__init__(self)

        self._dimensions = (0, 0, 0)

        self._catalog         = catalog
        self._cia             = cia
        self._frequency_range = frequency_range
        self._isotopologues   = isotopologues
        self._jacobian        = None
        self._model           = model
        self._on_the_fly      = on_the_fly
        self._retrieval       = None
        self._zeeman          = zeeman

    #
    # Abstract properties
    #

    def dimensions(self):
        return self._dimensions

    #
    # Properties
    #

    @property
    def catalog(self):
        return self._catalog

    @property
    def cia(self):
        return self._cia

    @property
    def isotopologues(self):
        return self._isotopologues

    @property
    def model(self):
        return self._model

    @property
    def frequency_range(self):
        return self._frequency_range

    @property
    def on_the_fly(self):
        return self._on_the_fly

    @property
    def zeeman(self):
        return self._zeeman

    def get_tag_string(self):

        ts = self._name
        ts += "-"

        if self._zeeman:
            ts += "Z"
            ts += "-"

        if not self._isotopologues is None:
            ts += self._isotopologues
            ts += "-"

        if self._model:
            ts += self._model
            ts += "-"

        if self._frequency_range:
           ts += str(self._frequency_range[0])
           ts += "-"
           ts += str(self._frequency_range[1])

        return ts

    #
    # Jacobian & retrieval
    #

    @property
    def jacobian_class(self):
        return Jacobian

    @property
    def retrieval_class(self):
        return Retrieval

    def set_from_x(self, ws, x):
        x = self.transformation.invert(x)
        x = np.copy(x.reshape(ws.vmr_field.value.shape[1:]))
        ws.vmr_field.value[self._wsv_index, :, :, :] = x

    #
    # Retrieval
    #

    @property
    def retrieved(self):
        return not self._retrieval is None

    #
    # Abstract methods
    #

    def setup(self, ws, i):
        self._wsv_index = i

    def get_data(self, ws, provider, *args, **kwargs):

        if not self.retrieved:

            dimensions = ws.t_field.shape
            f = provider.__getattribute__("get_" + self.name)
            x = f(*args, **kwargs)
            x = extend_dimensions(x)

            if not x.shape == dimensions:
                raise Exception("Shape of {0} field is inconsistent with "
                                "the dimensions of the atmosphere."
                                .format(self.name))

            ws.vmr_field.value[self._wsv_index, :, :, :] = x

class H2O(AbsorptionSpecies):
    def __init__(self,
                 catalog = None,
                 cia = None,
                 frequency_range = None,
                 isotopologues = None,
                 model = None,
                 on_the_fly = True,
                 zeeman = False):
        super().__init__("H2O",
                         catalog = catalog,
                         cia = cia,
                         frequency_range = frequency_range,
                         isotopologues = isotopologues,
                         model = "PWR98",
                         on_the_fly = on_the_fly,
                         zeeman = zeeman)

class N2(AbsorptionSpecies):
    def __init__(self,
                 catalog = None,
                 cia = None,
                 frequency_range = None,
                 isotopologues = None,
                 model = "SelfContStandardType",
                 on_the_fly = True,
                 zeeman = False):
        super().__init__("N2",
                         catalog = catalog,
                         cia = cia,
                         frequency_range = frequency_range,
                         isotopologues = isotopologues,
                         model = model,
                         on_the_fly = on_the_fly,
                         zeeman = zeeman)

class O2(AbsorptionSpecies):
    def __init__(self,
                 catalog = None,
                 cia = None,
                 frequency_range = None,
                 isotopologues = None,
                 model = "PWR93",
                 on_the_fly = True,
                 zeeman = False):
        super().__init__("O2",
                         catalog = catalog,
                         cia = cia,
                         frequency_range = frequency_range,
                         isotopologues = isotopologues,
                         model = model,
                         on_the_fly = on_the_fly,
                         zeeman = zeeman)
