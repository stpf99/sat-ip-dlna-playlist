import sys
import os
import requests  # Use the requests library for downloading files
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


def merge_files(output_filename, languages):
    """
    Merges only downloaded PHP files for specified languages into a single PHP file for processing.
    """
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
    channel_counter = 1  # Numeracja startowa

    with open(input_filename, "r", encoding="utf-8") as infile:
        for line in infile:
            # Zamień <pol>V</pol> na <pol>v</pol> i <pol>H</pol> na <pol>h</pol>
            line = re.sub(r"<pol>V</pol>", "<pol>v</pol>", line)
            line = re.sub(r"<pol>H</pol>", "<pol>h</pol>", line)

            # Pomijaj kanały bez nazw
            if '<name></name>' in line:
                continue

            # Pobieranie nazwy kanału
            name_match = re.search(r"<name>(.*?)</name>", line)
            if name_match:
                channel_name = name_match.group(1).strip()
                # Pomijaj kanały, jeśli ich nazwa znajduje się na liście `omit_list`
                if channel_name in omit_list:
                    continue
            else:
                continue  # Pomijaj, jeśli kanał nie ma nazwy

            # Sprawdź, czy to kanał radiowy, czy telewizyjny
            if '<type>radio</type>' in line:
                # Dodaj numer kanału do kanału radiowego i dodaj do listy radiowej
                line = line.replace("NR", str(channel_counter))
                radio_channels.append(line)
            else:
                # Dodaj numer kanału do kanału TV i dodaj do listy TV
                line = line.replace("NR", str(channel_counter))
                tv_channels.append(line)
            channel_counter += 1  # Inkrementuj licznik po każdym kanale

    # Zapisz do pliku, kanały TV przed radiowymi
    with open(output_filename, "w", encoding="utf-8") as outfile:
        for channel in tv_channels + radio_channels:  # TV najpierw, potem radio
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

    # Pobieramy argumenty
    position = sys.argv[1]
    source = sys.argv[2]
    languages = [arg for arg in sys.argv[3:] if not arg.startswith("--")]

    # Sprawdzenie, czy `--omit` zostało podane
    omit_list = []
    if "--omit" in sys.argv:
        omit_index = sys.argv.index("--omit") + 1
        if omit_index < len(sys.argv):
            omit_list = sys.argv[omit_index].split(",")

    # Nazwy plików wyjściowych
    merged_filename = f"tv-{position}-fta-langs.php"
    intermediate_xml_filename = f"tv-{position}-fta-langs.xml"
    final_output_filename = f"TV-{position}-FTA-langs-{'-'.join(languages)}.xml"

    # Główna logika
    cleanup_files()  # Cleanup old files
    download_files(position, languages)  # Download only specified languages
    merge_files(merged_filename, languages)  # Merge only files for specified languages
    process_file_with_script(merged_filename, intermediate_xml_filename, source)  # Process the merged file
    post_process_xml(intermediate_xml_filename, final_output_filename, omit_list)  # Post-process the XML
    finalize_xml(final_output_filename)  # Add XML header and footer

    # Przeniesienie finalnego pliku do katalogu wynikowego
    output_dir = "ONEPOSMULTILANG/"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    os.rename(final_output_filename, os.path.join(output_dir, final_output_filename))
    print(f"Final XML saved to {output_dir}{final_output_filename}")

    # Cleanup intermediate files
    cleanup_files()
    print("Cleanup completed.")

if __name__ == "__main__":
    main()
