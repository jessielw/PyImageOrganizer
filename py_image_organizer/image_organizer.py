import mimetypes
import re
from calendar import month_name
from datetime import datetime
from os import PathLike
from pathlib import Path
from shutil import copy2, move
from typing import Union, Callable

from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS
from pymediainfo import MediaInfo


class ImageOrganizer:
    def __init__(
        self,
        working_directory: Union[PathLike, str],
        image_dir_name: str = "images",
        video_dir_name: str = "videos",
        unknown_dir_name: str = "unknown",
        move_file: bool = False,
        fast_parse: bool = False,
    ):
        """
        Sorts files to images, videos, and unknown. By default (fast_parse=False) it will use the mediainfo library
        to correctly parse all files to see if they are an image or video. Anything that is not an image or video is
        sorted into the unknown directory.

        :param working_directory: Full path for the output of the sorted files.
        :param image_dir_name: A string for the image folder-name.
        :param video_dir_name: A string for the video folder-name.
        :param unknown_dir_name: A string for the unknown folder-name.
        :param move_file: If this is set to 'True' then the program will move instead of copying the files. (this
            will significantly speed the progress up if the files are on the same drive)
            Default is 'False' (copy)
        :param fast_parse: If set to 'True' the program will not sort files with mediainfo. This will speed things up
            to a degree but substantially decrease accuracy. As it uses the mimetypes library from python which
            doesn't correctly handle all files and only checks the files by extension.
            Default is 'False'
        """

        # default variables
        self.working_dir = working_directory
        self.image_dir_name = image_dir_name
        self.video_dir_name = video_dir_name
        self.unknown_dir_name = unknown_dir_name
        self.move_file = move_file
        self.fast_parse = fast_parse

        # variables
        self.image_dir = None
        self.video_dir = None
        self.unknown_dir = None

        # total files processed
        self.total_images = 0
        self.total_videos = 0
        self.total_unknown = 0

        # make directories
        self._make_directories()

    def _make_directories(self):
        """creates sorting directories if not known"""
        root_directory = Path(self.working_dir)
        Path(root_directory).mkdir(exist_ok=True)

        Path(root_directory / self.image_dir_name).mkdir(exist_ok=True)
        self.image_dir = Path(root_directory / self.image_dir_name)

        Path(root_directory / self.video_dir_name).mkdir(exist_ok=True)
        self.video_dir = Path(root_directory / self.video_dir_name)

        Path(root_directory / self.unknown_dir_name).mkdir(exist_ok=True)
        self.unknown_dir = Path(root_directory / self.unknown_dir_name)

    def parse_dir(
        self,
        dir_path,
        get_progress: bool = True,
        recursive_search: bool = True,
        callback: Callable[[dict], None] = None,
    ):
        """
        Parses provided directory

        :param dir_path: Full path string/Pathlike object to parse.
        :param get_progress: If set to 'True' the program will show the user progress of the task.
        :param recursive_search: If set to 'True' it will search for files in all directories in the provided path.
        :param callback: Set this to a function on the script calling ImageSorter to get call back information
        :return: None
        """

        glob_dir = []

        # use rglob if recursively searched
        if recursive_search:
            glob_dir = [x for x in sorted(Path(dir_path).rglob("*.*"))]
        elif not recursive_search:
            glob_dir = [x for x in sorted(Path(dir_path).glob("*.*"))]

        # needed variables
        total_dir_files = len(glob_dir)
        progress = 1

        # search the director(y/ies)
        for searched_file in glob_dir:
            if Path(searched_file).is_file():

                # handle progress/callback information here
                if get_progress or callback:
                    if not callable(callback):
                        print(
                            "Processing file "
                            + str(progress)
                            + " of "
                            + str(total_dir_files)
                        )
                    elif callable(callback):
                        callback(
                            {
                                "string": "Processing file "
                                + str(progress)
                                + " of "
                                + str(total_dir_files),
                                "percent": str(
                                    "{:.1%}".format(
                                        int(progress) / int(total_dir_files)
                                    )
                                ),
                            }
                        )

                    # determine media type
                    media_type = None
                    if not self.fast_parse:
                        media_type = self._check_filetype_media_info(searched_file)
                    elif self.fast_parse:
                        media_type = self._check_filetype_mime(searched_file)

                    # attempt to get exif data
                    file_creation_date = self._get_exif(searched_file)

                    # if unable to get exif data fallback to modification time
                    if not file_creation_date:
                        file_creation_date = self._get_modification_time(searched_file)

                    # if media_type is returned with anything other than None
                    if media_type:
                        # get date modified and send to images
                        if media_type == "Image":
                            self._img_sorter(searched_file, file_creation_date)
                            self.total_images += 1

                        # get date modified and send to video
                        elif media_type == "Video":
                            self._video_sorter(searched_file, file_creation_date)
                            self.total_videos += 1

                    # if media_type is None, send to unknown folder location
                    elif not media_type:
                        self._unknown_sorter(searched_file, file_creation_date)
                        self.total_unknown += 1

            # update progress counter
            progress += 1

        # update callback with total info at the end of the directory search
        if get_progress or callback:
            callback(
                {
                    "total_images": str(self.total_images),
                    "total_videos": str(self.total_videos),
                    "total_unknown": str(self.total_unknown),
                }
            )

    def _img_sorter(self, file, time):
        """
        create folders if they don't exist and add them to a variable

        :param file: image/video/unknown file
        :param time: exif datetime or file date modified
        :return: None
        """
        get_year = str(time).split(" ")[0].split("-")[2]
        Path(self.image_dir / get_year).mkdir(exist_ok=True)

        get_month = str(month_name[int(str(time).split(" ")[0].split("-")[0])]).lower()
        Path(self.image_dir / get_year / get_month).mkdir(exist_ok=True)

        file_name = str(time + Path(file).suffix).lower()
        date_dir_file = Path(
            Path(self.image_dir / get_year / get_month) / str(file_name)
        )

        if not self.move_file:
            if not Path(date_dir_file).exists():
                copy2(src=Path(file), dst=Path(date_dir_file))
            else:
                new_file_name = self._check_for_dupes(
                    self.image_dir, get_year, get_month, file_name
                )
                copy2(
                    src=Path(file), dst=Path(Path(date_dir_file).parent / new_file_name)
                )
        elif self.move_file:
            if not Path(date_dir_file).exists():
                move(src=Path(file), dst=date_dir_file)
            else:
                new_file_name = self._check_for_dupes(
                    self.image_dir, get_year, get_month, file_name
                )
                move(
                    src=Path(file), dst=Path(Path(date_dir_file).parent / new_file_name)
                )

    def _video_sorter(self, file, time):
        """
        create folders if they don't exist and add them to a variable

        :param file: image/video/unknown file
        :param time: exif datetime or file date modified
        :return: None
        """
        get_year = str(time).split(" ")[0].split("-")[2]
        Path(self.video_dir / get_year).mkdir(exist_ok=True)

        get_month = str(month_name[int(str(time).split(" ")[0].split("-")[0])]).lower()
        Path(self.video_dir / get_year / get_month).mkdir(exist_ok=True)

        file_name = str(time + Path(file).suffix).lower()
        date_dir_file = Path(
            Path(self.video_dir / get_year / get_month) / str(file_name)
        )

        if not self.move_file:
            if not Path(date_dir_file).exists():
                copy2(src=Path(file), dst=date_dir_file)
            else:
                new_file_name = self._check_for_dupes(
                    self.video_dir, get_year, get_month, file_name
                )
                copy2(
                    src=Path(file), dst=Path(Path(date_dir_file).parent / new_file_name)
                )
        elif self.move_file:
            if not Path(date_dir_file).exists():
                move(src=Path(file), dst=date_dir_file)
            else:
                new_file_name = self._check_for_dupes(
                    self.video_dir, get_year, get_month, file_name
                )
                move(
                    src=Path(file), dst=Path(Path(date_dir_file).parent / new_file_name)
                )

    def _unknown_sorter(self, file, time):
        """
        create folders if they don't exist and add them to a variable

        :param file: image/video/unknown file
        :param time: exif datetime or file date modified
        :return: None
        """
        get_year = str(time).split(" ")[0].split("-")[2]
        Path(self.unknown_dir / get_year).mkdir(exist_ok=True)

        get_month = str(month_name[int(str(time).split(" ")[0].split("-")[0])]).lower()
        Path(self.unknown_dir / get_year / get_month).mkdir(exist_ok=True)

        file_name = str(time + Path(file).suffix).lower()
        date_dir_file = Path(
            Path(self.unknown_dir / get_year / get_month) / str(file_name)
        )

        if not self.move_file:
            if not Path(date_dir_file).exists():
                copy2(src=Path(file), dst=date_dir_file)
            else:
                new_file_name = self._check_for_dupes(
                    self.unknown_dir, get_year, get_month, file_name
                )
                copy2(
                    src=Path(file), dst=Path(Path(date_dir_file).parent / new_file_name)
                )
        elif self.move_file:
            if not Path(date_dir_file).exists():
                move(src=Path(file), dst=date_dir_file)
            else:
                new_file_name = self._check_for_dupes(
                    self.unknown_dir, get_year, get_month, file_name
                )
                move(
                    src=Path(file), dst=Path(Path(date_dir_file).parent / new_file_name)
                )

    def _check_filetype_media_info(self, file):
        try:
            mi = MediaInfo.parse(
                file,
                mediainfo_options={"File_TestContinuousFileNames": "0"},
                parse_speed=0.1,
            )
            return mi.tracks[1].track_type
        except IndexError:
            return None
        except Exception as e:
            with open(
                Path(
                    Path(self.working_dir)
                    / Path(
                        "exception_log "
                        + str(datetime.now().strftime("%b-%d-%Y [%H.%M.%S]"))
                        + ".txt"
                    )
                ),
                "a",
            ) as f:
                f.write(str("\nFilename: " + str(file)) + "\n" + str(e) + "\n\n")
            return None

    def _get_exif(self, file):
        try:
            open_image = Image.open(file).getexif()
        except (UnidentifiedImageError, OSError):
            return None
        except Exception as e:
            with open(
                Path(
                    Path(self.working_dir)
                    / Path(
                        "exception_log"
                        + str(datetime.now().strftime("%b-%d-%Y [%H.%M.%S]"))
                        + ".txt"
                    )
                ),
                "a",
            ) as f:
                f.write(str("\nFilename: " + str(file)) + "\n" + str(e) + "\n\n")
            return None

        exif_key = None
        for exif_key, value in TAGS.items():
            if value == "ExifOffset":
                break
        info = open_image.get_ifd(exif_key)

        exif_dict = {
            TAGS.get(exif_key, exif_key): value for exif_key, value in info.items()
        }

        if exif_dict:
            try:
                exif_date_time_original = str(exif_dict["DateTimeOriginal"]).replace(
                    "\x00", ""
                )

                if exif_date_time_original == "00-00-0000 [00:00:00]":
                    return None

                # convert from "2013:10:01 09:17:50" to "10-01-2013 [09.17.50]"
                date_month = str(exif_date_time_original).split(" ")[0].split(":")
                date_time = str(exif_date_time_original).split(" ")[1].replace(":", ".")
                return (
                    date_month[1]
                    + "-"
                    + date_month[2]
                    + "-"
                    + date_month[0]
                    + " "
                    + "["
                    + date_time
                    + "]"
                )
            except (KeyError, IndexError):
                return None

    @staticmethod
    def _check_for_dupes(file_dir, get_year, get_month, file_name):
        get_last_dupe = None
        for x in sorted(
            Path(Path(file_dir / get_year / get_month)).glob("*.*"), reverse=True
        ):
            get_last_dupe = re.search(r"\((\d+)\)", str(x))

        dupe = ""
        if get_last_dupe:
            dupe = "(" + str(int(get_last_dupe.group(1)) + 1) + ")"
        elif not get_last_dupe:
            dupe = "(1)"

        return Path(
            str(Path(Path(file_name).name).with_suffix(""))
            + str(dupe)
            + str(Path(file_name).suffix)
        )

    @staticmethod
    def _get_modification_time(file):
        return (
            datetime.fromtimestamp(Path(file).stat().st_mtime)
            .replace(microsecond=0)
            .strftime("%m-%d-%Y [%H.%M.%S]")
        )

    @staticmethod
    def _check_filetype_mime(file):
        parse_mime = mimetypes.guess_type(file)
        if "image" in str(parse_mime):
            return "Image"
        elif "video" in str(parse_mime):
            return "Video"
        else:
            return None


if __name__ == "__main__":
    directory_to_parse = r"F:\IMPORTANT BACKUP\Pictures"
    output_directory = r"E:\Pictures\sorted"

    def callback_example(x):
        """This will output the progress and at the end the total progress"""
        print(x)

    job = ImageOrganizer(
        working_directory=output_directory, move_file=False, fast_parse=False
    )
    job.parse_dir(directory_to_parse, callback=callback_example)
