import random
import time

import requests
from bs4 import BeautifulSoup
import json
from pprint import pprint
import urllib3
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

ua = UserAgent()

urllib3.disable_warnings()

surface_habitable = "80"
prix_min = "180000"
prix_max = "330000"


class Annonce(dict):
    date = None
    id = None
    ref = None
    lien = None
    surface = None
    prix = None
    ville = None
    image = None
    site = None
    description = None


def get_user_agent():
    return ua.random


def get_html_from_selenium(url):
    options = webdriver.ChromeOptions()

    options.add_argument("--disable-gpu")
    options.add_argument('enable-logging')
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
    driver.get(url)

    time.sleep(20)

    html = driver.page_source
    driver.close()
    return html


def century21():
    host = "https://www.century21.fr"

    page_reponse = requests.get(
        host +
        "/annonces/achat-maison-ancien/d-38_isere/s-" +
        surface_habitable +
        "-/b-0-" +
        prix_max)
    if page_reponse.status_code != 200:
        return []

    annonces_a_enregistrer = []

    page = BeautifulSoup(page_reponse.content, 'html.parser')
    # permet de voir la page en code
    annonces = page.select('.js-the-list-of-properties-list-property')
    # . represente la class
    # on prend la plus haute ligne qui contient 1 seule annonce

    for annonce in annonces:
        # tableau des tags des images de l'annonce en cours
        img_element = annonce.select('img')
        prix_element = annonce.select(
            '.c-the-property-thumbnail-with-content__col-right > div:first-child > div:last-child > div:last-child')
        other_element = annonce.select(
            '.c-the-property-thumbnail-with-content__col-right > div:first-child > div:first-child')
        lien_element = annonce.select(
            '.c-the-property-thumbnail-with-content__col-right > div:last-child > div:last-child a')
        description_element = annonce.select(
            '.c-the-property-thumbnail-with-content__col-right .c-text-theme-base')

        other = other_element[0].text.strip().split("\n")

        annonce_to_add = Annonce()
        annonce_to_add.site = "Century21"
        annonce_to_add.ref = other[8].strip().replace('Ref : ', '')
        annonce_to_add.lien = host + lien_element[0].attrs['href']
        if 'data-src' in img_element[0].attrs.keys():
            annonce_to_add.image = host + img_element[0].attrs['data-src']
        else:
            annonce_to_add.image = host + img_element[0].attrs['src']
        annonce_to_add.prix = int(
            prix_element[0].text.replace(
                '€', '').replace(
                ' ', '').strip())
        annonce_to_add.surface = other[5].strip()
        annonce_to_add.ville = other[0].strip()
        annonce_to_add.description = description_element[0].text.strip()

        annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def cimm_immo():
    box_latitude_longitude = "5.422914415166825,45.233777955290144,5.724429597666282,45.4528660694386"

    page_reponse = requests.get(
        "https://api.cimm.com/api/realties?operation=vente&realty_family=maison&room_number__gte=&field_surface__gte=&field_surface__lte=&inhabitable_surface__gte=" + surface_habitable + "&inhabitable_surface__lte=&price__gte=" + prix_min + "&price__lte=" + prix_max + "&fields=id,virtual_visit,realtyphoto_set,realty_family,public_location,room_number,inhabitable_surface,field_surface,operation,photo,price,city_name,city_cp,slug,pool,bedroom_number,garage_number,negotiator,topi_admin,compromise,realtytype&in_bbox=" + box_latitude_longitude + "4&ordering=&sold_rented=false&agency=&limit=200")
    if page_reponse.status_code != 200:
        return []

    annonces_a_enregistrer = []

    dico = page_reponse.json()

    for annonce in dico.get("results"):
        lien = "http://cimm.com/bien/" + annonce.get("slug")

        if lien.__contains__("avec-cimm-estimez-mais-surtout-vendez"):
            continue

        annonce_to_add = Annonce()
        annonce_to_add.site = "CimmImmobilier"
        annonce_to_add.ref = annonce.get('id')
        annonce_to_add.lien = lien
        annonce_to_add.image = annonce.get('photo')
        annonce_to_add.prix = annonce.get('price')
        annonce_to_add.surface = ("Surface : " + str(annonce.get('inhabitable_surface')) + ' m2' if annonce.get(
            'inhabitable_surface') else '') \
            + (" - surface terrain : " + str(annonce.get('field_surface')) + ' m2' if annonce.get(
                'field_surface') else '') \
            + (" - avec garage" if annonce.get('garage_number') else '')
        annonce_to_add.ville = annonce.get("city_name")

        annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def safti():
    page_reponse = requests.post("https://api.safti.fr/public_site/property/search",
                                 json={"page": 1, "limit": 200, "locations": ["department-38"],
                                       "orderByField": "publication_date", "orderByType": "DESC",
                                       "transactionType": "vente", "propertyType": ["maison"],
                                       "livingSpaceMin": surface_habitable,
                                       "budgetMin": prix_min, "budgetMax": prix_max})
    if page_reponse.status_code != 200:
        return []

    annonces_a_enregistrer = []

    dico = page_reponse.json()

    for annonce in dico.get("properties"):
        annonce_to_add = Annonce()
        annonce_to_add.site = "Safti"
        annonce_to_add.date = annonce.get('diffusionDate')
        annonce_to_add.ref = annonce.get('propertyReference')
        annonce_to_add.lien = "https://www.safti.fr/annonces/achat/maison/" + \
                              annonce.get("city").lower().replace(' ', '-') + '/' + \
                              str(annonce.get('propertyReference'))
        annonce_to_add.image = annonce.get('photos')[0].get('urlPhotoLarge')
        annonce_to_add.prix = annonce.get('price')
        annonce_to_add.surface = "surface : " + \
                                 str(annonce.get("propertySurface")) + "m2"
        annonce_to_add.ville = annonce.get("city")

        annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def bien_ici():
    host = "https://www.bienici.com/"

    page_reponse = requests.get(
        host +
        "realEstateAds.json?filters=%7B%22size%22%3A24%2C%22from%22%3A0%2C%22showAllModels%22%3Afalse%2C%22filterType%22%3A%22buy%22%2C%22propertyType%22%3A[%22house%22]%2C%22minPrice%22%3A" +
        prix_min +
        "%2C%22maxPrice%22%3A" +
        prix_max +
        "%2C%22minRooms%22%3A0%2C%22minArea%22%3A" +
        surface_habitable +
        "%2C%22minBedrooms%22%3A0%2C%22minGardenSurfaceArea%22%3A0%2C%22newProperty%22%3Afalse%2C%22page%22%3A1%2C%22sortBy%22%3A%22publicationDate%22%2C%22sortOrder%22%3A%22desc%22%2C%22onTheMarket%22%3A[true]%2C%22mapMode%22%3A%22enabled%22%2C%22zoneIdsByTypes%22%3A%7B%22drawnZone%22%3A[%22615075286bbf5b00bd9059b6%22]%7D%7D&extensionType=extendedIfNoResult&leadingCount=2&access_token=b3qyzXq4Deluc%2FhqKWCs7uM1GJMO7%2BQGWIaNl2sOt0g%3D%3A60b61d6580cdf300b0d5e754&id=60b61d6580cdf300b0d5e754")
    if page_reponse.status_code != 200:
        return []

    annonces_a_enregistrer = []

    dico = page_reponse.json()

    for annonce in dico.get("realEstateAds"):
        annonce_to_add = Annonce()
        annonce_to_add.site = 'BienIci - ' + annonce.get('id').split('-')[0]
        annonce_to_add.date = annonce.get('modificationDate')
        annonce_to_add.ref = annonce.get('reference')
        annonce_to_add.lien = host + "annonce/" + annonce.get('id')
        annonce_to_add.image = annonce.get('photos')[0].get('url_photo')
        annonce_to_add.prix = annonce.get('price')
        annonce_to_add.surface = "surface : " + str(annonce.get("surfaceArea")) + "m2" \
                                 + (' - surface terrain : ' + str(annonce.get('landSurfaceArea')) + "m2" if annonce.get(
                                     'landSurfaceArea') else '') \
            + (' - avec garage' if annonce.get('garagesQuantity')
               and annonce.get('garagesQuantity') > 1 else '')
        annonce_to_add.ville = annonce.get("city")
        annonce_to_add.description = annonce.get("description")

        annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def trenta_immo():
    host = "https://trenta-immobilier.com/"

    page_reponse = requests.post(
        host +
        "acheter",
        data='type_prod=Maison&localisation=&reference_a_afficher=&surface_habitable_min=' +
             surface_habitable +
             '&surface_habitable_max=&prix_min=' +
             prix_min +
             '&prix_max=' +
             prix_max,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded'},
        verify=False)
    if page_reponse.status_code != 200:
        return []

    annonces_a_enregistrer = []

    page = BeautifulSoup(page_reponse.content, 'html.parser')
    annonces = page.select('div > .pure-g .pure-u-1')

    for annonce in annonces:
        lien_element = annonce.select('a')
        image_element = annonce.select('img')
        other_element = annonce.select('a > div:last-child')

        annonce_to_add = Annonce()
        annonce_to_add.site = 'Trenta Immobilier'
        annonce_to_add.lien = host + lien_element[0].attrs['href']
        annonce_to_add.image = image_element[0].attrs['src']
        annonce_to_add.ref = annonce_to_add.image.split('/')[5]
        annonce_to_add.prix = int(
            other_element[0].contents[2].contents[0].replace(
                '€', '').replace(
                ' ', '').strip())
        annonce_to_add.surface = other_element[0].contents[0].strip()
        annonce_to_add.ville = other_element[0].contents[2].contents[2].strip()

        annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def square_habitat():
    host = "https://www.squarehabitat.fr/"

    payload = {'ctl00$cphContent$recherche$typeAnnonce': '0',
               'ctl00$cphContent$recherche$search_id': '38_1',
               'ctl00$cphContent$recherche$search': 'ISERE (38)',
               'ctl00$cphContent$recherche$typeBien': '15',
               'ctl00_cphContent_recherche_prixMini_ClientState': '{"enabled":true,"emptyMessage":"","validationText":"' + prix_min + '","valueAsString":"' + prix_min + '","minValue":0,"maxValue":70368744177664,"lastSetTextBoxValue":"180 000 €"}',
               'ctl00_cphContent_recherche_prixMaxi_ClientState': '{"enabled":true,"emptyMessage":"","validationText":"' + prix_max + '","valueAsString":"' + prix_max + '","minValue":1,"maxValue":70368744177664,"lastSetTextBoxValue":"320 000 €"}',
               'ctl00_cphContent_recherche_surfaceMini': surface_habitable,
               'ctl00_cphContent_recherche_surfaceMini_ClientState': '{"enabled":true,"emptyMessage":"","validationText":"' + surface_habitable + '","valueAsString":"' + surface_habitable + '","minValue":0,"maxValue":70368744177664,"lastSetTextBoxValue":"' + surface_habitable + ' m²"}',
               '__EVENTTARGET': '',
               '__EVENTARGUMENT': '',
               '__LASTFOCUS': '',
               '__VIEWSTATE': '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',
               '__VIEWSTATEGENERATOR': '6A4191C2',
               '__EVENTVALIDATION': 'B9A6KKnznHhk1qjtcF8F6M0zMEykSZ6evJ5p+FtFqGqY2NFkSKPJLYiCir8MtAj3yT0Hx81QIs6ruWY0x/umX/90hrXy+8q2gWgONbmYMKejIj9iCjeD9ze9RjFmegSfD1qzuqm0Kyd2taFZSsNvAG2P3VmojZA3z607FLJkm/F+g0SBj9Y39BYNP01bUhtcvIIxk2a58Tt3zdiBDhJFvRDav8TSJkAzFKN2WCHkkFsSrOgWfVtDqGWO/Ni/JEGxp7+Nn1OxEb1J2npO4MiDdZqv7VJ0o4rmq+6YC5O+DI7kr2LR0VMZs/iLXIPBUH3jIBWQ0pyE/o+0nE/DXO5q3aUbUuRqv9HE6jwrYByPdlw6F5XSaA3bILPloYJXl8qZbYzfkR+PoymrhT4vHiCWItzp+wH9yxsyHUg6sdNkuHzV5rKRItFPV+tdXlfbmDXcGDL4RqJOFnpduJnVfHRkvqkJ56w2G3aAxF+HX53cOIcbB0B2ZUwa6T+gdAgjbdRqQV22l+MVMehhUZR2yFGdlRXMbecZDdve8N+fmFCkwgjyPO899el8G8bYxloMY0rZuudzkNVZ0Ujpl8hCUR2W8RjVOqWYtJUwK6JNGj1RFsXV2wVuy+dpXT1VSdQ4laPk1vAaX/roCHpy3pv/uwkDzE82rht2SeTuefhj8zBBKyW4+Upfmg2/gQT4Df8Qs427amy5xBNQpYv1z7ZeSOEvEFkDMkzZANaynuVHjOlLjJ1W1NrxNOX7gCvRkMag1DO3vIXW2hNT1g0k7fdPtj2i44r/2b9M2xZ3N4QtO/b8vlR9MGEa+zYpW3UUZKZFLbMvvnlc/pSBzDCYpdkc90BzyW8nBs3QbwxuBwThgwhYx6fHI9hl8jl2otZpnFpduGN5zOkiTNMcos36OE+HZpKWeAfGQUuViETViNCR9gIVXq/EaaledFRBxN/3SvBnP9S1mOFcJj62JubrNxV6v2BmxyhiZKIV5vGmwx0dr2wQ2rKrkQP0vj3xCOR7GB/7+T14XzcphhnayFNeu8IOfTr6uX6Q9t7vyGO1etZF26RE46PLdomIxX0fPbZSRFIHjHY03ZK3Bjc9kODwkJ0BhYQspoeMyokv4UkZm66zY4hde0OzpiWzq6mh+Zm1vZkqTw/90LEQy1WK3SRl/AHB4u6nKhq6cYqnpEHLO3/NAROo/eirvLUFHHsZALNEAq/iroNPGHV/8WoGUIIQ56VospSpPSzcZK0='}

    page_reponse = requests.request(
        "POST", host + "resultats.aspx", data=payload)

    if page_reponse.status_code != 200:
        return []

    annonces_a_enregistrer = []

    page = BeautifulSoup(page_reponse.content, 'html.parser')
    annonces = page.select('.blog-post')

    for annonce in annonces:
        lien_element = annonce.select('a:first-child')
        image_element = annonce.select('img')
        other_element = annonce.select('strong')

        annonce_to_add = Annonce()
        annonce_to_add.site = 'Square Habitat'
        annonce_to_add.lien = host + lien_element[0].attrs['href']
        annonce_to_add.image = image_element[0].attrs['src']
        annonce_to_add.ref = annonce_to_add.lien.split(
            '-')[-1].replace('.aspx', '')
        annonce_to_add.prix = int(
            other_element[1].text.replace(
                '€', '').replace(
                ' ', '').strip())
        annonce_to_add.surface = other_element[2].text.strip()
        annonce_to_add.ville = other_element[0].text.strip()

        annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def meilleurs_agents():
    host = "https://www.meilleursagents.com/"
    nb_page = 1

    annonces_a_enregistrer = []

    while True:
        page_reponse = requests.get(
            host +
            "annonces/achat/search/?sort=current_price_date%3Adesc&page=" +
            str(nb_page) +
            "&transaction_types=TRANSACTION_TYPE.SELL&place_ids=77&item_types=ITEM_TYPE.HOUSE&min_price=" +
            prix_min +
            "&max_price=" +
            prix_max +
            "&min_area=" +
            surface_habitable +
            "&max_area=&room_counts=0%2C3%2C4%2C5",
            headers={
                "User-Agent": get_user_agent()})

        if page_reponse.status_code != 200:
            return []

        page = BeautifulSoup(page_reponse.content, 'html.parser')
        annonces = page.select('.listing-item')

        for annonce in annonces:
            lien_element = annonce.select('a.listing-item__picture-container')
            image_element = annonce.select('img.listing-item__picture')
            surface_element = annonce.select('.listing-characteristic')
            ville_element = annonce.select('.text--small.text--muted')
            prix_element = annonce.select('.listing-price')

            annonce_to_add = Annonce()
            annonce_to_add.site = 'Meilleurs Agents'
            annonce_to_add.lien = lien_element[0].attrs['href']
            annonce_to_add.image = 'https:' + image_element[0].attrs['src']
            annonce_to_add.ref = annonce_to_add.lien.split('/')[-2]
            annonce_to_add.prix = int(
                prix_element[0].text.replace(
                    '€', '').replace(
                    ' ', '').strip())
            annonce_to_add.surface = surface_element[0].text.strip()
            annonce_to_add.ville = ville_element[0].text.strip()

            annonces_a_enregistrer.append(annonce_to_add)

        if len(page.select('.pagination__navigator--next')) > 0:
            nb_page += 1
        else:
            break

    return annonces_a_enregistrer


def capi():
    host = "https://www.capifrance.fr/"

    page_reponse = requests.get(
        host +
        "residentiel/acheter/recherche?propertyTypes%5B%5D=HOUSE&location%5B%5D=NT_4IGMsGyHYIJVUte-l8USsC&distance=15&priceMin=" +
        prix_min +
        "&priceMax=" +
        prix_max +
        "&mainSurfaceAreaMin=" +
        surface_habitable +
        "&mainSurfaceAreaMax=&outdoorsLotSizeMin=&outdoorsLotSizeMax=&mandateNumber=&sort=startDate-desc&expandSearchCity=Moirans")

    if page_reponse.status_code != 200:
        return []

    annonces_a_enregistrer = []

    page = BeautifulSoup(page_reponse.content, 'html.parser')
    annonces = page.select('#se-hits .properties-content')

    for annonce in annonces:
        lien_element = annonce.select('.properties-content-img a')
        image_element = annonce.select('.properties-content-img img')
        detail_element = annonce.select('.properties-sizes')
        ville_element = annonce.select('.properties-infos-location')
        prix_element = annonce.select('.pricevalue_euro')
        id_element = annonce.select('.properties-like')

        annonce_to_add = Annonce()
        annonce_to_add.site = 'Capi'
        annonce_to_add.lien = lien_element[0].attrs['href']
        annonce_to_add.image = image_element[0].attrs['src']
        annonce_to_add.ref = id_element[0].attrs['data-id']
        annonce_to_add.prix = int(
            prix_element[0].text.replace(
                '€', '').replace(
                ' ', '').strip())
        annonce_to_add.surface = detail_element[0].text.strip()
        annonce_to_add.ville = ville_element[0].text.split('\n')[1].strip()

        annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def aubreton():
    host = "https://www.aubreton.immo/"

    page_reponse = requests.post(
        host +
        "fr/ventes",
        headers={
            'Cookie': 'PHPSESSID=s70nqfnhueks5kst79nbi0j9jk; device_view=full',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': get_user_agent()},
        data="transaction_search%5Bcommune%5D=15486&transaction_search%5BtypeBien%5D%5B%5D=2&transaction_search%5Bprix_min%5D=" +
             prix_min +
             "&transaction_search%5Bprix_max%5D=" +
             prix_max +
             "&transaction_search%5BrayonCommune%5D=15&transaction_search%5Btri%5D=dateModification%7Cdesc&transaction_search%5BnoMandat%5D=&transaction_search%5BreferenceInterne%5D=&transaction_search%5BventeEtranger%5D=0&transaction_search%5BsecteurByFirstLetterMandat%5D=&transaction_search%5Bpiece_min%5D=&transaction_search%5Bpiece_max%5D=&transaction_search%5Bsurface_max%5D=")

    if page_reponse.status_code != 200:
        return []

    annonces_a_enregistrer = []

    page = BeautifulSoup(page_reponse.content, 'html.parser')
    annonces = page.select('.fiches-immo')

    for annonce in annonces:
        lien_element = annonce.select('a')
        image_element = annonce.select('a img')
        detail_element = annonce.select('.accroche')
        ville_element = annonce.select('.communeBien')
        prix_element = annonce.select('.prix')
        id_element = annonce.select('.reference')

        annonce_to_add = Annonce()
        annonce_to_add.site = 'Aubreton'
        annonce_to_add.lien = host.strip('/') + lien_element[0].attrs['href']
        annonce_to_add.image = image_element[0].attrs['src']
        annonce_to_add.ref = id_element[0].text.replace('Réf. : ', '').strip()
        annonce_to_add.prix = int(
            prix_element[0].text.replace(
                'Prix de vente : ',
                '').replace(
                '€',
                '').replace(
                ' ',
                '').strip())
        annonce_to_add.surface = detail_element[0].text.split('\n')[0].strip()
        annonce_to_add.ville = ville_element[0].text.split('-')[0].strip()

        annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def bievre_immo():
    host = 'https://www.bievre-immobilier.com/'

    page_reponse = requests.get(
        host +
        "ajax/ListeBien.php?tri=DATE_MAJ&menuSave=1&page=1&TypeModeListeForm=text&ope=1&filtre=8&prixmin=" +
        prix_min +
        "&prixmax=" +
        prix_max +
        "&lieu=V%C2%A422289%C2%A4Moirans+(38430)%C2%A40.7910908689120%C2%A40.0971227208581%C2%A415&lieu-alentour=15&langue=fr&MapWidth=100&MapHeight=0&DataConfig=JsConfig.GGMap.Liste&Pagination=0")

    if page_reponse.status_code != 200:
        return []

    annonces_a_enregistrer = []

    page = BeautifulSoup(page_reponse.content, 'html.parser')
    annonces = page.select('.liste-bien-container')

    for annonce in annonces:
        lien_element = annonce.select('.liste-bien-photo a')
        image_element = annonce.select('.liste-bien-photo a img:last-child')
        detail_element = annonce.select('.extrait-desc')
        ville_element = annonce.select('.liste-bien-ville')
        prix_element = annonce.select('.liste-bien-price')
        id_element = annonce.select('.liste-bien-offre span:first-child')

        annonce_to_add = Annonce()
        annonce_to_add.site = 'BièvreImmobilier'
        annonce_to_add.lien = lien_element[0].attrs['href']
        annonce_to_add.image = image_element[0].attrs['src']
        annonce_to_add.ref = id_element[0].text.replace(
            'ref.  n°  ', '').strip()
        annonce_to_add.prix = int(
            prix_element[0].text.replace(
                'Prix : ',
                '').replace(
                '€',
                '').replace(
                '*',
                '').replace(
                ' ',
                '').strip())
        annonce_to_add.surface = detail_element[0].text.split('\n')[0].strip()
        annonce_to_add.ville = ville_element[0].text.split('-')[0].strip()

        annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def imio():
    host = 'http://www.imio.fr/'

    page_reponse = requests.get(
        host +
        "recherche?a=1&b%5B%5D=house&c=38&radius=0&d=" +
        prix_min +
        "&e=" +
        prix_max +
        "&f=" +
        surface_habitable +
        "&x=illimité&do_search=Rechercher")

    if page_reponse.status_code != 200:
        return []

    annonces_a_enregistrer = []

    page = BeautifulSoup(page_reponse.content, 'html.parser')
    annonces = page.select('.res_tbl')

    for annonce in annonces:
        lien_element = annonce.select('a')
        ville_element = annonce.select('.loc_details')
        detail_element = annonce.select('.res_tbl_title_inner')
        prix_element = annonce.select('.res_tbl_value')

        annonce_to_add = Annonce()
        annonce_to_add.site = 'Imio'
        annonce_to_add.lien = host + lien_element[0].attrs['href']
        annonce_to_add.image = lien_element[0].attrs['style'].split(
            'background-image:url(')[1].split(')')[0]
        annonce_to_add.ref = lien_element[0].attrs['href'].split('_')[
            1].replace('.htm', '')
        annonce_to_add.prix = int(
            prix_element[0].text.replace(
                '€',
                '').replace(
                ' ',
                '').strip())
        annonce_to_add.surface = ville_element[0].text.strip(
        ) + '. ' + detail_element[0].text.strip()
        annonce_to_add.ville = 'Isere'

        annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def kd_immobilier():
    host = 'https://www.kdimmobilier.com/'

    page_reponse = requests.get(
        host +
        "nos-biens-a-vendre?field_ville_cp_filter_value_fsf%5B%5D=38500+-+Voiron&field_ville_cp_filter_value_fsf%5B%5D=38120+-+Saint-Égrève&field_type_de_bien_value=Maison&field_prix_value=All&field_surface_value=All&field_nombre_de_chambres_value=All")

    if page_reponse.status_code != 200:
        return []

    annonces_a_enregistrer = []

    page = BeautifulSoup(page_reponse.content, 'html.parser')
    annonces = page.select('.views-row')

    for annonce in annonces:
        lien_element = annonce.select('a')
        image_element = annonce.select('img')
        ville_element = annonce.select('.views-field-field-ville')
        prix_element = annonce.select('.views-field-field-prix')
        ref_element = annonce.select('.views-field-field-reference')

        annonce_to_add = Annonce()
        annonce_to_add.site = 'KdImmobilier'
        annonce_to_add.lien = host + lien_element[0].attrs['href']
        annonce_to_add.image = host + image_element[0].attrs['src']
        annonce_to_add.ref = ref_element[0].text.strip()
        annonce_to_add.prix = int(
            prix_element[0].text.split('-')[-1].replace(
                '€',
                '').replace(
                ' ',
                '').strip())
        annonce_to_add.surface = prix_element[0].text.split(
            '-')[0].replace('de ', '').strip()
        annonce_to_add.ville = ville_element[0].text.replace(
            'Maison à vendre à ', '').strip()

        if int(prix_min) <= annonce_to_add.prix <= int(prix_max):
            annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def klein_immobilier():
    host = 'https://www.klein-immobilier.com/'

    page_reponse = requests.get(
        host +
        "catalog/advanced_search_result.php?action=update_search&search_id=1714868691326376&map_polygone=&C_28_search=EGAL&C_28_type=UNIQUE&C_28=Vente&C_28_tmp=Vente&C_27_search=EGAL&C_27_type=TEXT&C_27=2&C_27_tmp=2&C_34_MIN=" +
        surface_habitable + "&C_34_search=COMPRIS&C_34_type=NUMBER&C_30_search=COMPRIS&C_30_type=NUMBER&C_30_MAX=" +
        prix_max + "&C_65_search=CONTIENT&C_65_type=TEXT&C_65=38140+RIVES&C_65_tmp=38140+RIVES&keywords=&C_30_MIN=" +
        prix_min +
        "&C_33_search=COMPRIS&C_33_type=NUMBER&C_33_MIN=&C_33_MAX=&C_34_MAX=&C_36_MIN=&C_36_search=COMPRIS&C_36_type=NUMBER&C_36_MAX=&C_38_MAX=&C_38_MIN=&C_38_search=COMPRIS&C_38_type=NUMBER&C_47_type=NUMBER&C_47_search=COMPRIS&C_47_MIN=&C_94_type=FLAG&C_94_search=EGAL&C_94=")

    if page_reponse.status_code != 200:
        return []

    annonces_a_enregistrer = []

    page = BeautifulSoup(page_reponse.content, 'html.parser')
    annonces = page.select('.item-product')

    for annonce in annonces:
        lien_element = annonce.select('.visuel-product a')
        image_element = annonce.select('img')
        ville_element = annonce.select('.products-name')
        prix_element = annonce.select('.products-price')
        ref_element = annonce.select('.products-ref')
        detail_element = annonce.select('.products-desc')

        annonce_to_add = Annonce()
        annonce_to_add.site = 'KleinImmobilier'
        annonce_to_add.lien = host + lien_element[0].attrs['href']
        annonce_to_add.image = host + image_element[0].attrs['src']
        annonce_to_add.ref = ref_element[0].text.replace(
            'Ref. :  ', '').strip()
        annonce_to_add.prix = int(
            prix_element[0].text.replace(
                '\xa0', '').replace(
                '\x80',
                '').strip())
        annonce_to_add.surface = detail_element[0].text.strip()
        annonce_to_add.ville = ville_element[0].text.split('-')[0].strip()

        annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def iad_france():
    host = 'https://www.iadfrance.fr/'
    nb_page = 1

    annonces_a_enregistrer = []

    while True:
        page_reponse = requests.get(
            host +
            "rechercher/annonces?surface_min=" +
            surface_habitable +
            "&surface_max=&price_min=" +
            prix_min +
            "&price_max=" +
            prix_max +
            "&id=&departments=Is%C3%A8re&tags_list=%5B%7B%22type%22%3A%22departments%22%2C%22value%22%3A%22Is%5Cu00e8re%22%2C%22name%22%3A%22Is%5Cu00e8re+%22%7D%5D&transaction_type=Vente&generic_type%5B%5D=MV&frequency=Journali%C3%A8re&sort=ad.firstPublishDate&dir=desc&page=" +
            str(nb_page))

        if page_reponse.status_code != 200:
            return []

        page = BeautifulSoup(page_reponse.content, 'html.parser')
        annonces = page.select('.estate')

        for annonce in annonces:
            lien_element = annonce.select('.c-offer__title a')
            image_element = annonce.select('.c-offer__img img')
            detail_element = annonce.select('.c-offer__footer div:first-child')
            ville_element = annonce.select('.c-offer__localization a')
            prix_element = annonce.select('.c-offer__price')
            id_element = annonce.select('.estate .c-offer__time')

            annonce_to_add = Annonce()
            annonce_to_add.site = 'IadFrance'
            annonce_to_add.lien = host.strip(
                '/') + lien_element[0].attrs['href'].strip()
            annonce_to_add.image = image_element[0].attrs['src']
            annonce_to_add.ref = id_element[0].text.replace(
                'Référence :\n', '').strip()
            annonce_to_add.prix = int(
                prix_element[0].text.replace(
                    '€', '').replace(
                    ' ', '').strip())
            annonce_to_add.surface = detail_element[0].text.strip()
            annonce_to_add.ville = ville_element[0].text.split('(')[0].strip()

            annonces_a_enregistrer.append(annonce_to_add)

        if len(page.select('.pagination .icon-arrow-right')) > 0:
            nb_page += 1
        else:
            break

    return annonces_a_enregistrer


def proximmo():
    host = 'https://www.proximmo-voiron.fr/'
    nb_page = 1

    annonces_a_enregistrer = []

    while True:
        page_reponse = requests.get(
            host +
            "annonces?id_polygon=498839&localisation_etendu=1&visite_virtuelle=&categorie=vente&type_bien=maison&nb_pieces=&surface=" +
            surface_habitable +
            "&budget=" +
            prix_max +
            "&localisation=1+secteur+d%C3%A9fini&submit=Rechercher&page=" +
            str(nb_page))

        if page_reponse.status_code != 200:
            return []

        page = BeautifulSoup(page_reponse.content, 'html.parser')
        annonces = page.select('.liste-offres li')

        for annonce in annonces:
            lien_element = annonce.select('.photo-offre a')
            image_element = annonce.select('.photo-offre img')
            detail_element = annonce.select('.accroche')
            detail2_element = annonce.select('.description')
            ville_element = annonce.select('.info-offre a')
            prix_element = annonce.select('.prix span')

            annonce_to_add = Annonce()
            annonce_to_add.site = 'ProxImmo'
            annonce_to_add.lien = host + lien_element[0].attrs['href']
            annonce_to_add.image = image_element[0].attrs['data-src']
            annonce_to_add.ref = lien_element[0].attrs['href'].split('-')[-1].replace('.htm', '').strip()
            annonce_to_add.prix = int(prix_element[0].attrs['content'])
            annonce_to_add.surface = detail_element[0].text.strip() + '. ' + detail2_element[0].text.strip()
            annonce_to_add.ville = ville_element[0].text\
                .replace('Maison', '')\
                .replace('Villa', '')\
                .replace('\n', '')\
                .strip()

            if int(prix_min) <= annonce_to_add.prix <= int(prix_max):
                annonces_a_enregistrer.append(annonce_to_add)

        if len(page.select('.pagelinks-next:not(.pagelinks-disabled)')) > 0:
            nb_page += 1
        else:
            break

    return annonces_a_enregistrer


"""
Ne fonctionne pas à cause de datadome :'(
Alternative possible : https://rapidapi.com/mayliepaul/api/lbc-aio/
"""
def le_bon_coin():
    host = "https://www.leboncoin.fr/"
    html = get_html_from_selenium(
        host + "recherche?category=9&text=NOT%20construire%20NOT%20%22projet%20de%20construction%22%20NOT%20investisseurs%20NOT%20%22sera%20disponible%20fin%22&locations=Voiron_38500__45.36724_5.59114_5415_10000&immo_sell_type=old&real_estate_type=1&price=" +
        prix_min + '-' + prix_max +
        "&rooms=2-8&square=" +
        surface_habitable + "-max")

    annonces_a_enregistrer = []

    page = BeautifulSoup(html, 'html.parser')
    annonces = page.select('a[data-qa-id="aditem_container"]')

    for annonce in annonces:
        lien_element = annonce
        image_element = annonce.select('picture img')

        annonce_to_add = Annonce()
        annonce_to_add.site = 'LeBonCoin'
        annonce_to_add.lien = host + lien_element.attrs['href']
        annonce_to_add.image = image_element[0].attrs['src']

        annonces_a_enregistrer.append(annonce_to_add)

    return annonces_a_enregistrer


def run_json():
    annonces = century21() + cimm_immo() + safti() + bien_ici() + trenta_immo() + \
        square_habitat() + meilleurs_agents() + capi() + klein_immobilier() + \
        aubreton() + bievre_immo() + iad_france() + imio() + kd_immobilier() + proximmo()
    for annonce in annonces:
        annonce.id = annonce.site + '_' + str(annonce.ref)
    print(json.dumps([ob.__dict__ for ob in annonces]))


def test():
    pprint([ob.__dict__ for ob in proximmo()])


#test()
run_json()
