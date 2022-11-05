import mimetypes
import re
import xml.etree.ElementTree
from calendar import month_name
from datetime import datetime
from os import PathLike
from pathlib import Path
from shutil import copy2, move
from typing import Union, Callable

from pymediainfo import MediaInfo


class ImageOrganizer:

    def __init__(self,
                 working_directory: Union[PathLike, str],
                 move_file: bool = False,
                 fast_parse: bool = True):

        self.working_dir = working_directory
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
        root_directory = Path(self.working_dir)
        Path(root_directory / "image_organizer").mkdir(exist_ok=True)

        Path(root_directory / "image_organizer" / "images").mkdir(exist_ok=True)
        self.image_dir = Path(root_directory / "image_organizer" / "images")

        Path(root_directory / "image_organizer" / "videos").mkdir(exist_ok=True)
        self.video_dir = Path(root_directory / "image_organizer" / "videos")

        Path(root_directory / "image_organizer" / "unknown").mkdir(exist_ok=True)
        self.unknown_dir = Path(root_directory / "image_organizer" / "unknown")

    def parse_dir(self,
                  dir_path,
                  get_progress: bool = True,
                  callback: Callable[[dict], None] = None):

        total_dir_files = len(list(Path(dir_path).rglob("*.*")))
        progress = 1

        for searched_file in sorted(Path(dir_path).rglob("*.*")):
            # ensure file is a file
            if Path(searched_file).is_file():

                if get_progress or callback:
                    if not callable(callback):
                        print("Processing file " + str(progress) + " of " + str(total_dir_files))
                    elif callable(callback):
                        callback({"string": "Processing file " + str(progress) + " of " + str(total_dir_files),
                                  "percent": str("{:.1%}".format(int(progress) / int(total_dir_files)))})

                    # determine media type
                    media_type = None
                    if not self.fast_parse:
                        media_type = self._check_filetype_media_info(searched_file)
                    elif self.fast_parse:
                        media_type = self._check_filetype_mime(searched_file)

                    file_date_modified = self._get_modification_time(searched_file)

                    if media_type:
                        # file_date_modified = self._get_modification_time(searched_file)
                        if media_type == "Image":
                            # get date modified and send to images
                            self._img_sorter(searched_file, file_date_modified)
                            self.total_images += 1
                        elif media_type == "Video":
                            # get date modified and send to video
                            self._video_sorter(searched_file, file_date_modified)
                            self.total_videos += 1
                    elif not media_type:
                        # send to unknown folder location
                        self._unknown_sorter(searched_file, file_date_modified)
                        self.total_unknown += 1

            progress += 1

        # update callback with total info at the end of the directory
        if get_progress or callback:
            callback({"total_images": str(self.total_images),
                      "total_videos": str(self.total_videos),
                      "total_unknown": str(self.total_unknown)})

    def _img_sorter(self, file, time):
        # create folders if they don't exist and add them to a variable
        get_year = str(time).split(" ")[0].split("-")[2]
        Path(self.image_dir / get_year).mkdir(exist_ok=True)

        get_month = str(month_name[int(str(time).split(" ")[0].split("-")[0])]).lower()
        Path(self.image_dir / get_year / get_month).mkdir(exist_ok=True)

        file_name = str(time + Path(file).suffix).lower()
        date_dir_file = Path(Path(self.image_dir / get_year / get_month) / str(file_name))

        if not self.move_file:
            if not Path(date_dir_file).exists():
                copy2(src=Path(file), dst=date_dir_file)
            else:
                new_file_name = self._check_for_dupes(self.image_dir, get_year, get_month, file_name)
                copy2(src=Path(file), dst=Path(Path(date_dir_file).parent / new_file_name))
        elif self.move_file:
            if not Path(date_dir_file).exists():
                move(src=Path(file), dst=date_dir_file)
            else:
                new_file_name = self._check_for_dupes(self.image_dir, get_year, get_month, file_name)
                move(src=Path(file), dst=Path(Path(date_dir_file).parent / new_file_name))

    def _video_sorter(self, file, time):
        # create folders if they don't exist and add them to a variable
        get_year = str(time).split(" ")[0].split("-")[2]
        Path(self.video_dir / get_year).mkdir(exist_ok=True)

        get_month = str(month_name[int(str(time).split(" ")[0].split("-")[0])]).lower()
        Path(self.video_dir / get_year / get_month).mkdir(exist_ok=True)

        file_name = str(time + Path(file).suffix).lower()
        date_dir_file = Path(Path(self.video_dir / get_year / get_month) / str(file_name))

        if not self.move_file:
            if not Path(date_dir_file).exists():
                copy2(src=Path(file), dst=date_dir_file)
            else:
                new_file_name = self._check_for_dupes(self.video_dir, get_year, get_month, file_name)
                copy2(src=Path(file), dst=Path(Path(date_dir_file).parent / new_file_name))
        elif self.move_file:
            if not Path(date_dir_file).exists():
                move(src=Path(file), dst=date_dir_file)
            else:
                new_file_name = self._check_for_dupes(self.video_dir, get_year, get_month, file_name)
                move(src=Path(file), dst=Path(Path(date_dir_file).parent / new_file_name))

    def _unknown_sorter(self, file, time):
        # create folders if they don't exist and add them to a variable
        get_year = str(time).split(" ")[0].split("-")[2]
        Path(self.unknown_dir / get_year).mkdir(exist_ok=True)

        get_month = str(month_name[int(str(time).split(" ")[0].split("-")[0])]).lower()
        Path(self.unknown_dir / get_year / get_month).mkdir(exist_ok=True)

        file_name = str(time + Path(file).suffix).lower()
        date_dir_file = Path(Path(self.unknown_dir / get_year / get_month) / str(file_name))

        if not self.move_file:
            if not Path(date_dir_file).exists():
                copy2(src=Path(file), dst=date_dir_file)
            else:
                new_file_name = self._check_for_dupes(self.unknown_dir, get_year, get_month, file_name)
                copy2(src=Path(file), dst=Path(Path(date_dir_file).parent / new_file_name))
        elif self.move_file:
            if not Path(date_dir_file).exists():
                move(src=Path(file), dst=date_dir_file)
            else:
                new_file_name = self._check_for_dupes(self.unknown_dir, get_year, get_month, file_name)
                move(src=Path(file), dst=Path(Path(date_dir_file).parent / new_file_name))

    @staticmethod
    def _check_for_dupes(file_dir, get_year, get_month, file_name):
        get_last_dupe = None
        for x in sorted(Path(Path(file_dir / get_year / get_month)).glob("*.*"), reverse=True):
            get_last_dupe = re.search(r"\((\d+)\)", str(x))

        dupe = ""
        if get_last_dupe:
            dupe = "(" + str(int(get_last_dupe.group(1)) + 1) + ")"
        elif not get_last_dupe:
            dupe = "(1)"

        return Path(str(Path(Path(file_name).name).with_suffix("")) + str(dupe) + str(Path(file_name).suffix))

    @staticmethod
    def _get_modification_time(file):
        return datetime.fromtimestamp(Path(file).stat().st_mtime).replace(microsecond=0).strftime("%m-%d-%Y [%H.%M.%S]")

    @staticmethod
    def _check_filetype_mime(file):
        parse_mime = mimetypes.guess_type(file)
        if "image" in str(parse_mime):
            return "Image"
        elif "video" in str(parse_mime):
            return "Video"
        else:
            return None

    @staticmethod
    def _check_filetype_media_info(file):
        # mi = MediaInfo.parse(file, mediainfo_options={"File_TestContinuousFileNames": "0"})
        try:
            mi = MediaInfo.parse(file, mediainfo_options={"File_TestContinuousFileNames": "0"}, parse_speed=0.1)
            return mi.tracks[1].track_type
        except IndexError:
            return None
        except Exception as e:
            with open(r"E:\Pictures\exception.txt", "a") as f:
                f.write(str(e) + "\n")
            return None

    # def parse_extensions(self, dir_path):
    #     for searched_file in Path(dir_path).rglob("*.*"):
    #         print(searched_file.suffix)


if __name__ == '__main__':
    # file1 = r"F:\IMPORTANT BACKUP\Pictures\2014-12-01\001.JPG"
    # file3 = r"F:\IMPORTANT BACKUP\Pictures\My Movie.mp4"
    file2 = r"F:\IMPORTANT BACKUP\Pictures"
    # dir1 = r"F:\IMPORTANT BACKUP\Pictures\00\00000000000\00"


    def test(x):
        print(x)
        # with open(r"C:\Users\jlw_4\Desktop\output.txt", "a") as y:
        #     y.write(str(x) + "\n")
        pass


    job = ImageOrganizer(working_directory=r"E:\Pictures", move_file=False, fast_parse=False)
    # job.parse_file(file3)
    job.parse_dir(file2, callback=test)
