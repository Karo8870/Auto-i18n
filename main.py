import google.api_core.exceptions
import google.generativeai as genai
from dotenv import load_dotenv
from os import getenv, mkdir
from os.path import exists
from time import time, sleep
from colorama import Fore
from re import sub, findall
from concurrent.futures import ThreadPoolExecutor, as_completed

TEMPLATE_FILE_NAME = 'template.po.template'
OUTPUT_DIRECTORY = 'templates'

MAX_THREADS = 5

load_dotenv()
genai.configure(api_key=getenv('GEMINI_API_KEY'))

languages = ['af', 'sq', 'ar', 'az', 'be', 'bn', 'bg', 'zh']


class POTemplate:
    def __init__(self, text):
        self.original = text
        self.optimized = sub(r'#[^\n]*\n', '', text)
        self.optimized = sub(r'\n{3,}', '\n\n', self.optimized)
        self.translations = set(findall(r'msgid\s*"((?:[^"\\]|\\.)*)"', self.optimized))


def generate_from_list(items: list[str]):
    return '\n\n'.join([f'msgid "{item}"\nmsgstr ""' for item in items])


def init():
    if not exists(OUTPUT_DIRECTORY):
        print(Fore.YELLOW + f'{OUTPUT_DIRECTORY} directory not found, creating it' + Fore.RESET)
        mkdir(OUTPUT_DIRECTORY)

    try:
        with open(TEMPLATE_FILE_NAME, 'r') as file:
            return file.read()

    except FileNotFoundError:
        raise FileNotFoundError(
            Fore.RED +
            'Template file (template.po.template) not found. You must add a template file for translations'
            + Fore.RESET
        )


def translate(template: POTemplate, language, model, start_time):
    if not exists(f'{OUTPUT_DIRECTORY}/{language}/messages.po'):
        start_time_lang = time()

        lang_template = template.optimized.replace('{{{language}}}', language)

        while True:
            try:
                response = model.generate_content(
                    f'Complete the translations from msgstr in the language with the code {language}:\n\n' + lang_template
                )

                break

            except google.api_core.exceptions.ResourceExhausted as exc:
                print(exc)

            sleep(2)

        mkdir(f'{OUTPUT_DIRECTORY}/{language}')

        with open(f'{OUTPUT_DIRECTORY}/{language}/messages.po', 'w', encoding='utf-8') as file:
            file.write(response.candidates[0].content.parts[0].text)

        print(f'Language {language} completed in {"{:.2f}".format(time() - start_time_lang, 2)} seconds')

    else:
        print('Language already exists')
        # print(f'Language {language} already exists, checking similarity')
        #
        # with open(f'{OUTPUT_DIRECTORY}/{language}/messages.po', 'r', encoding='utf-8') as file:
        #     text = file.read()
        #
        # lang_template = POTemplate(text)
        #
        # dif = list(template.translations - lang_template.translations)
        #
        # if len(dif) > 0:
        #     additions = generate_from_list(dif)
        #
        #     response = model.generate_content(
        #         f'Edit this by Completing the translations from msgstr in the language with the code {language}:\n\n' + additions
        #     )
        #
        #     with open(f'{OUTPUT_DIRECTORY}/{language}/messages.po', 'a', encoding='utf-8') as file:
        #         file.write('\n\n' + response.candidates[0].content.parts[0].text)


def main():
    template = init()

    base_template = POTemplate(template)

    model = genai.GenerativeModel('gemini-1.5-pro')

    start_time = time()

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_language = {
            executor.submit(translate, base_template, language, model, start_time): language
            for language in languages
        }

        for future in as_completed(future_to_language):
            language = future_to_language[future]

            try:
                future.result()
                print(f"Translation for {language} completed successfully.")
            except Exception as exc:
                raise exc

    print(f'Finished in {"{:.2f}".format(time() - start_time, 2)} seconds')


if __name__ == '__main__':
    try:
        main()

    except Exception as e:
        raise e
