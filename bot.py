import os
import subprocess
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters

BOT_TOKEN = ''  #enter your telegran bot token here
ALLOWED_USER_IDS = []  #allowed telegram userids to intract with the bot

added_subtitle_name = 'sub2'  #this will show as the name for the new subtitle added in the player
added_subtitle_language = 'eng'  #this will show as the language for the new subtitle added in the player

path_start = '' #start of the path to not repeat it every time in the input (leave empty if dont want to use it)

CHOOSING, FOLDERS, FILES, SUBTITLE_FOLDER, SUBTITLE_FILE = range(5)

def start(update, context):
    user_id = update.message.from_user.id
    if user_id not in ALLOWED_USER_IDS:
        update.message.reply_text("You are not authorized to use this bot.")
        return ConversationHandler.END

    update.message.reply_text(
        "Welcome Subtitle Muxer Bot!\n\n"
        "Do you want to merge folders or files?\n"
        "Please choose one option:\n"
        "- /folders: Merge folders\n"
        "- /files: Merge files"
    )
    return CHOOSING

def choose_folders(update, context):
    update.message.reply_text("You chose to merge folders.\n\nPlease provide the path to the video folder:")
    return FOLDERS

def choose_files(update, context):
    update.message.reply_text("You chose to merge files.\n\nPlease provide the path to the video file:")
    return FILES

def folders(update, context):
    video_folder_path = update.message.text.strip()

    context.user_data['video_folder_path'] = video_folder_path

    update.message.reply_text("Video folder path received. Now, please provide the path to the subtitle folder:")
    return SUBTITLE_FOLDER

def files(update, context):
    video_file_path = update.message.text.strip()

    context.user_data['video_file_path'] = video_file_path

    update.message.reply_text("Video file path received. Now, please provide the path to the subtitle file:")
    return SUBTITLE_FILE

def subtitle_folder(update, context):
    subtitle_folder_path = update.message.text.strip()

    context.user_data['subtitle_folder_path'] = subtitle_folder_path

    update.message.reply_text("Subtitle folder path received. Starting the merging process...")

    try:
        merge_folders(context.user_data['video_folder_path'], context.user_data['subtitle_folder_path'])
        update.message.reply_text("Subtitle merging completed!")
    except Exception as e:
        update.message.reply_text(f"An error occurred while merging subtitles: {str(e)}")

    return ConversationHandler.END

def subtitle_file(update, context):
    subtitle_file_path = update.message.text.strip()

    context.user_data['subtitle_file_path'] = subtitle_file_path

    update.message.reply_text("Subtitle file path received. Starting the merging process...")

    try:
        merge_files(context.user_data['video_file_path'], context.user_data['subtitle_file_path'])
        update.message.reply_text("Subtitle merging completed!")
    except Exception as e:
        update.message.reply_text(f"An error occurred while merging subtitles: {str(e)}")

    return ConversationHandler.END

def merge_folders(video_folder, subtitle_folder):
    video_folder = path_start + video_folder
    subtitle_folder = path_start + subtitle_folder

    video_files = sorted([file for file in os.listdir(video_folder) if file.endswith('.mkv')])
    subtitle_files = sorted([file for file in os.listdir(subtitle_folder) if file.endswith('.srt') or file.endswith('.ass')])

    if len(video_files) != len(subtitle_files):
        raise Exception("Number of video files and subtitle files do not match.")

    for video_file, subtitle_file in zip(video_files, subtitle_files):
        try:
            merge_files(os.path.join(video_folder, video_file), os.path.join(subtitle_folder, subtitle_file))
        except Exception as e:
            raise Exception(f"Error merging {video_file} with {subtitle_file}: {str(e)}")


def merge_files(video_file, subtitle_file):
    video_file = path_start + video_file
    subtitle_file = path_start + subtitle_file

    output_file = os.path.join(os.path.dirname(video_file), 'output.mkv')

    video_file = os.path.abspath(video_file)
    subtitle_file = os.path.abspath(subtitle_file)

    command = [
        'ffmpeg', '-hide_banner',
        '-i', video_file,
        '-i', subtitle_file,
        '-map','1:0','-map','0',
        '-disposition:s:0', 'default',
        '-c:v', 'copy',
        '-c:a', 'copy',
        '-c:s', 'ass',
        '-metadata:s:s:0', f"title='added_subtitle_name'",
        '-metadata:s:s:0', f"language='added_subtitle_name'",
        '-y', output_file
    ]

    try:
        subprocess.run(command, check=True)
        os.replace(output_file, video_file)
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg encountered an error: {e}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                CommandHandler('folders', choose_folders),
                CommandHandler('files', choose_files),
            ],
            FOLDERS: [MessageHandler(Filters.text, folders)],
            FILES: [MessageHandler(Filters.text, files)],
            SUBTITLE_FOLDER: [MessageHandler(Filters.text, subtitle_folder)],
            SUBTITLE_FILE: [MessageHandler(Filters.text, subtitle_file)],
        },
        fallbacks=[],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
