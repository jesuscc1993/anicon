import os
import re
import traceback
from warnings import filterwarnings

from PIL import Image, ImageOps
# noinspection PyPackageRequirements
from mal import AnimeSearch, MangaSearch
from requests import get

filterwarnings("ignore")

def get_name(folder_name: str) -> str:
    last_words = ['bd', 's0', '480p', '720p', '1080p']
    words_to_remove = [
      'bluray', 'x265', 'x264', 'hevc', 'hi10p', 'avc', '10bit', 'dual',
      'audio', 'eng', 'english', 'subbed', 'sub', 'dubbed', 'dub'
    ]

    folder_name = folder_name.lower().replace('_', ' ').replace('.', ' ')

    for word in words_to_remove:
        folder_name = folder_name.replace(word, '')

    folder_name = re.sub(r"(?<=\[)(.*?)(?=])", '', folder_name)
    folder_name = re.sub(r"(?<=\()(.*?)(?=\))", '', folder_name)
    folder_name = folder_name.replace('()', '').replace('[]', '')

    for word in last_words:
        regex_str = "(?<=" + word + ").*$"
        folder_name = re.sub(regex_str, '', folder_name, flags=re.DOTALL).replace(word, '')

    return folder_name.strip()


def get_artwork(media_name: str, max_results: int = 5, mode: str = "anime") -> tuple:
    print('\n' + media_name.title())

    counter, choice = 1, 0
    if mode == "anime":
        results = AnimeSearch(media_name).results
        for result in results:
            if auto_mode:
                print(' - ' + result.title)
                choice = 1
                break
            else:
                print(str(counter) + ' - ' + result.title)

            if counter == max_results:
                break
            counter += 1
    elif mode == "manga":
        results = MangaSearch(media_name).results
        for result in results:
            if auto_mode:
                print(' - ' + result.title)
                choice = 1
                break
            else:
                print(str(counter) + ' - ' + result.title)

            if counter == max_results:
                break
            counter += 1
    else:
        raise Exception("Invalid mode specified")
    print("X - Skip this folder")

    if not auto_mode:
        choice = input('> ')
        if choice == '':
            choice = 1
        elif choice.upper() == "X":
            return None, None
        choice = int(choice) - 1

    image_url = results[choice].image_url
    image_type = results[choice].type

    return image_url, image_type


def create_icon(img_link: str):
    art = get(img_link)
    open(jpg_file, 'wb').write(art.content)

    img = Image.open(jpg_file)
    img = ImageOps.expand(img, (69, 0, 69, 0), fill=0)
    img = ImageOps.fit(img, (300, 300)).convert("RGBA")

    datas = img.getdata()
    new_data = []
    for item in datas:
        if item[0] == 0 and item[1] == 0 and item[2] == 0:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    os.remove(jpg_file)
    img.save(ico_file)
    img.close()
    return ico_file

if __name__ == "__main__":
    print("""\
Run this in your anime/manga folder
For help, info and memes, check out
https://github.com/notdedsec/anicon
""")
    auto_mode = True if input('Use AutoMode? Y/N : ').upper() == 'Y' else False
    max_res = input("Max Results (default 5): ")
    try:
        max_res = int(max_res)
    except ValueError:
        max_res = 5

    media_mode = input("""\

Media Mode:
1. anime (default)
2. manga
> """)
    if media_mode == "2":
        media_mode = "manga"
    else:
        media_mode = "anime"

    folder_list = next(os.walk('.'))[1]
    if folder_list is None or len(folder_list) == 0:
        # In case the file is placed inside an innermost directory which
        # contains only files and no other folders, this list will be empty.
        # Thus adding the current directory path as an element of the list.
        folder_list = [str(os.getcwd())]

    for folder in folder_list:
        name = get_name(folder)

        # Extracting the name of the folder without the path and then performing
        # search for the same. This will be the name of the anime episode /
        # manga chapter, thus instead of performing a search for the directory
        # path, now performing a search for the directory name.
        name = name.rpartition('\\')[2].strip()

        icon_name = re.sub("[^A-Za-z0-9_,. ()-]", "_", name)
        jpg_file = folder + '\\' + icon_name + '.jpg'
        ico_file = folder + '\\' + icon_name + '.ico'

        if os.path.isfile(folder + "\\" + "desktop.ini"):
            print('An icon is already present. Delete the older icon and `desktop.ini` file before applying a new icon')
            continue

        link, artwork_type = get_artwork(name, max_results=max_res, mode=media_mode)
        if not link or not artwork_type:
            print("Skipping this folder...")
            continue

        try:
            icon = create_icon(link)
        except Exception as e:
            print('Ran into an error while creating the icon object. Blame the dev :(')
            for line in traceback.format_exception(None, e, e.__traceback__):
                print(line, end="")
            continue

        try:
            f = open(folder + "\\desktop.ini", "w+")

            f.write("[.ShellClassInfo]\nConfirmFileOp=0\n")
            f.write("IconResource={},0".format(ico_file.replace(folder, "").strip("\\")))
            f.write("\nIconFile={}\nIconIndex=0".format(ico_file.replace(folder, "").strip("\\")))

            if artwork_type is not None and len(artwork_type) > 0:
                # If the result has a type, then using this as the info-tip for
                # the desktop icon.
                f.write("\nInfoTip={}".format(artwork_type))

            # Closing the output stream.
            # All the text will be written into `desktop.ini` file only when the
            # output is being closed.
            f.close()

            # Not marking the `desktop.ini` file as a system file.
            # This will make sure that the file can be seen if display hidden
            # items is enabled.
            os.system('attrib +r \"{}\\{}\"'.format(os.getcwd(), folder))
            os.system('attrib +h \"{}\\desktop.ini\"'.format(folder))
            os.system('attrib +h \"{}\"'.format(icon))
        except Exception as e:
            print('Ran into an error while creating files. Blame the dev :(')
            for line in traceback.format_exception(None, e, e.__traceback__):
                print(line, end="")
            continue
