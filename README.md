# Py Image Organizer

Easily sort images, videos, and random files by year/month/date and time.

Program uses the exif data to properly get date taken. If this cannot be found it will fall back to date modified. 

Developed by Jessie Wilson (2022)

## Install

`pip install PyImageSorter`

**If using Linux you must also install MediaInfo**

`sudo apt install mediainfo`

## Uninstall

`pip uninstall PyImageSorter`

## Examples of How To Use

**Example with callback**

```python
from py_image_organizer import ImageOrganizer

directory_to_parse = r"F:\IMPORTANT BACKUP\Pictures"
output_directory = r"E:\Pictures\sorted"

def callback_example(x):
    """
    This will output the progress and at the end the total progress in a dictionary
    
    Example: {'string': 'Processing file 57 of 133874', 'percent': '0.0%'}
    You can access either of these with x["string"] or x["percent"]
    
    At the very end of the job the program will output a total
    print(x)
    {"total_images": "20000",
    "total_videos": "3200",
    "total_unknown": "1901"}
    """
    print(x)

image_organizer = ImageOrganizer(working_directory=output_directory)
image_organizer.parse_dir(directory_to_parse, callback=callback_example)

```

\
**Example without callback**

When not using callback the output is automatically printed to console in the format of a string.

```python
from py_image_organizer import ImageOrganizer

directory_to_parse = r"F:\IMPORTANT BACKUP\Pictures"
output_directory = r"E:\Pictures\sorted"

image_organizer = ImageOrganizer(working_directory=output_directory)
image_organizer.parse_dir(directory_to_parse)

"If you'd like to disable the output completely just set get_progress=False"
image_organizer.parse_dir(directory_to_parse, get_progress=False)

```

## ImageOrganizer Parameters

`working_directory` Full path for the output of the sorted files.

`image_dir_name` A string for the image folder-name.

`video_dir_name` A string for the video folder-name.

`unknown_dir_name` A string for the unknown folder-name.

`move_file` If this is set to 'True' then the program will move instead of copying the files. (this will significantly speed the progress up if the files are on the same drive)\
*Default is 'False' (copy)*

`fast_parse` If set to 'True' the program will not sort files with mediainfo. This will speed things up to a degree but substantially decrease accuracy. As it uses the mimetypes library from python which doesn't correctly handle all files and only checks the files by extension.\
*Default is 'False'*

## parse_dir() Parameters

`dir_path` Full path string/Pathlike object to parse.

`get_progress` If set to 'True' the program will show the user progress of the task.\
*Default is 'True'*

`recursive_search` If set to 'True' it will search for files in all directories in the provided path.\
*Default is 'True'*

`callback` Set this to a function on the script calling ImageSorter to get call back information\
*Default is 'None'*
