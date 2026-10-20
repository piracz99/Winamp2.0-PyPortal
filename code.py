import os
import time

import audioio
import audiomixer
import audiomp3
import board
import digitalio
import displayio
import sdcardio
import storage
import terminalio

from adafruit_display_text import label
from adafruit_touchscreen import Touchscreen


display = board.DISPLAY
display.auto_refresh = False

BLACK = 0x090D0A
PANEL = 0x172019
ROW = 0x202820
GREEN = 0x8CFF00
WHITE = 0xE8F2E8
GRAY = 0x718071

DISPLAY_UPDATE_INTERVAL = 1.0
MIXER_BUFFER_SIZE = 4096
CROSSFADE_SECONDS = 5.0
VOLUME_RAMP_SECONDS = 5.0
AUDIO_LEVEL_UPDATE_INTERVAL = 0.05

screen = displayio.Group()


def add_rect(x, y, width, height, color):
    bitmap = displayio.Bitmap(width, height, 1)
    bitmap.fill(0)
    palette = displayio.Palette(1)
    palette[0] = color
    tile = displayio.TileGrid(bitmap, pixel_shader=palette, x=x, y=y)
    screen.append(tile)
    return palette


add_rect(0, 0, display.width, display.height, BLACK)
add_rect(0, 0, display.width, 22, PANEL)
add_rect(0, 21, display.width, 2, GREEN)

brand = label.Label(terminalio.FONT, text="WINAMP 2.0  |  PYPORTAL", color=GREEN)
brand.x = 8
brand.y = 13
screen.append(brand)

volume_label = label.Label(terminalio.FONT, text="VOL", color=GREEN)
volume_label.x = display.width - 112
volume_label.y = 13
screen.append(volume_label)
volume_left = display.width - 82
volume_width = 48
volume_top = 11
volume_height = 4
volume_percent = 50
volume_bitmap = displayio.Bitmap(volume_width, volume_height, 2)
volume_palette = displayio.Palette(2)
volume_palette[0] = GRAY
volume_palette[1] = GREEN
volume_track = displayio.TileGrid(
    volume_bitmap,
    pixel_shader=volume_palette,
    x=volume_left,
    y=volume_top,
)
screen.append(volume_track)
volume_knob_width = 6
volume_knob_bitmap = displayio.Bitmap(volume_knob_width, 12, 1)
volume_knob_palette = displayio.Palette(1)
volume_knob_palette[0] = WHITE
volume_knob = displayio.TileGrid(
    volume_knob_bitmap,
    pixel_shader=volume_knob_palette,
    x=volume_left + (volume_width - volume_knob_width) // 2,
    y=volume_top - 4,
)
screen.append(volume_knob)
volume_percent_label = label.Label(terminalio.FONT, text="50%", color=WHITE)
volume_percent_label.x = display.width - 30
volume_percent_label.y = 13
screen.append(volume_percent_label)

track_title = label.Label(terminalio.FONT, text="SD MP3 PLAYER", color=WHITE)
track_title.x = 8
track_title.y = 39
screen.append(track_title)

progress_left = 8
progress_top = 48
progress_width = display.width - 16
progress_height = 5
progress_bitmap = displayio.Bitmap(progress_width, progress_height, 2)
progress_palette = displayio.Palette(2)
progress_palette[0] = GRAY
progress_palette[1] = GREEN
progress_track = displayio.TileGrid(
    progress_bitmap,
    pixel_shader=progress_palette,
    x=progress_left,
    y=progress_top,
)
screen.append(progress_track)
progress_knob_width = 8
progress_knob_bitmap = displayio.Bitmap(progress_knob_width, 13, 1)
progress_knob_palette = displayio.Palette(1)
progress_knob_palette[0] = WHITE
progress_knob = displayio.TileGrid(
    progress_knob_bitmap,
    pixel_shader=progress_knob_palette,
    x=progress_left,
    y=progress_top - 4,
)
screen.append(progress_knob)

playlist_header = label.Label(terminalio.FONT, text="PLAYLIST", color=GREEN)
playlist_header.x = 8
playlist_header.y = 69
screen.append(playlist_header)

count_label = label.Label(terminalio.FONT, text="0 UTWOROW", color=GRAY)
count_label.y = 69
screen.append(count_label)

list_top = 81
row_height = 14
visible_rows = 6
row_left = 8
row_width = display.width - 46
row_backgrounds = []
row_labels = []
for row_index in range(visible_rows):
    y = list_top + row_index * row_height
    row_backgrounds.append(add_rect(row_left, y, row_width, row_height - 1, ROW))
    item_label = label.Label(terminalio.FONT, text="", color=WHITE)
    item_label.x = row_left + 4
    item_label.y = y + 9
    screen.append(item_label)
    row_labels.append(item_label)

up_background = add_rect(display.width - 31, list_top, 23, 26, PANEL)
up_label = label.Label(terminalio.FONT, text="UP", color=GREEN)
up_label.x = display.width - 29
up_label.y = list_top + 14
screen.append(up_label)
down_y = list_top + (visible_rows - 1) * row_height
down_background = add_rect(display.width - 31, down_y, 23, 16, PANEL)
down_label = label.Label(terminalio.FONT, text="DN", color=GREEN)
down_label.x = display.width - 29
down_label.y = down_y + 9
screen.append(down_label)

controls_y = 171
control_width = 70
control_height = 30
control_gap = 7
controls_left = (display.width - 4 * control_width - 3 * control_gap) // 2
control_names = ["PREV", "PLAY", "NEXT", "STOP"]
control_labels = []
control_backgrounds = []
for index, name in enumerate(control_names):
    x = controls_left + index * (control_width + control_gap)
    control_backgrounds.append(
        add_rect(x, controls_y, control_width, control_height, PANEL)
    )
    button_label = label.Label(terminalio.FONT, text=name, color=GREEN)
    button_label.x = x + (control_width - len(name) * 6) // 2
    button_label.y = controls_y + control_height // 2
    screen.append(button_label)
    control_labels.append(button_label)

time_label = label.Label(terminalio.FONT, text="00:00", color=WHITE)
time_label.x = 8
time_label.y = 220
screen.append(time_label)

status_label = label.Label(terminalio.FONT, text="Wczytywanie SD...", color=GRAY)
status_label.y = 220
screen.append(status_label)

display.root_group = screen

touchscreen = Touchscreen(
    board.TOUCH_XL,
    board.TOUCH_XR,
    board.TOUCH_YD,
    board.TOUCH_YU,
    calibration=((5200, 59000), (5800, 57000)),
    size=(display.width, display.height),
)

speaker_enable = digitalio.DigitalInOut(board.SPEAKER_ENABLE)
speaker_enable.direction = digitalio.Direction.OUTPUT
speaker_enable.value = True
speaker_audio = audioio.AudioOut(board.SPEAKER)
audio_mixer = None
audio_mixer_format = None

sd_card = None
sd_filesystem = None
sd_error = None
tracks = []
try:
    sd_card = sdcardio.SDCard(board.SPI(), board.SD_CS)
    sd_filesystem = storage.VfsFat(sd_card)
    storage.mount(sd_filesystem, "/sd")
    tracks = [
        filename
        for filename in os.listdir("/sd")
        if filename.lower().endswith(".mp3")
    ]
    tracks.sort(key=lambda filename: filename.lower())
except (OSError, RuntimeError, ValueError) as error:
    sd_error = str(error)
    print("SD/playlist error: {}".format(sd_error))

selected_track = None
current_file = None
decoder = None
is_paused = False
track_started_at = None
pause_started_at = None
paused_seconds = 0
track_file_size = 0
track_audio_start = 0
track_duration = 0
track_seek_index = []
playback_started = False
seek_mute_until = None
pending_seek_preroll = 0
active_voice = 0
next_file = None
next_decoder = None
next_track_index = None
next_track_file_size = 0
next_track_audio_start = 0
next_track_duration = 0
next_track_seek_index = None
next_track_format = None
crossfade_started_at = None
volume_ramp_started_at = None
last_audio_level_update = 0
list_offset = 0
last_elapsed = -1
last_status_update = 0
last_progress_position = -1


def set_status(text):
    status_label.text = text[:20]
    status_label.x = display.width - len(status_label.text) * 6 - 8


def set_title(text):
    track_title.text = text[:50]


def refresh_playlist():
    count_label.text = "{} UTWOROW".format(len(tracks))
    count_label.x = display.width - len(count_label.text) * 6 - 8
    for row_index, item_label in enumerate(row_labels):
        track_index = list_offset + row_index
        if track_index < len(tracks):
            filename = tracks[track_index]
            display_name = filename[:-4]
            if len(display_name) > 44:
                display_name = display_name[:41] + "..."
            item_label.text = "{} {}".format(track_index + 1, display_name)
            row_backgrounds[row_index][0] = (
                GREEN if track_index == selected_track else ROW
            )
            item_label.color = BLACK if track_index == selected_track else WHITE
        else:
            item_label.text = ""
            row_backgrounds[row_index][0] = ROW
    display.refresh()


def format_time(seconds):
    seconds = max(0, int(seconds))
    return "{}:{:02d}".format(seconds // 60, seconds % 60)


def elapsed_time():
    if track_started_at is None:
        return 0
    now = pause_started_at if is_paused else time.monotonic()
    return now - track_started_at - paused_seconds


def refresh_volume_control():
    filled_width = (volume_percent * (volume_width - 1)) // 100
    for x in range(volume_width):
        color = 1 if x <= filled_width else 0
        for y in range(volume_height):
            volume_bitmap[x, y] = color
    volume_knob.x = min(
        volume_left + volume_width - volume_knob_width,
        max(
            volume_left,
            volume_left + filled_width - volume_knob_width // 2,
        ),
    )
    volume_percent_label.text = "{}%".format(volume_percent)
    volume_percent_label.x = display.width - len(volume_percent_label.text) * 6 - 4


def set_volume_from_touch(touch_x):
    global volume_percent

    position = min(
        volume_width - 1, max(0, touch_x - volume_left)
    )
    new_volume = position * 100 // (volume_width - 1)
    if new_volume == volume_percent:
        return False

    volume_percent = new_volume
    update_audio_levels(force=True)
    refresh_volume_control()
    return True


def configure_audio_mixer(mixer_format):
    global audio_mixer, audio_mixer_format

    if mixer_format == audio_mixer_format:
        return

    if audio_mixer is not None:
        audio_mixer.voice[0].stop()
        audio_mixer.voice[1].stop()
        audio_mixer.voice[0].level = 0
        audio_mixer.voice[1].level = 0
        if speaker_audio.playing:
            time.sleep(0.03)
            speaker_audio.stop()
        audio_mixer.deinit()

    sample_rate, channel_count, bits_per_sample = mixer_format
    audio_mixer = audiomixer.Mixer(
        voice_count=2,
        buffer_size=MIXER_BUFFER_SIZE,
        channel_count=channel_count,
        bits_per_sample=bits_per_sample,
        samples_signed=True,
        sample_rate=sample_rate,
    )
    audio_mixer.voice[0].level = 0
    audio_mixer.voice[1].level = 0
    audio_mixer_format = mixer_format


def update_audio_levels(force=False):
    global last_audio_level_update

    if audio_mixer is None or decoder is None:
        return
    now = time.monotonic()
    if (
        not force
        and now - last_audio_level_update < AUDIO_LEVEL_UPDATE_INTERVAL
    ):
        return
    last_audio_level_update = now

    if volume_ramp_started_at is None:
        ramp = 1.0
    else:
        ramp = min(1.0, max(0.0, (now - volume_ramp_started_at) / VOLUME_RAMP_SECONDS))
    master_level = volume_percent / 100 * ramp
    if seek_mute_until is not None and now < seek_mute_until:
        master_level = 0
    if pending_seek_preroll > 0 and is_paused:
        master_level = 0
    if crossfade_started_at is None:
        audio_mixer.voice[active_voice].level = master_level
        audio_mixer.voice[1 - active_voice].level = 0
    else:
        crossfade = min(
            1.0,
            max(0.0, (now - crossfade_started_at) / CROSSFADE_SECONDS),
        )
        audio_mixer.voice[active_voice].level = master_level * (1 - crossfade)
        audio_mixer.voice[1 - active_voice].level = master_level * crossfade


def start_decoder_audio(sample_decoder, voice_index, level=0):
    sample_format = (
        sample_decoder.sample_rate,
        sample_decoder.channel_count,
        sample_decoder.bits_per_sample,
    )
    configure_audio_mixer(sample_format)
    audio_mixer.voice[voice_index].level = level
    audio_mixer.voice[voice_index].play(sample_decoder, loop=False)
    if not speaker_audio.playing:
        speaker_audio.play(audio_mixer)


def load_track(index):
    path = "/sd/{}".format(tracks[index])
    new_file = None
    new_decoder = None
    try:
        new_file = open(path, "rb")
        new_file.seek(0, 2)
        file_size = new_file.tell()
        audio_start = mp3_audio_start(new_file, file_size)
        first_frame, _, _ = find_mp3_frame(new_file, audio_start, file_size)
        audio_start = first_frame
        duration, seek_index = index_mp3_track(new_file, audio_start, file_size)
        new_file.seek(0)
        new_decoder = audiomp3.MP3Decoder(new_file)
        sample_format = (
            new_decoder.sample_rate,
            new_decoder.channel_count,
            new_decoder.bits_per_sample,
        )
    except (OSError, RuntimeError, ValueError, MemoryError):
        if new_decoder is not None:
            new_decoder.deinit()
        if new_file is not None:
            new_file.close()
        raise
    return (
        new_file,
        new_decoder,
        file_size,
        audio_start,
        duration,
        seek_index,
        sample_format,
    )


def close_track_resources(track_file, track_decoder):
    if track_decoder is not None:
        track_decoder.deinit()
    if track_file is not None:
        track_file.close()


def clear_next_track():
    global next_file, next_decoder, next_track_index
    global next_track_file_size, next_track_audio_start, next_track_duration
    global next_track_seek_index, next_track_format

    close_track_resources(next_file, next_decoder)
    next_file = None
    next_decoder = None
    next_track_index = None
    next_track_file_size = 0
    next_track_audio_start = 0
    next_track_duration = 0
    next_track_seek_index = None
    next_track_format = None


def preload_next_track():
    global next_file, next_decoder, next_track_index
    global next_track_file_size, next_track_audio_start, next_track_duration
    global next_track_seek_index, next_track_format

    if len(tracks) < 2 or selected_track is None:
        return
    next_track_index = (selected_track + 1) % len(tracks)
    try:
        (
            next_file,
            next_decoder,
            next_track_file_size,
            next_track_audio_start,
            next_track_duration,
            next_track_seek_index,
            next_track_format,
        ) = load_track(next_track_index)
    except (OSError, RuntimeError, ValueError, MemoryError) as error:
        print("MP3 preload error: {}".format(error))
        next_track_index = None
        next_file = None
        next_decoder = None
        next_track_file_size = 0
        next_track_audio_start = 0
        next_track_duration = 0
        next_track_seek_index = None
        next_track_format = None


def start_crossfade():
    global crossfade_started_at, next_track_format

    if (
        audio_mixer is None
        or next_decoder is None
        or next_track_format != audio_mixer_format
        or crossfade_started_at is not None
    ):
        return False
    incoming_voice = 1 - active_voice
    try:
        audio_mixer.voice[incoming_voice].play(next_decoder, loop=False)
    except (OSError, RuntimeError, ValueError, MemoryError) as error:
        print("MP3 crossfade start error: {}".format(error))
        next_track_format = None
        set_status("BEZ NAKLADANIA")
        return False
    crossfade_started_at = time.monotonic()
    set_status("PRZEJSCIE")
    update_audio_levels(force=True)
    return True


def finish_crossfade():
    global current_file, decoder, selected_track, active_voice
    global track_file_size, track_audio_start, track_duration, track_seek_index
    global track_started_at, crossfade_started_at, playback_started
    global last_elapsed, last_progress_position, list_offset
    global paused_seconds, pause_started_at
    global next_file, next_decoder, next_track_index, next_track_file_size
    global next_track_audio_start, next_track_duration, next_track_seek_index
    global next_track_format

    if next_file is None or next_decoder is None:
        crossfade_started_at = None
        return False

    old_file = current_file
    old_decoder = decoder
    old_voice = active_voice
    fade_started_at = crossfade_started_at

    active_voice = 1 - active_voice
    current_file = next_file
    decoder = next_decoder
    selected_track = next_track_index
    track_file_size = next_track_file_size
    track_audio_start = next_track_audio_start
    track_duration = next_track_duration
    track_seek_index = next_track_seek_index
    track_started_at = fade_started_at
    paused_seconds = 0
    pause_started_at = None
    crossfade_started_at = None
    playback_started = True
    last_elapsed = -1
    last_progress_position = -1

    next_file = None
    next_decoder = None
    next_track_index = None
    next_track_file_size = 0
    next_track_audio_start = 0
    next_track_duration = 0
    next_track_seek_index = None
    next_track_format = None
    audio_mixer.voice[old_voice].stop()
    audio_mixer.voice[old_voice].level = 0
    close_track_resources(old_file, old_decoder)

    if selected_track < list_offset:
        list_offset = selected_track
    elif selected_track >= list_offset + visible_rows:
        list_offset = selected_track - visible_rows + 1
    refresh_playlist()
    set_title(tracks[selected_track])
    set_status("ODTWARZANIE")
    update_audio_levels(force=True)
    preload_next_track()
    return True


def mp3_frame_info(header):
    if len(header) != 4:
        return None

    value = int.from_bytes(header, "big")
    if value >> 21 != 0x7FF:
        return None

    version = (value >> 19) & 0x03
    layer = (value >> 17) & 0x03
    bitrate_index = (value >> 12) & 0x0F
    sample_rate_index = (value >> 10) & 0x03
    if version == 0x01 or layer != 0x01 or bitrate_index in (0, 0x0F):
        return None
    if sample_rate_index == 0x03:
        return None

    mpeg1_bitrates = (
        0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320
    )
    mpeg2_bitrates = (
        0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160
    )
    sample_rates = (44100, 48000, 32000)
    bitrate = (
        mpeg1_bitrates[bitrate_index]
        if version == 0x03
        else mpeg2_bitrates[bitrate_index]
    )
    sample_rate = sample_rates[sample_rate_index]
    if version == 0x02:
        sample_rate //= 2
    elif version == 0x00:
        sample_rate //= 4

    padding = (value >> 9) & 0x01
    coefficient = 144000 if version == 0x03 else 72000
    frame_length = coefficient * bitrate // sample_rate + padding
    return bitrate, sample_rate, frame_length


def mp3_audio_start(wave_file, file_size):
    wave_file.seek(0)
    header = wave_file.read(10)
    if len(header) == 10 and header[:3] == b"ID3":
        size_bytes = header[6:10]
        if all(value < 0x80 for value in size_bytes):
            tag_size = (
                (size_bytes[0] << 21)
                | (size_bytes[1] << 14)
                | (size_bytes[2] << 7)
                | size_bytes[3]
            )
            footer_size = 10 if header[5] & 0x10 else 0
            return min(file_size, 10 + tag_size + footer_size)
    return 0


def find_mp3_frame(wave_file, start_offset, file_size):
    search_start = max(0, start_offset - 1024)
    search_end = min(file_size, start_offset + 1024 + 1448)
    wave_file.seek(search_start)
    data = wave_file.read(search_end - search_start)
    best_frame = None
    best_distance = None

    index = 0
    while index < len(data) - 3:
        index = data.find(b"\xff", index)
        if index < 0 or index + 4 > len(data):
            break

        info = mp3_frame_info(data[index : index + 4])
        if info is None:
            index += 1
            continue

        frame_offset = search_start + index
        bitrate, sample_rate, frame_length = info
        next_offset = frame_offset + frame_length
        next_index = index + frame_length
        if next_offset + 4 <= file_size:
            if next_index + 4 > len(data):
                index += 1
                continue
            if mp3_frame_info(data[next_index : next_index + 4]) is None:
                index += 1
                continue
        elif next_offset > file_size:
            index += 1
            continue
        distance = abs(frame_offset - start_offset)
        if best_distance is None or distance < best_distance:
            best_frame = (frame_offset, bitrate, sample_rate)
            best_distance = distance
        index += 1

    if best_frame is not None:
        return best_frame
    raise ValueError("Nie znaleziono ramki MP3 przy wybranej pozycji")


def mp3_header_duration(wave_file, start_offset, file_size):
    wave_file.seek(start_offset)
    header = wave_file.read(4)
    info = mp3_frame_info(header)
    if info is None:
        return None

    _, sample_rate, frame_length = info
    header_value = int.from_bytes(header, "big")
    version = (header_value >> 19) & 3
    samples_per_frame = 1152 if version == 3 else 576
    frame_end = start_offset + frame_length
    if frame_end > file_size:
        return None

    crc_size = 0 if header_value & (1 << 16) else 2
    channel_mode = (header_value >> 6) & 3
    if version == 3:
        side_info_size = 17 if channel_mode == 3 else 32
    else:
        side_info_size = 9 if channel_mode == 3 else 17
    xing_offset = start_offset + 4 + crc_size + side_info_size
    wave_file.seek(xing_offset)
    marker = wave_file.read(4)
    if marker in (b"Xing", b"Info"):
        flags_data = wave_file.read(4)
        if len(flags_data) == 4:
            flags = int.from_bytes(flags_data, "big")
            if flags & 1:
                frame_count_data = wave_file.read(4)
                if len(frame_count_data) == 4:
                    frame_count = int.from_bytes(frame_count_data, "big")
                    if frame_count:
                        return frame_count * samples_per_frame / sample_rate

    vbri_offset = start_offset + 36
    if vbri_offset + 18 <= frame_end:
        wave_file.seek(vbri_offset)
        if wave_file.read(4) == b"VBRI":
            wave_file.seek(vbri_offset + 14)
            frame_count_data = wave_file.read(4)
            if len(frame_count_data) == 4:
                frame_count = int.from_bytes(frame_count_data, "big")
                if frame_count:
                    return frame_count * samples_per_frame / sample_rate
    return None


def index_mp3_track(wave_file, start_offset, file_size):
    if file_size - start_offset < 4:
        raise ValueError("Nie można odczytać czasu trwania pliku MP3")
    sample_count = 16
    seek_index = []
    total_estimated_duration = 0.0
    previous_offset = start_offset
    previous_bitrate = None
    for sample_number in range(sample_count + 1):
        target_offset = start_offset + (
            (file_size - start_offset - 1) * sample_number // sample_count
        )
        frame_offset, bitrate, _ = find_mp3_frame(
            wave_file, target_offset, file_size
        )
        if sample_number == 0:
            frame_offset = start_offset
            previous_bitrate = bitrate
            seek_index.append((frame_offset, 0.0))
            continue
        if frame_offset <= previous_offset:
            continue

        average_seconds_per_byte = (
            1 / previous_bitrate + 1 / bitrate
        ) / 2
        segment_duration = (
            (frame_offset - previous_offset)
            * 8
            * average_seconds_per_byte
            / 1000
        )
        total_estimated_duration += segment_duration
        seek_index.append((frame_offset, total_estimated_duration))
        previous_offset = frame_offset
        previous_bitrate = bitrate

    header_duration = mp3_header_duration(wave_file, start_offset, file_size)
    if total_estimated_duration <= 0:
        if header_duration is None:
            raise ValueError("Nie można odczytać czasu trwania pliku MP3")
        return header_duration, [(start_offset, 0.0), (file_size - 4, header_duration)]

    if header_duration is not None:
        scale = header_duration / total_estimated_duration
        seek_index = [
            (offset, elapsed * scale) for offset, elapsed in seek_index
        ]
        total_estimated_duration = header_duration

    return total_estimated_duration, seek_index


def find_mp3_frame_at_time(wave_file, target_time, seek_index, file_size):
    previous_offset, previous_time = seek_index[0]
    next_offset, next_time = seek_index[-1]
    for indexed_offset, indexed_time in seek_index:
        if indexed_time >= target_time:
            next_offset = indexed_offset
            next_time = indexed_time
            break
        previous_offset = indexed_offset
        previous_time = indexed_time

    if next_time <= previous_time:
        target_offset = previous_offset
    else:
        fraction = (target_time - previous_time) / (next_time - previous_time)
        target_offset = previous_offset + int(
            (next_offset - previous_offset) * fraction
        )
    frame_offset, _, _ = find_mp3_frame(wave_file, target_offset, file_size)
    return frame_offset


def refresh_progress(preview_position=None):
    global last_progress_position

    if preview_position is not None:
        position = min(progress_width - 1, max(0, preview_position))
    elif current_file is not None and track_duration > 0:
        elapsed = min(track_duration, max(0, elapsed_time()))
        position = int(elapsed * (progress_width - 1) / track_duration)
    else:
        position = 0
    if position == last_progress_position:
        return False

    for x in range(progress_width):
        color = 1 if x <= position and current_file is not None else 0
        for y in range(progress_height):
            progress_bitmap[x, y] = color
    progress_knob.x = min(
        progress_left + progress_width - progress_knob_width,
        max(progress_left, progress_left + position - progress_knob_width // 2),
    )
    last_progress_position = position
    return True


def stop_track():
    global current_file, is_paused, track_started_at, pause_started_at
    global paused_seconds, last_elapsed, track_file_size, track_audio_start
    global track_duration, track_seek_index, playback_started
    global seek_mute_until, pending_seek_preroll, last_progress_position
    global decoder, crossfade_started_at, volume_ramp_started_at
    global active_voice

    if audio_mixer is not None:
        audio_mixer.voice[0].stop()
        audio_mixer.voice[1].stop()
        audio_mixer.voice[0].level = 0
        audio_mixer.voice[1].level = 0
    if is_paused:
        speaker_audio.stop()
    close_track_resources(current_file, decoder)
    current_file = None
    decoder = None
    clear_next_track()
    speaker_enable.value = True
    seek_mute_until = None
    pending_seek_preroll = 0
    crossfade_started_at = None
    volume_ramp_started_at = None
    active_voice = 0
    is_paused = False
    track_started_at = None
    pause_started_at = None
    paused_seconds = 0
    track_file_size = 0
    track_audio_start = 0
    track_duration = 0
    track_seek_index = []
    playback_started = False
    last_elapsed = -1
    last_progress_position = -1
    time_label.text = "00:00"
    control_labels[1].text = "PLAY"
    refresh_progress()
    display.refresh()


def scroll_playlist(direction):
    global list_offset

    maximum = max(0, len(tracks) - visible_rows)
    list_offset = min(maximum, max(0, list_offset + direction * visible_rows))
    refresh_playlist()


def play_track(index):
    global selected_track, current_file, decoder, is_paused
    global track_started_at, pause_started_at, paused_seconds, last_elapsed
    global list_offset, track_file_size, track_audio_start, track_duration
    global playback_started, track_seek_index
    global seek_mute_until, pending_seek_preroll
    global active_voice, crossfade_started_at, volume_ramp_started_at

    if not tracks:
        set_title("BRAK PLIKOW MP3 NA KARCIE SD")
        set_status("DODAJ MP3 DO KATALOGU SD")
        display.refresh()
        return False

    index %= len(tracks)
    stop_track()
    selected_track = index
    if selected_track < list_offset:
        list_offset = selected_track
    elif selected_track >= list_offset + visible_rows:
        list_offset = selected_track - visible_rows + 1
    refresh_playlist()

    new_file = None
    new_decoder = None
    try:
        (
            new_file,
            new_decoder,
            new_file_size,
            audio_start,
            new_track_duration,
            new_track_seek_index,
            _,
        ) = load_track(index)
        start_decoder_audio(new_decoder, active_voice, level=0)
    except (OSError, RuntimeError, ValueError, MemoryError) as error:
        if audio_mixer is not None:
            audio_mixer.voice[active_voice].stop()
            audio_mixer.voice[active_voice].level = 0
        if new_file is not None or new_decoder is not None:
            close_track_resources(new_file, new_decoder)
        path = "/sd/{}".format(tracks[index])
        print("MP3 playback error for {}: {}".format(path, error))
        set_title("BLAD MP3: {}".format(tracks[index]))
        set_status("SPRAWDZ PLIK")
        display.refresh()
        return False

    current_file = new_file
    decoder = new_decoder
    track_file_size = new_file_size
    track_audio_start = audio_start
    track_duration = new_track_duration
    track_seek_index = new_track_seek_index
    playback_started = True
    is_paused = False
    track_started_at = time.monotonic()
    volume_ramp_started_at = track_started_at
    crossfade_started_at = None
    pause_started_at = None
    paused_seconds = 0
    last_elapsed = -1
    control_labels[1].text = "PAUSE"
    set_title(tracks[index])
    set_status("ODTWARZANIE")
    time_label.text = "{}/{}".format("0:00", format_time(track_duration))
    refresh_progress()
    display.refresh()
    update_audio_levels(force=True)
    preload_next_track()
    return True


def seek_track(touch_x):
    global current_file, decoder, is_paused, track_started_at
    global track_file_size, pause_started_at, paused_seconds, last_elapsed
    global playback_started, seek_mute_until, pending_seek_preroll
    global last_progress_position
    global crossfade_started_at

    if current_file is None or selected_track is None or track_duration <= 0:
        return

    clear_next_track()
    crossfade_started_at = None
    seek_mute_until = None
    pending_seek_preroll = 0
    position = min(
        progress_width - 1, max(0, touch_x - progress_left)
    )
    fraction = position / (progress_width - 1)
    target_seconds = track_duration * fraction
    seek_preroll = min(target_seconds, 0.35)
    seek_start_time = target_seconds - seek_preroll
    path = "/sd/{}".format(tracks[selected_track])
    was_paused = is_paused
    was_playing = (
        audio_mixer is not None and audio_mixer.voice[active_voice].playing
    )
    seek_pause_started_at = None
    if was_playing:
        speaker_audio.pause()
        seek_pause_started_at = time.monotonic()

    new_file = None
    try:
        new_file = open(path, "rb")
        new_file.seek(0, 2)
        new_file_size = new_file.tell()
        frame_offset = find_mp3_frame_at_time(
            new_file, seek_start_time, track_seek_index, new_file_size
        )
        new_file.seek(frame_offset)
    except (OSError, ValueError) as error:
        if new_file is not None:
            new_file.close()
        print("MP3 seek error for {}: {}".format(path, error))
        if was_playing:
            speaker_audio.resume()
            paused_seconds += time.monotonic() - seek_pause_started_at
        set_status("BLAD PRZEWIJANIA")
        refresh_progress()
        display.refresh()
        return

    previous_file = current_file
    if audio_mixer is not None:
        audio_mixer.voice[0].stop()
        audio_mixer.voice[1].stop()
        audio_mixer.voice[0].level = 0
        audio_mixer.voice[1].level = 0

    try:
        decoder.file = new_file
        start_decoder_audio(decoder, active_voice, level=0)
        if was_paused:
            speaker_audio.pause()
    except (OSError, RuntimeError, ValueError) as error:
        new_file.close()
        print("MP3 seek playback error for {}: {}".format(path, error))
        try:
            decoder.file = previous_file
            start_decoder_audio(decoder, active_voice, level=0)
            if was_paused:
                speaker_audio.pause()
            elif was_playing:
                paused_seconds += time.monotonic() - seek_pause_started_at
        except (OSError, RuntimeError, ValueError) as restore_error:
            print("MP3 playback restore error: {}".format(restore_error))
            stop_track()
        set_status("BLAD PRZEWIJANIA")
        refresh_progress()
        display.refresh()
        return

    previous_file.close()
    current_file = new_file
    track_file_size = new_file_size
    playback_started = False
    now = time.monotonic()
    track_started_at = now - seek_start_time
    paused_seconds = 0
    pause_started_at = now if was_paused else None
    is_paused = was_paused
    if was_paused:
        pending_seek_preroll = seek_preroll
    elif seek_preroll > 0:
        seek_mute_until = now + seek_preroll
    else:
        update_audio_levels(force=True)
    last_elapsed = -1
    last_progress_position = -1
    time_label.text = "{}/{}".format(
        format_time(target_seconds), format_time(track_duration)
    )
    set_status("PAUZA" if was_paused else "ODTWARZANIE")
    refresh_progress()
    display.refresh()
    preload_next_track()


def toggle_pause():
    global is_paused, pause_started_at, paused_seconds
    global seek_mute_until, pending_seek_preroll
    global crossfade_started_at, volume_ramp_started_at

    if selected_track is None:
        if tracks:
            play_track(0)
        return

    if is_paused:
        speaker_audio.resume()
        now = time.monotonic()
        paused_for = now - pause_started_at
        paused_seconds += paused_for
        if crossfade_started_at is not None:
            crossfade_started_at += paused_for
        if volume_ramp_started_at is not None:
            volume_ramp_started_at += paused_for
        pause_started_at = None
        is_paused = False
        if pending_seek_preroll > 0:
            seek_mute_until = now + pending_seek_preroll
            pending_seek_preroll = 0
        update_audio_levels(force=True)
        control_labels[1].text = "PAUSE"
        set_status("ODTWARZANIE")
    elif audio_mixer is not None and (
        audio_mixer.voice[0].playing or audio_mixer.voice[1].playing
    ):
        speaker_audio.pause()
        pause_started_at = time.monotonic()
        is_paused = True
        if seek_mute_until is not None:
            pending_seek_preroll = max(
                0, seek_mute_until - pause_started_at
            )
            seek_mute_until = None
            update_audio_levels(force=True)
        control_labels[1].text = "PLAY"
        set_status("PAUZA")
    else:
        play_track(selected_track)
        return
    display.refresh()


def handle_touch(x, y):
    if list_top <= y < list_top + visible_rows * row_height:
        if x >= display.width - 36:
            if y < list_top + 26:
                scroll_playlist(-1)
            elif y >= down_y:
                scroll_playlist(1)
            return

        row_index = (y - list_top) // row_height
        track_index = list_offset + row_index
        if track_index < len(tracks):
            play_track(track_index)
        return

    if controls_y <= y < controls_y + control_height:
        control_index = (x - controls_left) // (control_width + control_gap)
        if 0 <= control_index < len(control_names):
            button_left = controls_left + control_index * (
                control_width + control_gap
            )
            if button_left <= x < button_left + control_width:
                if control_index == 0 and tracks:
                    play_track(
                        selected_track - 1 if selected_track is not None else 0
                    )
                elif control_index == 1:
                    toggle_pause()
                elif control_index == 2 and tracks:
                    play_track(
                        selected_track + 1 if selected_track is not None else 0
                    )
                elif control_index == 3:
                    stop_track()
                    set_status("STOP")
                    display.refresh()


if sd_error is not None:
    set_title("BLAD KARTY SD")
    set_status(sd_error)
elif not tracks:
    set_title("BRAK PLIKOW MP3 NA KARCIE SD")
    set_status("DODAJ MP3 DO KATALOGU SD")
else:
    set_title("WYBIERZ UTWOR Z LISTY")
    set_status("GOTOWY")

refresh_playlist()
refresh_volume_control()
display.refresh()

was_touched = False
progress_dragging = False
progress_drag_x = None
volume_dragging = False
while True:
    point = touchscreen.touch_point
    touched = point is not None
    if touched:
        touch_x, touch_y, _ = point
        in_volume_area = (
            volume_left - 8 <= touch_x <= volume_left + volume_width + 8
            and volume_top - 6
            <= touch_y
            <= volume_top + volume_height + 6
        )
        if volume_dragging or in_volume_area:
            volume_dragging = True
            if set_volume_from_touch(touch_x):
                display.refresh()
        else:
            in_progress_area = (
                progress_left - 8
                <= touch_x
                <= progress_left + progress_width + 8
                and progress_top - 6
                <= touch_y
                <= progress_top + progress_height + 8
            )
            if progress_dragging or in_progress_area:
                progress_dragging = True
                progress_drag_x = touch_x
                if current_file is not None:
                    preview_position = min(
                        progress_width - 1,
                        max(0, touch_x - progress_left),
                    )
                    if refresh_progress(preview_position):
                        display.refresh()
            elif not was_touched:
                handle_touch(touch_x, touch_y)
    elif progress_dragging:
        seek_track(progress_drag_x)
        progress_dragging = False
        progress_drag_x = None
    elif volume_dragging:
        volume_dragging = False
    was_touched = touched

    if selected_track is not None and not is_paused and current_file is not None:
        now = time.monotonic()
        update_audio_levels()
        if crossfade_started_at is not None:
            if now - crossfade_started_at >= CROSSFADE_SECONDS:
                finish_crossfade()
        elif audio_mixer is not None and audio_mixer.voice[active_voice].playing:
            playback_started = True
            if track_duration - elapsed_time() <= CROSSFADE_SECONDS:
                if next_decoder is None or next_track_format != audio_mixer_format:
                    set_status("BEZ NAKLADANIA")
                else:
                    start_crossfade()
        elif playback_started:
            next_track = (selected_track + 1) % len(tracks)
            if len(tracks) > 1:
                play_track(next_track)
            else:
                stop_track()
                set_status("KONIEC")
                display.refresh()

    if seek_mute_until is not None and time.monotonic() >= seek_mute_until:
        seek_mute_until = None
        update_audio_levels(force=True)

    if (
        track_started_at is not None
        and time.monotonic() - last_status_update >= DISPLAY_UPDATE_INTERVAL
    ):
        elapsed = int(elapsed_time())
        display_changed = False
        if not progress_dragging:
            display_changed = refresh_progress()
        if elapsed != last_elapsed:
            time_label.text = "{}/{}".format(
                format_time(elapsed), format_time(track_duration)
            )
            last_elapsed = elapsed
            display_changed = True
        if display_changed:
            display.refresh()
        last_status_update = time.monotonic()

    time.sleep(0.01)
