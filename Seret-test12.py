"""parsing www.seret.co.il and create an html file containing recommended movies
"""
import re
import os
import webbrowser
import requests
from bs4 import BeautifulSoup
import seret_dialog

CITIES_OK = ['הרצליה', 'חולון', 'סביון', 'פתח-תקווה', 'קריית-אונו', 'ראשון לציון',
             'רמת-גן/גבעתיים', 'רמת-השרון', 'רעננה', 'תל-אביב/יפו']
GENRES_NOK = {'ישראלי', 'ילדים', 'אימה', 'אנימציה', 'תיעודי'}
RESULTS_HEADER = '''
    <head>\n
        <title>סרטים מומלצים</title>
        <meta http-equiv="Content-Type" content="text/html; charset=windows-1255">
        <meta http-equiv="Content-language" content ="he">
        <style>body{direction:rtl}</style>\n
    </head>\n
    <body>\n'''
RESULTS_FOOTER = '<br><br>\n</body>\n</html>'
RESULTS_FORMAT_ATTRIB = '<span style="float:right;width:{}px;"><strong>{}</strong></span>'' \
''<span style="float:right">{}</span><br>'
MOVIES_SITE_URL = 'http://www.seret.co.il/movies/'


def get_parsed_url(url, dump_file, from_file):
    """get an html and return a parsed soup
    html can be retrieved either from url or from a file
     it is also possible to retrieve an html from url and store it in a file
     Args:
         url (str)
         dump_file (str) full path
         from_file (bool)
     Returns:
         souped_html
    """
    dump_file_exists = os.path.exists(dump_file)
    if from_file and dump_file_exists:
        fhandle = open(dump_file, "r")
        html_page = fhandle.read()
        fhandle.close()
    else:
        html_page = requests.get(url).content.decode('windows-1255')
    if from_file and not dump_file_exists:
        fhandle = open(dump_file, "w")
        fhandle.write(html_page)
        fhandle.close()
    souped_html = BeautifulSoup(html_page, "html.parser")
    return souped_html


def find_attrib(content_s, attrib):
    """find an attribute value in a soup object
    Args:
        content_s (soup)
        attrib (str)
    Returns:
        attribute value - if found
        None - if not found
    """
    if content_s.find(text=attrib):
        return content_s.find(text=attrib).parent.findNextSibling().text
    else:
        return None


def find_attrib1(search, def_val):
    """find attribute value and returns default value if attribute
    does not exist
    Args:
        search (soup object)
        def_val (str)
    Returns:
        search text or default value if search object does not exist
    """
    if search:
        return search.get_text()
    else:
        return def_val


def seret_recommend():
    """ parse www.seret.co.il and generates an html page with recommended movies.
    It is possible to use html pages stored in file for regression testing.
    Args:

    Returns:
        none
    """
    requested_days, lowest_acceptable_rate = seret_dialog.get_day_rate()
    showtime_days_vals = {'א:': [True, False, False, False, False, False, False],
                          'ב:': [False, True, False, False, False, False, False],
                          'ג:': [False, False, True, False, False, False, False],
                          'ד:': [False, False, False, True, False, False, False],
                          'ה:': [False, False, False, False, True, False, False],
                          'שישי:': [False, False, False, False, False, True, False],
                          'שבת:': [False, False, False, False, False, False, True],
                          'א - ד:': [True, True, True, True, False, False, False],
                          'א - ה:': [True, True, True, True, True, False, False]}
    from_file = False
    try:
        with open('seret-skip.txt') as skip_file:
            seret_skip = [line.rstrip('\n').split(';') for line in skip_file]
    except FileNotFoundError:
        seret_skip = []
    skip_list_new = []
    result_file = open("seret.html", "w")
    result_file.write(RESULTS_HEADER)
    seret_main_parsed = get_parsed_url(MOVIES_SITE_URL + r'index.asp?catCase=2',
                                       r'htmls\seret-all.html', from_file)
    results = seret_main_parsed.find_all("a", {'href': re.compile(r's_movies.asp\?MID='),
                                               r'style': 'direction:rtl;'})
    for result in results:
        name = result.text
        movie_id = result['href'].split('=')[1]
        if any(movie_id == x[0] for x in seret_skip):
            skip_list_new.append([movie_id, name])
            print(movie_id, ';', name, '-->Skipped')
            continue
        else:
            print(movie_id, ';', name, '-->NOT skipped')
        content_s = get_parsed_url(MOVIES_SITE_URL + r's_movies.asp?MID=' + movie_id,
                                   r'htmls\seret-movie' + movie_id, from_file)

        genres = [s.get_text() for s in content_s.find_all(itemprop='genre')]
        genre_ok = GENRES_NOK.isdisjoint(genres)
        if not genre_ok:
            skip_list_new.append([movie_id, name])
            continue
        rating_value = find_attrib1(content_s.find(itemprop='ratingValue'), '0.0')
        if 0.0 < float(rating_value) < lowest_acceptable_rate:
            skip_list_new.append([movie_id, name])
            continue
        duration = find_attrib1(content_s.find(itemprop='duration'), '0.0')
        desc_text = find_attrib1(content_s.find(id='divDescText'), '')
        if not desc_text:
            desc_text = find_attrib1(content_s.find(itemprop='description'), '')

        reviews = [review_comment.parent for review_comment
                   in content_s.find(id='revboxContent').find_all('div', {'class': 'BGComments'})]

        content_cinemas = get_parsed_url(MOVIES_SITE_URL
                                         + r'showTimesAjax.asp?MID=' + movie_id,
                                         r'htmls\seret-movie-cinemas-' + movie_id, from_file)

        film_hours = []
        cinema_found = False
        city_name = None
        for city_or_cinema in content_cinemas.find_all('div', {'class': ['cityname', 'trow']}):
            if city_or_cinema['class'][0] == 'cityname':
                city_name = city_or_cinema.find('a').contents[0]
                continue
            if city_name not in CITIES_OK:
                continue
            theatre_name = city_or_cinema.find('a').contents[0]
            for dayline in city_or_cinema.find_all('span', {'class': 'dayline'}):
                showtimes_days_text = dayline.find('span', {'class': 'dayname'}).contents[0]
                showtime_days = showtime_days_vals[showtimes_days_text]
                is_matched_day = any([requested_day and showtime_day
                                      for (requested_day, showtime_day)
                                      in zip(requested_days, showtime_days)])
                if not is_matched_day:
                    continue
                hours = dayline.find('span', {'class': 'dayhours'}).contents
                if len(hours) == 0:
                    continue
                for hour in hours[0].split():
                    if hour < '19:00' or hour > '20:30':
                        continue
                    film_hours.append([theatre_name, showtimes_days_text, hour])
                    cinema_found = True
                    break
        if not cinema_found:
            continue
        result_file.write('<br><hr><h2>{};{}</h2>'.format(movie_id, name))
        result_file.write('<p>{}</p>'.format(desc_text))
        movie_pic = content_s.find('div', {'class': 'moviePic'}).img
        movie_pic['src'] = MOVIES_SITE_URL + movie_pic['src']
        result_file.write(str(movie_pic) + '<br>')
        for attrib in ['במאי', 'בכורה: ', 'ז\'אנר', 'אורך', 'מקום / שנה']:
            attrib_found = find_attrib(content_s, attrib)
            if attrib_found:
                result_file.write(RESULTS_FORMAT_ATTRIB.format(100, attrib, attrib_found))
        result_file.write(RESULTS_FORMAT_ATTRIB.format(100, 'דרוג', rating_value))
        result_file.write('<br>')
        for film_hour in film_hours:
            result_file.write(RESULTS_FORMAT_ATTRIB.format(190, film_hour[0],
                                                           film_hour[1] + film_hour[2]))
        for review in reviews:
            result_file.write('<br><br>{}'.format(
                review.find('div', {'class': 'BGComments'}).find_all('div')[0].contents[2]))
            result_file.write('<br><strong>{}</strong>{}'.format(
                review.find('div', {'class': 'BGCommentsRatingSqare'}).text,
                review.find_all('div')[3].text))
    result_file.write(RESULTS_FOOTER)
    result_file.close()

    with open('seret-skip.txt', 'w') as skip_file:
        for skip_movie in skip_list_new:
            skip_file.write(';'.join(skip_movie) + '\n')
    skip_file.close()

    webbrowser.register('chrome', None,
                        webbrowser.BackgroundBrowser(
                            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'))
    webbrowser.get('chrome').open(os.getcwd()+'\\seret.html')

if __name__ == '__main__':
    seret_recommend()
