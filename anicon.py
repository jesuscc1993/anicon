import argparse
import os
import re
import sys
import traceback

from PIL import Image, ImageOps
# noinspection PyPackageRequirements
from mal import AnimeSearch, MangaSearch
from requests import get
from warnings import filterwarnings

filterwarnings('ignore')

COVER_IMAGE_FILENAME = 'cover.jpg'
FOLDER_IMAGE_FILENAME = 'folder.jpg'
DESKTOP_INI_FILENAME = 'desktop.ini'

SKIPPED_ALREADY_EXISTING = 'Skipping "{}", which already has an icon.'

WORDS_TO_REMOVE_REGEX = r'\b(?:BLURAY|X265|X264|HEVC|HI10P|AVC|10BIT|DUAL|AUDIO|ENG|ENGLISH|SUBBED|SUB|DUBBED|DUB)\b'
LAST_WORDS_REGEX = r'\b(?:BD|S0|480P|720P|1080P)\b.*$'

BRACKETS_OR_PARENS_REGEX = r'\[[^\]]*\]|\([^\)]*\)|\(\)|\[\]'

def get_name(folder_name: str) -> str:
  folder_name = re.sub(r'[_.]', ' ', folder_name)
  folder_name = re.sub(WORDS_TO_REMOVE_REGEX, '', folder_name, flags = re.IGNORECASE)
  folder_name = re.sub(BRACKETS_OR_PARENS_REGEX, '', folder_name, flags = re.IGNORECASE)
  folder_name = re.sub(LAST_WORDS_REGEX, '', folder_name, flags = re.IGNORECASE)
  return folder_name.strip()

def get_artwork(media_name: str, max_results: int = 5, media_type: str = 'anime') -> tuple:
  results, counter, choice = None, 1, 0
  if media_type == 'anime':
    results = AnimeSearch(media_name).results
  elif media_type == 'manga':
    results = MangaSearch(media_name).results
  else:
    raise Exception('Invalid mode specified')

  if not auto_mode:
    print(f'\n{media_name}\n X  Skip this folder')

  for result in results:
    if auto_mode:
      choice = 0
      break
    else:
      counter_str = f'({counter})' if counter == 1 else f' {counter} '
      print(f'{counter_str} [{result.type}] {result.title}')

    if counter == max_results:
      break
    counter += 1

  if not auto_mode:
    choice = input('> ')
    if choice == '':
      choice = 1
    elif choice.upper() == 'X':
      return None, None
    choice = int(choice) - 1

  image_url = results[choice].image_url
  image_type = results[choice].type

  return image_url, image_type

def download_cover(img_link: str):
  art = get(img_link)
  open(cover_image_path, 'wb').write(art.content)

def create_icon(keep_cover: bool, target_ratio: float = None):
  if os.path.isfile(cover_image_path):
    img_path = cover_image_path
  elif os.path.isfile(folder_image_path):
    img_path = folder_image_path
  else:
    raise FileNotFoundError('No cover image found')

  img = Image.open(img_path)
  if target_ratio is not None:
    old_w, old_h = img.size
    current_ratio = old_w / old_h

    if current_ratio != target_ratio:
      x0, y0, x1, y1 = 0, 0, old_w, old_h

      if current_ratio > target_ratio:
        new_w = round(old_h * target_ratio)
        x0 = (old_w - new_w) // 2
        x1 = x0 + new_w
      elif current_ratio < target_ratio:
        new_h = round(old_w / target_ratio)
        y0 = (old_h - new_h) // 2
        y1 = y0 + new_h

      img = img.crop((x0, y0, x1, y1))

  img = ImageOps.pad(img, (256, 256), color=(0, 0, 0, 0)).convert('RGBA')

  new_data = []
  for item in img.getdata():
    if item[0] == 0 and item[1] == 0 and item[2] == 0:
      new_data.append((0, 0, 0, 0))
    else:
      new_data.append(item)

  img.putdata(new_data)

  if not keep_cover:
    os.remove(cover_image_path)

  img.save(ico_path, format='ICO', sizes=[(256, 48), (256, 256), (16, 16)])
  img.close()
  return ico_path

def handle_exception(e):
  print('Ran into an error.')
  for line in traceback.format_exception(None, e, e.__traceback__):
    print(line, end = '')
  input('Press Enter to continue...')

if __name__ == '__main__':
  print('''\
Run this in your anime/manga folder
For help and info, check out
https://github.com/jesuscc1993/anicon''')

  if len(sys.argv) > 1:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('--auto-mode', '-a', action='store_true', help='Use AutoMode (non-interactive)')
    parser.add_argument('--max-results', '-n', type=int, help='Max results to show (default 5)')
    parser.add_argument('--media-type', '-m', choices=['anime', 'manga'], help='Media type: (anime/manga)')
    parser.add_argument('--keep-cover', '-k', action='store_true', help='Save cover image')
    parser.add_argument('--ratio', '-r', type=float, help='Aspect ratio for icon crop (e.g. 2/3 = 0.67)')
    args = parser.parse_args()

    auto_mode = bool(args.auto_mode)
    max_results = 1 if auto_mode else (args.max_results if args.max_results is not None else 5)
    media_type = args.media_type or 'anime'
    keep_cover = args.keep_cover if args.keep_cover is not None else (media_type == 'manga')
    ratio = args.ratio if args.ratio else None

    print('''
Using arguments:
  auto_mode   : {}
  max_results : {}
  media_type  : {}
  keep_cover  : {}
'''.format(auto_mode, max_results, media_type, keep_cover))

  else:
    auto_mode = input('''
Use Auto Mode? Y/N:
(Default = N)
> ''').upper() == 'Y'

    if auto_mode:
      max_results = 1
    else:
      max_results = input('''
Max Results:
(Default = 5)
> ''')
      try:
        max_results = int(max_results)
      except ValueError:
        max_results = 5

    media_type = input('''
Media Type:
(1) anime
 2  manga
> ''')
    if media_type == '2':
      media_type = 'manga'
      keep_cover = input('''
Save cover? Y/N:
(Default = Y)
> ''').upper() != 'N'
    else:
      media_type = 'anime'
      keep_cover = False

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

    icon_name = re.sub('[^A-Za-z0-9_,. ()-]', '_', name)

    ico_file = icon_name + '.ico'
    ico_path = os.path.join(folder, ico_file)
    ini_path = os.path.join(folder, DESKTOP_INI_FILENAME)
    cover_image_path = os.path.join(folder, COVER_IMAGE_FILENAME)
    folder_image_path = os.path.join(folder, FOLDER_IMAGE_FILENAME)

    try:
      if os.path.isfile(ico_path):
        print(SKIPPED_ALREADY_EXISTING.format(folder))
        continue

      if os.path.isfile(ini_path):
        with open(ini_path, 'r') as f:
          if 'IconResource' in f.read():
            print(SKIPPED_ALREADY_EXISTING.format(folder))
            continue

      artwork_url, artwork_type = None, None
      if os.path.isfile(cover_image_path) or os.path.isfile(folder_image_path):
        print(f'Using already existing cover image for "{folder}".')
        keep_cover = True
      else:
        for file_path in [ico_path, ini_path]:
          if os.path.isfile(file_path):
            os.remove(file_path)

        artwork_url, artwork_type = get_artwork(name, max_results, media_type)
        if not artwork_url or not artwork_type:
          print(f'Skipping "{folder}" since artwork could not be retrieved.')
          continue

        try:
          download_cover(artwork_url)
        except Exception as e:
          handle_exception(e)
          continue

      create_icon(keep_cover, ratio)

      with open(ini_path, 'w+') as f:
        f.write('[.ShellClassInfo]\nConfirmFileOp=0\n')
        f.write('IconResource={},0'.format(ico_file))
        f.write('\nIconFile={}\nIconIndex=0'.format(ico_file))

        if artwork_type:
          f.write('\nInfoTip={}'.format(artwork_type))

      f.close()

      os.system('attrib +h +s \"{}\"'.format(ini_path))
      os.system('attrib +h \"{}\"'.format(ico_path))
      os.system('attrib +s \"{}\"'.format(folder))

      if auto_mode:
        print(f'Generated icon for folder "{folder}".')
    except Exception as e:
      handle_exception(e)
      continue

  input('Press Enter to exit...')