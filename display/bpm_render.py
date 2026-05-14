from pydoc import text
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import time
from utils import get_config, get_logger

logger = get_logger(__name__)

DISPLAY_HEIGHT = 640
DISPLAY_WIDTH = 384
DISPLAY_SIZE = (DISPLAY_WIDTH, DISPLAY_HEIGHT)


HEADER_HEIGHT = 42
HEADER_PADDING_X = 10
HEADER_PADDING_Y = 10

TITLE_FONT = ImageFont.truetype('fonts/Ubuntu-M.ttf', 24)
MONO_FONT = ImageFont.truetype('fonts/UbuntuMono-R.ttf', 22)


WEATHER_FONT_SMALL = ImageFont.truetype('fonts/UbuntuMono-R.ttf', 20)
WEATHER_FONT_LARGE = ImageFont.truetype('fonts/UbuntuMono-R.ttf', 28)
# ICON_FONT = ImageFont.truetype('fonts/DejaVuSansMono.ttf', 55)

WIENMOBILRAD_ASSETS_DIR = 'assets/wienmobilrad/'
YR_ASSETS_DIR = 'assets/met_icons/'
IONICONS_ASSETS_DIR = 'assets/ionicons/'


def _display_countdown(num):
    if num == 0:
        return '**'
    else:
        return str(num).zfill(2)


def _format_name(name, length):
    if len(name) > length:
        return name[:(length - 2)] + '…'
    else:
        return name


def _format_addr(addr, length):
    # str.replace is sufficient for now, might cause with 'Tassenplatz' or similar in the future
    if addr.isupper():
        addr = addr.title()
    if len(addr) > length:
        addr = addr.replace('asse', '.') \
            .replace('traße', 'tr.') \
            .replace('latz', 'pl.')
    return _format_name(addr, length)


def render(display_data, weather_data):
    conf = get_config()

    # Setup Image and Draw
    image_black = Image.new('L', DISPLAY_SIZE, 255)  # 255: clear the frame
    draw_black = ImageDraw.Draw(image_black)
    draw_black.fontmode = "L"  # less antialias of fonts

    image_red = Image.new('L', DISPLAY_SIZE, 255)  # 255: clear the frame
    draw_red = ImageDraw.Draw(image_red)
    draw_red.fontmode = "L"  # less antialias of fonts


    draw_red.rectangle(((0, 0), (DISPLAY_WIDTH, HEADER_HEIGHT)), fill=0)

    HEADER_CENTER_Y = HEADER_HEIGHT // 2

    time_text = time.strftime("%H:%M", display_data['lastUpdate'])
    _, time_y = _centered_text_pos(draw_red, time_text, TITLE_FONT, center_x=0, center_y=HEADER_CENTER_Y)
    draw_red.text((HEADER_PADDING_X, time_y), time_text, font=TITLE_FONT, fill=255)

    date_text = time.strftime("%d/%m/%Y", display_data['lastUpdate'])
    bbox = draw_red.textbbox((0, 0), date_text, font=TITLE_FONT)
    date_x = DISPLAY_WIDTH - HEADER_PADDING_X - (bbox[2] - bbox[0])
    _, date_y = _centered_text_pos(draw_red, date_text, TITLE_FONT, center_x=0, center_y=HEADER_CENTER_Y)
    draw_red.text((date_x, date_y), date_text, font=TITLE_FONT, fill=255)


    # Main: Public Transport Data
    y_offset = 55
    for station in sorted(display_data['stations'], key=lambda s: s['name']):
        if 'wienmobilrad' in station:
            draw_red.text((10, y_offset), _format_addr(station['name'], 23), font=TITLE_FONT, fill=0)
            draw_red.bitmap((307, 4 + y_offset),
                            Image.open(WIENMOBILRAD_ASSETS_DIR + 'wienmobilrad.png').resize((25, 20), Image.ANTIALIAS),
                            fill=0)
            draw_red.text((345, 7 + y_offset), station['wienmobilrad']['bikes'].zfill(2), font=MONO_FONT, fill=0)
        else:
            draw_red.text((10, y_offset), _format_addr(station['name'], 26), font=TITLE_FONT, fill=0)

        if 'lines' in station:
            for line in sorted(station['lines'], key=lambda l: l['name'] + l['direction']):
                draw_black.text((10, 35 + y_offset), line['name'], font=MONO_FONT, fill=0)

                line['direction'] = _format_addr(line['direction'], 17)
                draw_black.text((60, 35 + y_offset), line['direction'], font=MONO_FONT, fill=0)

                if line['trafficJam']:
                    draw_red.bitmap((270, 38 + y_offset),
                                    Image.open(IONICONS_ASSETS_DIR + "ionicons_alert_md.png").resize((18, 18),
                                                                                                     Image.ANTIALIAS),
                                    fill=0)

                if len(line['departures']) > 0:
                    if 'walkingTime' in station and station['walkingTime'] + conf['stations']['avgWaitingTime'] >= \
                            line['departures'][0] >= station['walkingTime']:
                        draw_red.text((305, 35 + y_offset), _display_countdown(line['departures'][0]), font=MONO_FONT,
                                      fill=0)
                    else:
                        draw_black.text((305, 35 + y_offset), _display_countdown(line['departures'][0]), font=MONO_FONT,
                                        fill=0)
                    if len(line['departures']) > 1:
                        if 'walkingTime' in station and station['walkingTime'] + conf['stations']['avgWaitingTime'] >= \
                                line['departures'][1] >= station['walkingTime']:
                            draw_red.text((345, 35 + y_offset), _display_countdown(line['departures'][1]),
                                          font=MONO_FONT,
                                          fill=0)
                        else:
                            draw_black.text((345, 35 + y_offset), _display_countdown(line['departures'][1]),
                                            font=MONO_FONT,
                                            fill=0)
                y_offset = y_offset + 25
        y_offset = y_offset + 45

    # Footer: Weather data
    if bool(weather_data):
        draw_red.rectangle(((0, 564), (DISPLAY_WIDTH, DISPLAY_HEIGHT)), fill=0)
        x_offset = 0
        weahter_row_start = 568

        WEATHER_FOOTER_CENTER_Y = weahter_row_start + (DISPLAY_HEIGHT - weahter_row_start) // 2
        TEMP_ROW_Y = weahter_row_start + (DISPLAY_HEIGHT - weahter_row_start) // 3
        WIND_ROW_Y = weahter_row_start + (DISPLAY_HEIGHT - weahter_row_start) * 2 // 3
        RIGHT_MARGIN = DISPLAY_WIDTH - 10
        RIGHT_COLUMN_GAP = 4

        ICON_MARGIN = 12
        footer_height = DISPLAY_HEIGHT - weahter_row_start
        symbol_height = footer_height - ICON_MARGIN * 2
        ICON_X = 10 + x_offset
        ICON_Y = weahter_row_start + (footer_height - symbol_height) // 2

        symbol_code = weather_data['forecast'][0]['symbol']['id']
        icon_path = YR_ASSETS_DIR + symbol_code + '.png'

        try:
            img = Image.open(icon_path)
            img = img.convert("RGBA").resize((symbol_height, symbol_height), Image.LANCZOS)
            draw_red.bitmap((ICON_X, ICON_Y), img, fill=255)
        except FileNotFoundError:
            logger.warning("No icon found for symbol: %s" % symbol_code)


        celsius_text = weather_data['forecast'][0]['celsius']['current'].rjust(3) + '°C'
        celsius_x = ICON_X + symbol_height - ICON_MARGIN // 2
        celsius_y = ICON_Y
        draw_red.text((celsius_x, celsius_y), celsius_text, font=WEATHER_FONT_LARGE, fill=255)


        temp_text = (weather_data['forecast'][0]['celsius']['min'].rjust(2) + '°C' + '-' + weather_data['forecast'][0]['celsius']['max'].rjust(2) + '°C')
        bbox = draw_red.textbbox((0, 0), temp_text, font=WEATHER_FONT_SMALL)
        temp_x = RIGHT_MARGIN - (bbox[2] - bbox[0])
        _, temp_y = _centered_text_pos(draw_red, temp_text, WEATHER_FONT_SMALL, center_x=0, center_y=TEMP_ROW_Y)
        draw_red.text((temp_x, temp_y - RIGHT_COLUMN_GAP), temp_text, font=WEATHER_FONT_SMALL, fill=255)

        # Wind
        wind_text = str(weather_data['forecast'][0]['wind']['mps']).rjust(3) + ' km/h'
        bbox = draw_red.textbbox((0, 0), wind_text, font=WEATHER_FONT_SMALL)
        wind_x = RIGHT_MARGIN - (bbox[2] - bbox[0])
        _, wind_y = _centered_text_pos(draw_red, wind_text, WEATHER_FONT_SMALL, center_x=0, center_y=WIND_ROW_Y)
        draw_red.text((wind_x, wind_y + RIGHT_COLUMN_GAP), wind_text, font=WEATHER_FONT_SMALL, fill=255)
        
        
    return image_black.rotate(90, expand=True), image_red.rotate(90, expand=True)


def render_exception(err, err_type, msg_list=None):
    if msg_list is None:
        msg_list = []
    import textwrap

    image_black = Image.new('L', DISPLAY_SIZE, 255)  # 255: clear the frame
    draw_black = ImageDraw.Draw(image_black)
    image_red = Image.new('L', DISPLAY_SIZE, 255)  # 255: clear the frame
    draw_red = ImageDraw.Draw(image_red)

    y_offset = 20
    draw_red.text((10, y_offset), err_type, font=TITLE_FONT, fill=0)

    lines = textwrap.wrap(err, width=36)

    y_offset = y_offset + 10
    for line in lines:
        y_offset = y_offset + 25
        draw_black.text((10, y_offset), line, font=MONO_FONT, fill=0)

    if msg_list is not []:
        small_mono_font = ImageFont.truetype('fonts/UbuntuMono-R.ttf', 18)
        flattened = lambda li: [i for sublist in li for i in sublist]

        y_offset = y_offset + 5
        formatted_lines = flattened([textwrap.wrap(str(msg), width=36) for msg in msg_list])
        for line in formatted_lines:
            y_offset = y_offset + 25
            draw_black.text((10, y_offset), line, font=small_mono_font, fill=0)

    return image_black, image_red



def _centered_text_pos(draw, text, font, center_x, center_y):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = center_x - text_width // 2
    y = center_y - text_height // 2 - bbox[1]
    return x, y