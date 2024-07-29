import google.generativeai as genai
from dotenv import load_dotenv
from os import getenv, mkdir
from os.path import exists
from time import time

load_dotenv()
genai.configure(api_key=getenv('GEMINI_API_KEY'))

languages = ['af', 'sq', 'ar', 'az', 'be', 'bn', 'bs', 'bg', 'zh', 'co', 'hr', 'cs', 'da', 'nl', 'et', 'fi', 'ka', 'el',
			 'he', 'hi', 'is', 'id', 'ga', 'ja', 'ko', 'la', 'lt', 'mk', 'ms', 'mn', 'ne', 'no', 'pl', 'pt', 'ru', 'sr',
			 'sl', 'sv', 'th', 'tr', 'uk', 'vi']

if __name__ == '__main__':
	if not exists('templates'):
		mkdir('templates')

	with open('template.po.template', 'r') as file:
		template = file.read()

	model = genai.GenerativeModel('gemini-1.5-pro')

	start_time = time()

	for language in languages:
		if not exists(f'templates/{language}'):
			start_time_lang = time()

			lang_template = template.replace('{{{language}}}', language)

			response = model.generate_content(
				f'Complete the translations from msgstr in the language with the code {language}:\n\n' + lang_template
			)

			mkdir(f'templates/{language}')

			with open(f'templates/{language}/messages.po', 'w', encoding='utf-8') as file:
				file.write(response.candidates[0].content.parts[0].text)

			print(f'Language {language} completed in {"{:.2f}".format(time() - start_time_lang, 2)} seconds')

		else:
			print(f'Language {language} already exists')

	print(f'Finished in {"{:.2f}".format(time() - start_time, 2)}')
