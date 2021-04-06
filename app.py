from avito_parser import AvitoParser
from avito_parser import IPBlockedError
from avito_parser import compareItemsForUpdate
import time
import argparse
import os
import sys
import socks
import socket

start_time = time.time()

#ARGUMENTS
parser = argparse.ArgumentParser()

parser.add_argument("--region", help = "region URL for avito", default='krasnoyarskiy_kray')
parser.add_argument("--category", help='category URL for avito', default='False')
parser.add_argument("--query", help='query for avito', default='')
parser.add_argument("--output", help = "Path of the output directory", default='output')
parser.add_argument("--cmd", help = "get_items_urls OR scrap OR update_items OR scrap_update OR clean_table", default='scrap')
parser.add_argument("--urls_file", help = "need for scrap after use get_items_url", default='items_urls.txt')
parser.add_argument("--proxy", help = "proxy", default='no')
parser.add_argument("--csv_file", help = "for clean_table", default='default.csv')

#BODY
args = parser.parse_args()
if args.cmd == 'scrap' or args.cmd == 'scrap_update':
    avitoParser = AvitoParser(args.proxy)
    pages = []
    save_descriptor = args.urls_file.split('.')[0].split('items_urls_')[1].split('_upd')[0]
    print('[INF] Reading URLs file...')
    try:
        f = open(args.urls_file, 'r')
        for line in f:
            print(line)
            pages.append(line)
    except Exception as e:
        print('[ERR] Url items file "' + args.urls_file + '" reading failed: ' + str(e))
    old_pages = []
    if args.cmd == 'scrap_update':
        try:
            avito_file = args.output + '/avito_' + save_descriptor + '.csv'
            print(avito_file)
            f = open(avito_file, 'r', errors='ignore')
            for line in f:
                url = line.split(';')[-1]
                if url == 'URL':
                    continue
                old_pages.append(url)
            new_pages = compareItemsForUpdate(old_pages, pages)
            pages = new_pages
            f.close()
        except Exception as e:
            print('[ERR] Update file read failed "' + 'avito_' + save_descriptor + '.csv": ' + str(e))
            sys.exit()
    for page in pages:
        counter = 0
        try:
            t0 = time.time()
            counter = counter + 1
            print('[INF] Reading page: ' + page)
            avitoParser.readPage(page)
            print('[INF] Scrapping...')
            category = page.split('/')[-2]
            if category == 'avtomobili':
                category = 1
            elif category == 'zapchasti_i_aksessuary':
                category = 2
            else:
                category = 1
            output = avitoParser.parseHtml(category)
            if '\n' in page:
                page = page.replace('\n', '')
            if '"' in page:
                page = page.replace('"', '')
            output.append(page)
            avitoParser.data.append(output)
            print('[INF] Processing "' + page + '" time: ' + str(time.time() - t0) + ' seconds\n')
            if time.time() - t0 < 5:
                print('[INF] Sleeping 5 sec to avoid IP address block')
                time.sleep(5)
            if counter >= 100:
                try:
                    avitoParser.driver.delete_all_cookies()
                    counter = 0
                    print('[INF] 100 URLs parsed. Deleting all cookies.')
                except Exception as e:
                    counter = 0
                    print('[WRN] Error during deleting cookies occured: ' + str(e))
        except KeyboardInterrupt:
            print('[INF] Keyboard interruption. Saving data.')
            break
        except IPBlockedError as IBE:
            print('[ERR] ' + str(IBE))
            if args.cmd == 'scrap':
                avitoParser.outputInCsv(args.output, save_descriptor)
            elif args.cmd == 'scrap_update':
                avitoParser.updateCsv(args.output, save_descriptor)
            sys.exit(0)
        except Exception as e:
            print('[ERR] Scrapping error: ' + str(e))
            if str(e) == 'Message: Tried to run command without establishing a connection\n':
                if args.cmd == 'scrap':
                    avitoParser.outputInCsv(args.output, save_descriptor)
                elif args.cmd == 'scrap_update':
                    avitoParser.updateCsv(args.output, save_descriptor)
                print('[ERR] Driver closed. Closing app...')
                sys.exit()
            time.sleep(3)
            continue
    avitoParser.printTable()
    if args.cmd == 'scrap':
        avitoParser.outputInCsv(args.output, save_descriptor)
    elif args.cmd == 'scrap_update':
        avitoParser.updateCsv(args.output, save_descriptor)
elif args.cmd == 'get_items_urls' or args.cmd == 'update_items':
    base_url = 'https://www.avito.ru'
    url = base_url
    save_descriptor = 'items_urls'
    if args.category == 'False' and args.query == '':
        print('[ERR] Not enough data. Need category or query or both.')
        sys.exit()
    elif args.category != 'False' and args.query == '':
        url = url + '/' + args.region + '/' + args.category
        save_descriptor = save_descriptor + '_' + args.region + '_' + args.category
    elif args.category == 'False':
        url = url + '/' + args.region + '?q=' + args.query
        save_descriptor = save_descriptor + '_' + args.region + '_' + args.query
    else:
        url = url + '/' + args.region + '/' + args.category + '?q=' + args.query
        save_descriptor = save_descriptor + '_' + args.region + '_' + args.category + '_' + args.query
    print('[INF] Scrapping URL: ' + url)
    avitoParser = AvitoParser(args.proxy)
    pages = []
    try:
        pages = avitoParser.getPages(url)
    except Exception as e:
        print('[ERR] Getting items pages failed: ' + str(e))
        sys.exit()
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    old_save_descriptor = save_descriptor + '.txt'
    upd_save_descriptor = save_descriptor + '_upd_' + str(time.time()).split('.')[1] + '.txt'
    print('[INF] Saving items urls in file: ' + args.output + '/' + save_descriptor)
    if args.cmd == 'get_items_urls':
        f = open(args.output + '/' + old_save_descriptor, 'w')
        for page in pages:
            f.write(page + '\n')
        f.close()
    elif args.cmd == 'update_items':
        if os.path.exists(args.output + '/' + old_save_descriptor):
            f = open(args.output + '/' + old_save_descriptor, 'r')
            old_pages = f.read().splitlines()
            new_pages = compareItemsForUpdate(old_pages, pages)
            f.close()
            f = open(args.output + '/' + old_save_descriptor, 'a')
            upd_f = open(args.output + '/' + upd_save_descriptor, 'w')
            for new_page in new_pages:
                f.write(new_page + '\n')
                upd_f.write(new_page + '\n')
        else:
            print('[WRN] Old items not found. Creating new items file...')
            f = open(args.output + '/' + old_save_descriptor, 'w')
            for page in pages:
                f.write(page + '\n')
            f.close()
elif args.cmd == 'clean_table':
    try:
        avitoParser = AvitoParser(args.proxy)
        avitoParser.loadDataFromCsv(args.csv_file)
        avitoParser.cleanTableFromTrash()
        avitoParser.outputInCsv(args.output, 'cleaned_' + str(time.time()).split('.')[0])
    except Exception as e:
        print('[ERR] Clean table err: ' + str(e))
        sys.exit()
else:
    print('[ERR] Wrong command. Available commands: "get_items_urls" or "scrap" or "update_items"')
print('[OK] Scrapping finished successfuly.')
print('[INF] Time: ' + str(time.time() - start_time) + ' seconds')
sys.exit()
