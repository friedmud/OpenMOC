import numpy as np
import opencg
import openmc
import openmc.mgxs
import openmc.opencg_compatible

###############################################################################
#                      Simulation Input File Parameters
###############################################################################

# OpenMC simulation parameters
batches = 100
inactive = 10
particles = 10000


###############################################################################
#                 Exporting to OpenMC materials.xml File
###############################################################################

# Instantiate some Nuclides
h1 = openmc.Nuclide('H-1')
b10 = openmc.Nuclide('B-10')
b11 = openmc.Nuclide('B-11')
o16 = openmc.Nuclide('O-16')
u235 = openmc.Nuclide('U-235')
u238 = openmc.Nuclide('U-238')
zr90 = openmc.Nuclide('Zr-90')
zr91 = openmc.Nuclide('Zr-91')
zr92 = openmc.Nuclide('Zr-92')
zr94 = openmc.Nuclide('Zr-94')
zr96 = openmc.Nuclide('Zr-96')

# Instantiate some Materials and register the appropriate Nuclides
fuel = openmc.Material(name='3.1 w/o enriched UO2')
fuel.set_density('sum')
fuel.add_nuclide(u235, 7.18132E-4,)
fuel.add_nuclide(u238, 2.21546E-2)
fuel.add_nuclide(o16, 4.57642E-2)

clad = openmc.Material(name='Cladding')
clad.set_density('sum')
clad.add_nuclide(zr90, 2.18865E-2)
clad.add_nuclide(zr91, 4.77292E-3)
clad.add_nuclide(zr92, 7.29551E-3)
clad.add_nuclide(zr94, 7.39335E-3)
clad.add_nuclide(zr96, 1.19110E-3)

water = openmc.Material(name='Borated Water')
water.set_density('sum')
water.add_nuclide(h1, 4.41459E-2)
water.add_nuclide(o16, 2.20729E-2)
water.add_nuclide(b10, 9.52537E-6)
water.add_nuclide(b11, 3.83408E-5)
water.add_s_alpha_beta(name='HH2O', xs='71t')

# Instantiate a MaterialsFile, add Materials
materials_file = openmc.MaterialsFile()
materials_file.add_materials([fuel, clad, water])
materials_file.make_isotropic_in_lab()
materials_file.default_xs = '71c'

# Export to "materials.xml"
materials_file.export_to_xml()

# Get OpenCG versions of each OpenMC material to fill OpenCG Cells below
opencg_fuel = openmc.opencg_compatible.get_opencg_material(fuel)
opencg_clad = openmc.opencg_compatible.get_opencg_material(clad)
opencg_water = openmc.opencg_compatible.get_opencg_material(water)


###############################################################################
#                 Exporting to OpenMC geometry.xml File
###############################################################################

# Create bounding surfaces
min_x = opencg.XPlane(boundary='reflective', x0=0.0)
max_x = opencg.XPlane(boundary='reflective', x0=5.0)
min_y = opencg.YPlane(boundary='reflective', y0=0.0)
max_y = opencg.YPlane(boundary='reflective', y0=10.0)
min_z = opencg.ZPlane(boundary='reflective', z0=0.0)
max_z = opencg.ZPlane(boundary='reflective', z0=10.0)

# Create material interfacial surfaces
left = opencg.XPlane(surface_id=1, boundary='interface', x0=2.0)
right = opencg.XPlane(surface_id=2, boundary='interface', x0=2.4)

# Create a Universe to encapsulate the 1D slab
slab_universe = opencg.Universe(name='1D slab')

# Create fuel Cell
fuel_cell = opencg.Cell(name='fuel')
fuel_cell.fill = opencg_fuel
fuel_cell.add_surface(halfspace=+1, surface=min_x)
fuel_cell.add_surface(halfspace=-1, surface=left)
slab_universe.add_cell(fuel_cell)

# Create clad Cell
clad_cell = opencg.Cell(name='clad')
clad_cell.fill = opencg_clad
clad_cell.add_surface(halfspace=+1, surface=left)
clad_cell.add_surface(halfspace=-1, surface=right)
slab_universe.add_cell(clad_cell)

# Create water Cell
water_cell = opencg.Cell(name='water')
water_cell.fill = opencg_water
water_cell.add_surface(halfspace=+1, surface=right)
water_cell.add_surface(halfspace=-1, surface=max_x)
slab_universe.add_cell(water_cell)

# Create root Cell
root_cell = opencg.Cell(name='root cell')
root_cell.fill = slab_universe

# Add boundary planes
root_cell.add_surface(halfspace=+1, surface=min_x)
root_cell.add_surface(halfspace=-1, surface=max_x)
root_cell.add_surface(halfspace=+1, surface=min_y)
root_cell.add_surface(halfspace=-1, surface=max_y)
root_cell.add_surface(halfspace=+1, surface=min_z)
root_cell.add_surface(halfspace=-1, surface=max_z)

# Create root Universe
root_universe = opencg.Universe(universe_id=0, name='root universe')
root_universe.add_cell(root_cell)

# Instantiate OpenCG's linear mesh operators for spatial discretization
fuel_mesh = opencg.LinearMesh('x', fuel_cell.min_x, fuel_cell.max_x, 40)
clad_mesh = opencg.LinearMesh('x', clad_cell.min_x, clad_cell.max_x, 20)
water_mesh = opencg.LinearMesh('x', water_cell.min_x, water_cell.max_x, 40)

# Discretize the fuel, clad and water cells
fuel_cells = fuel_mesh.subdivide_cell(fuel_cell, slab_universe)
clad_cells = clad_mesh.subdivide_cell(clad_cell, slab_universe)
water_cells = water_mesh.subdivide_cell(water_cell, slab_universe)

# Create Geometry and set root Universe
opencg_geometry = opencg.Geometry()
opencg_geometry.root_universe = root_universe

# Get an OpenMC version of this OpenCG geometry
openmc_geometry = openmc.opencg_compatible.get_openmc_geometry(opencg_geometry)

# Instantiate a GeometryFile, register Geometry, and export to XML
geometry_file = openmc.GeometryFile()
geometry_file.geometry = openmc_geometry
geometry_file.export_to_xml()


###############################################################################
#                   Exporting to OpenMC settings.xml File
###############################################################################

# Construct uniform initial source distribution over fissionable zones
lower_left = opencg_geometry.bounds[:3]
upper_right = opencg_geometry.bounds[3:]
source = openmc.source.Source(space=openmc.stats.Box(lower_left, upper_right))
source.only_fissionable = True

# Instantiate a SettingsFile
settings_file = openmc.SettingsFile()
settings_file.batches = batches
settings_file.inactive = inactive
settings_file.particles = particles
settings_file.output = {'tallies': False, 'summary': True}
settings_file.source = source
settings_file.sourcepoint_write = False

# Export to "settings.xml"
settings_file.export_to_xml()


###############################################################################
#                     Exporting to OpenMC plots.xml File
###############################################################################

# Find the edge widths for the geometry's bounding box
delta_x = opencg_geometry.max_x - opencg_geometry.min_x
delta_y = opencg_geometry.max_y - opencg_geometry.min_y
delta_z = opencg_geometry.max_z - opencg_geometry.min_z

# Instantiate a Plot
plot = openmc.Plot()
plot.origin = [delta_x/2., delta_y/2., delta_z/2.]
plot.width = [delta_x, delta_z]
plot.pixels = [250, 250]
plot.color = 'cell'

# Instantiate a PlotsFile, add Plot, and export to "plots.xml"
plot_file = openmc.PlotsFile()
plot_file.add_plot(plot)
plot_file.export_to_xml()


###############################################################################
#                        Create OpenMC MGXS Library
###############################################################################

# Instantiate a 1-group EnergyGroups object
groups = openmc.mgxs.EnergyGroups()
groups.group_edges = [0., 20.]

# Initialize an MGXS Library for OpenMOC
mgxs_lib = openmc.mgxs.Library(openmc_geometry, by_nuclide=False)
mgxs_lib.energy_groups = groups
mgxs_lib.mgxs_types = ['total', 'nu-fission', 'nu-scatter matrix', 'chi']
mgxs_lib.domain_type = 'cell'
mgxs_lib.correction = None
mgxs_lib.domains = openmc_geometry.get_all_material_cells()
mgxs_lib.build_library()

# Create a "tallies.xml" file for the MGXS Library
tallies_file = openmc.TalliesFile()
mgxs_lib.add_to_tallies_file(tallies_file, merge=True)
tallies_file.export_to_xml()


###############################################################################
#                         Run OpenMC Simulation
###############################################################################

# Run OpenMC
executor = openmc.Executor()
executor.run_simulation(output=True, mpi_procs=3)
