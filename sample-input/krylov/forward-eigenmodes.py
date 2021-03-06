import openmoc

###############################################################################
#                          Main Simulation Parameters
###############################################################################

options = openmoc.options.Options()

num_threads = options.getNumThreads()
track_spacing = options.getTrackSpacing()
num_azim = options.getNumAzimAngles()
tolerance = options.getTolerance()
max_iters = options.getMaxIterations()
num_modes = 5

openmoc.log.set_log_level('NORMAL')
openmoc.log.py_printf('TITLE', 'Computing %d forward eigenmodes', num_modes)


###############################################################################
#                          Creating the TrackGenerator
###############################################################################

openmoc.log.py_printf('NORMAL', 'Initializing the track generator...')

from geometry import geometry
track_generator = openmoc.TrackGenerator(geometry, num_azim, track_spacing)
track_generator.setNumThreads(num_threads)
track_generator.generateTracks()


###############################################################################
#                            Running a Simulation
###############################################################################

# Initialize a CPUSolver to perform forward fixed source calculations
cpu_solver = openmoc.CPUSolver(track_generator)
cpu_solver.setNumThreads(num_threads)

# Initialize IRAMSolver to perform forward eigenmode calculation
iram_solver = openmoc.krylov.IRAMSolver(cpu_solver)
iram_solver.computeEigenmodes(num_modes=num_modes, solver_mode=openmoc.FORWARD)

# Report the forward eigenvalues to the user
eigenvalues = iram_solver._eigenvalues
openmoc.log.py_printf('RESULT', 'Forward eigenvalues: %s', str(eigenvalues))


###############################################################################
#                             Generating Plots
###############################################################################

openmoc.log.py_printf('NORMAL', 'Plotting data...')

openmoc.plotter.plot_materials(geometry, gridsize=500)
openmoc.plotter.plot_cells(geometry, gridsize=500)
openmoc.plotter.plot_flat_source_regions(geometry, gridsize=500)
openmoc.plotter.plot_eigenmode_fluxes(iram_solver, gridsize=250,
                                      energy_groups=[1,2,3,4,5,6,7])

openmoc.log.py_printf('TITLE', 'Finished')
