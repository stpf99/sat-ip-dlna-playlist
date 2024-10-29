# king2xml.py
import sys
import os
import requests
import re

def download_files(position, languages):
    """
    Downloads the channel data files for the specified position and languages.
    """
    for lang in languages:
        url = f"https://de.kingofsat.net/freqs.php?&pos={position}&standard=All&ordre=freq&filtre=Clear&cl={lang}"
        response = requests.get(url)
        if response.status_code == 200:
            with open(f"freqs_{lang}.php", "w", encoding="utf-8") as file:
                file.write(response.text)
            print(f"Downloaded data for language {lang} successfully.")
        else:
            print(f"Failed to download data for language {lang}. Status code: {response.status_code}")

def cleanup_files():
    """
    Removes old files matching specific patterns.
    """
    for filename in os.listdir():
        if filename.endswith(".php") or filename.endswith(".xml") or filename.startswith("freq"):
            os.remove(filename)

def merge_files(output_filename, languages, omit_list=[]):
    """
    Merges downloaded PHP files for specified languages into a single PHP file.
    Also creates a map of channel names to their languages, excluding omitted channels.
    """
    channel_languages = {}  # Dictionary to store channel name -> languages mapping

    # First pass: collect channel names and their languages
    for lang in languages:
        filename = f"freqs_{lang}.php"
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as infile:
                for line in infile:
                    if "title=\"Id:" in line:
                        channel_name = line.split(':', 1)[1].lstrip().split('"', 1)[0]
                        # Skip channels that are in the omit list
                        if channel_name not in omit_list:
                            if channel_name in channel_languages:
                                if lang not in channel_languages[channel_name]:
                                    channel_languages[channel_name].append(lang)
                            else:
                                channel_languages[channel_name] = [lang]

    # Save channel-language mapping
    with open("channel_languages.txt", "w", encoding="utf-8") as mapfile:
        for channel, langs in channel_languages.items():
            mapfile.write(f"{channel}|||{'|'.join(langs)}\n")

    # Second pass: merge files
    with open(output_filename, "w", encoding="utf-8") as outfile:
        for lang in languages:
            filename = f"freqs_{lang}.php"
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())

    print(f"Merged specified language files into {output_filename}.")

def process_file_with_script(input_filename, output_filename, source):
    """
    Calls the getchannels.py script to process the merged PHP file.
    """
    os.system(f"python getchannels.py newslave {input_filename} {source}")

def post_process_xml(input_filename, output_filename, omit_list=[]):
    tv_channels = []
    radio_channels = []
    channel_counter = 1

    # Load channel-language mapping
    channel_languages = {}
    if os.path.exists("channel_languages.txt"):
        with open("channel_languages.txt", "r", encoding="utf-8") as mapfile:
            for line in mapfile:
                channel, langs = line.strip().split("|||")
                channel_languages[channel] = langs.split("|")

    with open(input_filename, "r", encoding="utf-8") as infile:
        for line in infile:
            # Standardize polarization
            line = re.sub(r"<pol>V</pol>", "<pol>v</pol>", line)
            line = re.sub(r"<pol>H</pol>", "<pol>h</pol>", line)

            # Skip channels without names
            if '<name></name>' in line:
                continue

            # Get channel name
            name_match = re.search(r"<name>(.*?)</name>", line)
            if name_match:
                channel_name = name_match.group(1).strip()
                if channel_name in omit_list:
                    continue

                # Format channel number
                formatted_number = f"{channel_counter:04d}"

                # Get languages for this channel
                langs = channel_languages.get(channel_name, [])
                lang_str = f"[{','.join(langs)}] " if langs else ""

                # Create new channel name with number and languages
                new_name = f"{formatted_number} {lang_str}{channel_name}"

                # Update both the channel name and number attribute
                line = re.sub(r"<name>.*?</name>", f"<name>{new_name}</name>", line)
                line = re.sub(r'number="NR"', f'number="{channel_counter}"', line)

                # Add to appropriate list
                if '<type>radio</type>' in line:
                    radio_channels.append(line)
                else:
                    tv_channels.append(line)

                channel_counter += 1

    # Write processed channels to file
    with open(output_filename, "w", encoding="utf-8") as outfile:
        for channel in tv_channels + radio_channels:
            outfile.write(channel)

def finalize_xml(output_filename):
    """
    Finalizes the XML output by adding the starting and ending tags.
    """
    STR2 = '<?xml version="1.0" encoding="UTF-8"?><channelTable msys="DVB-S">'
    STR3 = '</channelTable>'

    with open(output_filename, "r", encoding="utf-8") as infile:
        content = infile.read()

    with open(output_filename, "w", encoding="utf-8") as outfile:
        outfile.write(STR2 + "\n" + content + "\n" + STR3)

    print(f"Final XML structure prepared in {output_filename}.")

def main():
    if len(sys.argv) < 4:
        print("Usage: python king2xml.py <position> <source> <lang1> <lang2> ... [--omit <name1,name2,...>]")
        sys.exit(1)

    position = sys.argv[1]
    source = sys.argv[2]

    # Oddziel języki od parametrów --omit
    languages = []
    omit_list = []
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--omit":
            if i + 1 < len(sys.argv):
                omit_list = sys.argv[i + 1].split(",")
                break
            else:
                print("Error: --omit requires a list of channels")
                sys.exit(1)
        else:
            languages.append(sys.argv[i])
        i += 1

    merged_filename = f"tv-{position}-fta-langs.php"
    intermediate_xml_filename = f"tv-{position}-fta-langs.xml"
    final_output_filename = f"TV-{position}-FTA-langs-{'-'.join(languages)}.xml"

    cleanup_files()
    download_files(position, languages)
    merge_files(merged_filename, languages, omit_list)
    process_file_with_script(merged_filename, intermediate_xml_filename, source)
    post_process_xml(intermediate_xml_filename, final_output_filename, omit_list)
    finalize_xml(final_output_filename)

    output_dir = "ONEPOSMULTILANG/"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    os.rename(final_output_filename, os.path.join(output_dir, final_output_filename))
    print(f"Final XML saved to {output_dir}{final_output_filename}")

    cleanup_files()
    print("Cleanup completed.")

if __name__ == "__main__":
    main()
