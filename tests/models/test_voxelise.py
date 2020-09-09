import os
import pytest
import numpy as np
from sksurgeryvtk.models import voxelise
import vtk
from vtk.util import numpy_support

""" These are regression tests to ensure that we get the same result(s) as
running the standalone code from the original repository.
This is not by any means a thorough set of tests, just confirming the
functionality we want it for at present (August 2020). """

if not os.path.exists('tests/data/output/voxelise'):
    os.makedirs('tests/data/output/voxelise')

def test_liver_stl_voxelisation():
    """ If this test doesn't run, then subsequent tests will fail, as they
    expect the data generated by this test to be present. """
    #Tutorial-section-1-start
    input_mesh = 'tests/data/voxelisation/liver_downsample.stl'
    output_grid = "tests/data/output/voxelise/voxelised.vts"

    # Voxelisation will throw an error if the file already exists with a preoperative surface array.
    if os.path.exists(output_grid):
        os.remove(output_grid)

    signed_df = True
    center = True
    scale_input = 0.001
    size = 0.3
    grid_elements = 64
    #Tutorial-section-1-end

    #Tutorial-section-2-start
    grid = voxelise.voxelise(input_mesh=input_mesh,
                            output_grid=output_grid,
                            signed_df=signed_df,
                            center=center,
                            scale_input=scale_input,
                            size=size,
                            grid_elements=64)
    #Tutorial-section-2-end


    # Check dimensions correct
    cell_dims = [0, 0, 0]
    grid.GetCellDims(cell_dims)
    assert cell_dims == [63, 63, 63]

    numpy_data = voxelise.extract_array_from_grid(grid, 'preoperativeSurface')

    # Cells 'inside' the liver have negative values, so this should be
    # consistent
    cells_in_liver = numpy_data < 0
    assert np.count_nonzero(cells_in_liver) == 14628

def test_extract_arrays_from_model_file():

    # Contains data written by previous tests
    output_grid = "tests/data/output/voxelise/voxelised.vts"

    preoperative = \
        voxelise.extract_array_from_grid_file(output_grid,
                                              'preoperativeSurface')
    
def test_intraop_surface_voxelisation():
    """ test_liver_stl_voxelisation needs to have run successfully for this
    to work correctly. """
    #Tutorial-section-3-start
    input_mesh = 'tests/data/voxelisation/intraop_surface.stl'
    output_grid = "tests/data/output/voxelise/voxelised.vts"

    # If the output_grid doesn't exist, we can't run this test
    assert os.path.exists(output_grid)

    signed_df = False
    reuse_transform = True
    size = 0.3
    grid_elements = 64

    grid = voxelise.voxelise(input_mesh=input_mesh,
                            output_grid=output_grid,
                            signed_df=signed_df,
                            reuse_transform=reuse_transform,
                            size=size,
                            grid_elements=grid_elements
                            )
    #Tutorial-section-3-end

    # Check dimensions correct
    cell_dims = [0, 0, 0]
    grid.GetCellDims(cell_dims)
    assert cell_dims == [63, 63, 63]

    # Check array name is correct
    numpy_data = voxelise.extract_array_from_grid(grid, 'intraoperativeSurface')
    print("Numpy data" ,numpy_data)
    # Cells on the intraop surface should have a value between 0 and the voxel size
    voxel_size = size/grid_elements
    cells_on_surface = numpy_data < voxel_size

    assert np.count_nonzero(cells_on_surface) == 2059


def test_intraop_from_numpy():
    """ test_liver_stl_voxelisation needs to have run successfully for this
    to work correctly. """

    # Using a different name here so that we don't have to remove 
    # the 'intraoperativeSurface' that was made by the previous test.
    # Normally, we wouldn't specify this new name.
    output_grid = "tests/data/output/voxelise/voxelised.vts"

    # If the output_grid doesn't exist, we can't run this test
    assert os.path.exists(output_grid)

    signed_df = False
    reuse_transform = True
    size = 0.3
    grid_elements = 64
    # Same surface as the previous test, but saved as points rather than surface
    #Tutorial-section-4-start

    input_mesh = 'tests/data/voxelisation/intraop_surface.xyz'
    numpy_mesh = np.loadtxt(input_mesh)
    array_name = "point_intraoperativeSurface"

    grid = voxelise.voxelise(input_mesh=numpy_mesh,
                            array_name=array_name,
                            output_grid=output_grid,
                            signed_df=signed_df,
                            reuse_transform=reuse_transform,
                            size=size,
                            grid_elements=grid_elements
                            )
    #Tutorial-section-4-end

    # Check dimensions correct
    cell_dims = [0, 0, 0]
    grid.GetCellDims(cell_dims)
    assert cell_dims == [63, 63, 63]

    numpy_data = voxelise.extract_array_from_grid(grid, array_name)
    # Cells on the intraop surface should have a value between 0 and the voxel size
    voxel_size = size/grid_elements
    cells_on_surface = numpy_data < voxel_size
    print(cells_on_surface)
    assert np.count_nonzero(cells_on_surface) == 1956


def test_voxelise_more_than_one_surface():
    # Voxelise a preop surface, then voxelise more than one intraoperative
    #surface. The second surface should overwrite the first

    input_mesh = 'tests/data/voxelisation/intraop_surface.xyz'
    numpy_mesh = np.loadtxt(input_mesh)

    grid_size = 64
    grid = voxelise.voxelise(input_mesh=numpy_mesh,
                            signed_df=True,
                            center=True,
                            scale_input=0.001,
                            grid_elements=grid_size
                            )

    points_a = np.random.random((1000,3))
    points_b = np.random.random((1000,3))

    grid = voxelise.voxelise(input_mesh=points_a,
                            output_grid=grid,
                            signed_df=False,
                            reuse_transform=True
                            )

    numpy_data_a = voxelise.extract_array_from_grid(grid, 'intraoperativeSurface')

    grid = voxelise.voxelise(input_mesh=points_b,
                            output_grid=grid,
                            signed_df=False,
                            reuse_transform=True
                            )

    numpy_data_b = voxelise.extract_array_from_grid(grid, 'intraoperativeSurface')
    assert not np.allclose(numpy_data_a, numpy_data_b)

def test_save_load_array_in_grid():

    dims = 8
    grid = voxelise.createGrid(1, dims)
    data_preop = np.random.random((dims**3, 3))
    data_intraop = np.random.random((dims**3, 3))

    preop_name = 'preoperativeSurface'
    intraop_name = 'intraoperativeSurface'
    # Save in vtk grid
    voxelise.save_displacement_array_in_grid(data_preop, grid, preop_name)
    voxelise.save_displacement_array_in_grid(data_intraop, grid, intraop_name)

    # Read data back from vtk grid
    preop, intraop = voxelise.extract_surfaces_for_v2snet(grid)


    assert np.array_equal(preop, data_preop)
    assert np.array_equal(intraop, data_intraop)

def test_apply_displacement_field_to_mesh():

    #Tutorial-section-5-start
    input_mesh = "tests/data/voxelisation/liver_downsample.stl"
    displacement_grid = "tests/data/voxelisation/voxelizedResult.vts"

    displaced_mesh = \
        voxelise.apply_displacement_to_mesh(input_mesh,
                                            displacement_grid,
                                            save_mesh="tests/data/output/voxelise/deformed.vtp")
    #Tutorial-section-5-end

    # Do some basic checking on the result
    point_data = displaced_mesh.GetPoints().GetData()
    numpy_data = numpy_support.vtk_to_numpy(point_data)

    mean_values = np.mean(numpy_data, axis=0)
    expected_mean = [ -41.47275, 1.8251724, 1530.5344]

    assert numpy_data.shape == (2582, 3)
    assert np.allclose(mean_values, expected_mean)

# Above tests are based on writing data to/from disk to save the grid, which
# how it works in Micha's orginal work. A more practical workflow is to 
# keep the grid in memory and work with it directly, so this test does that.
def test_entire_workflow():
    #Tutorial-section-6-start
    input_mesh = 'tests/data/voxelisation/liver_downsample.stl'

    signed_df = True
    center = True
    scale_input = 0.001

    # No output_mesh passed to voxelise(), a new grid will be created.
    grid = voxelise.voxelise(input_mesh=input_mesh,
                            signed_df=signed_df,
                            center=center,
                            scale_input=scale_input
                            )

    input_intraop = 'tests/data/voxelisation/intraop_surface.xyz'
    numpy_intraop = np.loadtxt(input_intraop)

    signed_df = False
    reuse_transform = True

    grid = voxelise.voxelise(input_mesh=numpy_intraop,
                            output_grid=grid,
                            signed_df=signed_df,
                            reuse_transform=reuse_transform
                            )

    preop, intraop = voxelise.extract_surfaces_for_v2snet(grid)

    # Load displacement data previously calculated using V2SNet
    # This would be calculated on the fly in a 'real' implementation e.g.
    # displacement = v2snet.predict(preop, intraop)
    displacement_grid = "tests/data/voxelisation/voxelizedResult.vts"
    displacement = voxelise.extract_array_from_grid_file(displacement_grid, "estimatedDisplacement")
    np.savetxt('disp_extracted.txt', displacement)
    voxelise.save_displacement_array_in_grid(displacement, grid)

    displaced_mesh = voxelise.apply_displacement_to_mesh(input_mesh,
                                                        grid,
                                                        save_mesh="tests/data/output/voxelise/deformed_no_saved_grid.vtp")
    #Tutorial-section-6-end

    point_data = displaced_mesh.GetPoints().GetData()
    numpy_data = numpy_support.vtk_to_numpy(point_data)

    mean_values = np.mean(numpy_data, axis=0)
    expected_mean = [ -41.47275, 1.8251724, 1530.5344]

    assert numpy_data.shape == (2582, 3)
    assert np.allclose(mean_values, expected_mean)


# class LoadDisplacmentFromFile:

#     def get_displacement(self, grid):
#         displacement_grid = "tests/data/voxelisation/voxelizedResult.vts"
#         displacement = voxelise.extract_array_from_grid_file(displacement_grid, "estimatedDisplacement")

#         return displacement

# def test_non_rigid_class():

#     input_mesh = 'tests/data/voxelisation/liver_downsample.stl'
#     scale_input = 0.001
#     input_intraop = 'tests/data/voxelisation/intraop_surface.xyz'
#     numpy_intraop = np.loadtxt(input_intraop)

#     non_rigid_alignment = \
#         voxelise.NonRigidAlignment(input_mesh,
#                                    displacement_estimator=LoadDisplacmentFromFile(),
#                                    scale_input=scale_input)

#     non_rigid_alignment.load_surface(numpy_intraop)
#     non_rigid_alignment.calculate_displacement()
    
#     displaced_mesh = non_rigid_alignment.displace_model(input_mesh)
    
#     point_data = displaced_mesh.GetPoints().GetData()
#     numpy_data = numpy_support.vtk_to_numpy(point_data)

#     mean_values = np.mean(numpy_data, axis=0)
#     expected_mean = [ -41.47275, 1.8251724, 1530.5344]

#     assert numpy_data.shape == (2582, 3)
#     assert np.allclose(mean_values, expected_mean)