def _low_bresenham_line(
    pt1: tuple[int, int], pt2: tuple[int, int]
) -> list[tuple[int, int]]:
    """
    Implements Bresenham Algorithm to rasterize a line for slopes from -0.5 to
    0.5.

    Parameters
    ----------
    pt1: tuple[int, int]
        Starting point for the line.
    pt2: tuple[int, int]
        Ending point for the line.

    Returns
    -------
    pt_list: list[tuple[int, int]]
        All the pixels that intersect the line.
    """

    dx = pt2[0] - pt1[0]
    dy = pt2[1] - pt1[1]

    if dy < 0:
        y_change = -1
        dy *= -1
    else:
        y_change = 1

    if dx < 0:
        x_change = -1
        dx *= -1
    else:
        x_change = 1

    diff = (2 * dy) - dx

    pixels: list[tuple[int, int]] = []

    x, y = pt1
    n = 0
    while True:
        n += 1

        pixels.append((x, y))

        if x == pt2[0] and y == pt2[1]:
            break

        x += x_change

        if diff > 0:
            y += y_change
            diff += 2 * (dy - dx)
        else:
            diff += 2 * dy

        if n > 100:
            print("Low Slope Bresenham Line missed the endpoint.")
            return pixels

    return pixels


def _high_bresenham_line(
    pt1: tuple[int, int], pt2: tuple[int, int]
) -> list[tuple[int, int]]:
    """
    Implements Bresenham Algorithm to rasterize a line for slopes < -0.5 or >
    0.5.

    Parameters
    ----------
    pt1: tuple[int, int]
        Starting point for the line.
    pt2: tuple[int, int]
        Ending point for the line.

    Returns
    -------
    pt_list: list[tuple[int, int]]
        All the pixels that intersect the line.
    """

    dx = pt2[0] - pt1[0]
    dy = pt2[1] - pt1[1]

    if dx < 0:
        print("Negative High Slope")
        x_change = -1
        dx *= -1
    else:
        print("Positive High Slope")
        x_change = 1

    if dy < 0:
        print("Negative Y Change")
        y_change = -1
        dy *= -1
    else:
        y_change = 1

    diff = (2 * dx) - dy

    pixels: list[tuple[int, int]] = []

    x, y = pt1
    n = 0
    while True:
        n += 1

        pixels.append((x, y))

        if x == pt2[0] and y == pt2[1]:
            break

        y += y_change

        if diff > 0:
            x += x_change
            diff += 2 * (dx - dy)
        else:
            diff += 2 * dx

        if n > 100:
            print("High Slope Bresenham Line missed the endpoint.")
            return pixels

    return pixels


def get_bresenham_line(
    pt1: tuple[int, int], pt2: tuple[int, int]
) -> list[tuple[int, int]]:
    if abs(pt2[1] - pt1[1]) < abs(pt2[0] - pt1[0]):
        return _low_bresenham_line(pt1, pt2)
    else:
        return _high_bresenham_line(pt1, pt2)
