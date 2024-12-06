from utils.multi_column import column_boxes


def is_two_vertical_blocks(page):
    bboxes = column_boxes(page, no_image_text=False)
    if (len(bboxes) != 2):
        return False
    # Check if the two blocks are vertically aligned
    # The x-coordinates of the two blocks should be close to each other
    x0_1, _, x2_1, _ = bboxes[0]
    x0_2, _, x2_2, _ = bboxes[1]
    return x2_1<x0_2 or x2_2<x0_1