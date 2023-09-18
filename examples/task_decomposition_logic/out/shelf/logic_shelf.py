

move_hand()  # move hand to the spam; <spam>: on_something(<table>)
grasp_object()  # grasp the spam; <spam>: inside_hand()
detach_from_plane()  # detach the spam from the table; <spam>: inside_hand()

# Move the spam near the camera
move_hand()  # move the spam near the camera; <spam>: inside_hand()

# Check the best-by date of the spam
check_best_by_date()  # <spam>: inside_hand()

# If the best-by date is expired, throw it away
if not check_best_by_date():
    move_hand()  # move hand near the trash bin; <spam>: inside_hand()
    release_object()  # release the spam to drop it in the trash bin; <spam>: inside_something(<trash_bin>)
# If the best-by date is not expired, put it on the shelf
else:
    move_hand()  # move hand to the shelf; <spam>: inside_hand()
    move_hand()  # move the spam to the shelf; <spam>: inside_hand()
    attach_to_plane()  # place the spam on the shelf; <spam>: on_something(<shelf_top>)
    release_object()  # release the spam; <spam>: on_something(<shelf_top>)
