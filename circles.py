# import numpy and maplotlib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
from shapely.geometry import Polygon, MultiPolygon
from shapely import set_precision

global precision, min_area
precision = 1e-15
min_area = 1e-4


# define a function to parse arguments
def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Plotting polygons.")
    parser.add_argument("-n", "--number", type=int, default=10, help="number of polygons to plot")
    parser.add_argument("-s", "--sides", type=int, default=4, help="number of sides for each polygons")
    parser.add_argument("-r", "--radius", type=float, default=0.2, help="size of the polygons")
    parser.add_argument("--seed", type=int, default=42, help="random initilization seed")
    parser.add_argument("--prefix", type=str, default=None, help="prefix for the output files")

    return parser.parse_args()


# define a function to plot a polygon
def plot_polygon(ax, polygon, colour="blue", filled=True):
    mpl_polygon = patches.Polygon(
        np.array(polygon.exterior.coords),
        closed=True,
        color=colour,
        alpha=1.0,
        fill=filled,
    )
    ax.add_patch(mpl_polygon)


# define a function to plot the polygons
def plot_polygons(poly_list, name="polygons.png", filled=True):
    # Generate a list of unique colors
    colours = plt.get_cmap("plasma")

    # create a figure and axis
    fig, ax = plt.subplots()
    colour_indexes = np.linspace(0, 1, len(poly_list))  # create a list of unique colors

    # loop over the polygons and plot them
    for poly, colour_index in zip(poly_list, colour_indexes):
        plot_polygon(ax, polygon=poly, colour=colours(colour_index), filled=filled)

    # set the aspect of the plot to be equal
    ax.set_aspect("equal")

    # write the plot to a file
    plt.savefig(name)
    plt.close()


# define a function to create the polygons
def create_polygons(gen, n, s, r):
    # create a list of polygons
    poly_list = []
    # loop over the number of polygons
    for i in range(n):
        # create a random x and y
        x, y = gen.random(2)

        # generate the polygon
        poly = generate_polygon(gen, x=x, y=y, s=s, r=r)

        # add the polygon to the list
        poly_list.append(poly)

    # return the list of polygons
    return poly_list


def generate_polygon(gen, x, y, s, r):

    # use the generator to deterimine the starting angle
    theta = gen.random() * 2 * np.pi

    # Generate n equally spaced angles between 0 and 2π
    angles = np.linspace(0, 2 * np.pi, s, endpoint=False)

    # Calculate the x and y coordinates for points on the circle
    xp = x + r * np.cos(angles + theta)
    yp = y + r * np.sin(angles + theta)

    # Combine the x and y coordinates
    points = list(zip(xp, yp))

    # # Randomly shuffle the points
    # np.random.shuffle(points)

    # Return the list of points
    return points


# turn the list of polygons into a list of shapely polygons
def shapely_polygons(poly_list):
    global precision

    # create a list of shapely polygons
    shp_list = []
    # loop over the polygons
    for poly in poly_list:
        # create a shapely polygon
        shp_poly = Polygon(poly)
        shp_poly = set_precision(shp_poly, grid_size=precision)

        # add the polygon to the list
        shp_list.append(shp_poly)
    # return the list of shapely polygons
    return shp_list


# add each of the polygons, one at a time. If the polygon intersects with any of the previous polygons, break it
# into smaller polygons
def add_polygon(shp_list, new_poly, count=0):

    if len(shp_list) == 0:
        return [new_poly]

    # create a list of polygons
    final_list = []
    poly_check_list = [new_poly]

    intersection_list = np.zeros(len(shp_list))

    # loop over the polygons
    while len(poly_check_list) > 0:
        # if poly_index >= len(shp_list):
        #     final_list.extend(poly_check_list)
        #     break
        # else:
        new_poly = poly_check_list.pop(0)
        intersection = False
        for i in range(len(shp_list)):
            if intersection_list[i] == 1:
                # skip the polygons that have already been intersected
                continue

            poly = shp_list[i]
            if poly.intersects(new_poly):
                sub_polys, remainder = break_polygon(poly, new_poly)
                final_list.extend(sub_polys)
                poly_check_list.extend(remainder)
                intersection = True
                intersection_list[i] = 1
                break
        if not intersection:
            final_list.append(new_poly)

    for i in range(len(intersection_list)):
        if intersection_list[i] == 0:
            final_list.append(shp_list[i])

    # # return the final list of polygons
    return final_list


def clean_polygons(poly_object):
    global precision, min_area

    out_list = []
    if poly_object.geom_type == "Polygon":
        poly = set_precision(poly_object, grid_size=precision)
        if not poly.is_empty and poly.is_valid and poly.area > min_area:
            out_list.append(poly)
    elif poly_object.geom_type == "MultiPolygon":
        for poly in poly_object.geoms:
            poly = set_precision(poly, grid_size=precision)
            if not poly.is_empty and poly.is_valid and poly.area > min_area:
                out_list.append(poly)
    elif poly_object.geom_type == "GeometryCollection":
        for poly in poly_object.geoms:
            if poly.geom_type == "Polygon":
                poly = set_precision(poly, grid_size=precision)
                if not poly.is_empty and poly.is_valid and poly.area > min_area:
                    out_list.append(poly)

    return out_list


# break the polygon into smaller polygons
def break_polygon(poly, intersecting_poly):

    p1 = poly.difference(intersecting_poly)
    p1 = clean_polygons(p1)

    p2 = poly.intersection(intersecting_poly)
    p2 = clean_polygons(p2)

    p3 = intersecting_poly.difference(poly)
    p3 = clean_polygons(p3)

    # return the list of polygons
    return p1 + p2, p3


def main():
    # parse the arguments
    args = parse_args()

    # create a random number generator
    gen = np.random.default_rng(args.seed)

    # create the polygons
    poly_list = create_polygons(gen, n=args.number, s=args.sides, r=args.radius)
    poly_list = shapely_polygons(poly_list)

    # plot the polygons
    plot_polygons(poly_list, name="polygons.png", filled=False)

    # turn the list of polygons into a list of shapely polygons
    shp_polys = []
    for count, poly in enumerate(poly_list):
        shp_polys = add_polygon(shp_polys, poly, count)
        plot_polygons(shp_polys, name=f"final_list_{count}.png")
        print(f"After adding {count}, Number of polygons: {len(shp_polys)}")

    # plot the polygons
    prefix_str = ""
    if args.prefix is not None:
        prefix_str = args.prefix + "_"
    plot_polygons(shp_polys, name=f"{prefix_str}shapely_polygons-{args.sides:04}.png")

    print(f"Number of polygons: {len(shp_polys)}")


# if this is the main module, call the main function
if __name__ == "__main__":
    main()
