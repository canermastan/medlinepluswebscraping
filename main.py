import string
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import click

class MedlineScraper:
    def __init__(self):
        self.base_url = "https://medlineplus.gov/druginfo"
        self.drug_links = set()

    def get_categories(self):
        letters = string.ascii_uppercase
        result = list(map(lambda letter: self.base_url + "/drug_{}a.html".format(letter), letters))
        result.append("https://medlineplus.gov/druginfo/drug_00.html")
        return result

    def get_source(self, url):
        r = requests.get(url)
        if r.status_code == 200:
            return BeautifulSoup(r.content, "html5lib")
        else:
            return False

    def get_drug_links(self, source):
        drug_elements = source.find('ul', {'id': 'index'}).find_all('li')
        drug_list = list(map(lambda drug: self.base_url + drug.find('a').get('href').replace(".", "", 1), drug_elements))
        return set(drug_list)

    def find_all_drug_links(self):
        categories = self.get_categories()
        bar = tqdm(categories, unit=" category link")
        for category_link in bar:
            bar.set_description(category_link)
            category_source = self.get_source(category_link)
            result = self.get_drug_links(category_source)
            self.drug_links = self.drug_links.union(result)
        return self.drug_links

    def get_name(self,source):
        try:
            return source.find("h1",{'class':'with-also'}).text
        except Exception:
            return None
    def get_section_info(self,source,id_element):
        try:
            title = source.find("div",{'id':id_element}).find("h2").text
            content = source.find("div",{'id':id_element}).find("div",{'class':'section-body'}).text
            return dict(
                title = title,
                content = content
            )
        except Exception:
            return None

    def scrape_drugs(self,start,end):
        if start is None:
            start = 0
        result = list()
        links = list(self.find_all_drug_links())
        if end is None:
            end = len(links)
        bar = tqdm(links[start:end], unit= "drug links")
        for link in bar:
            sections = list()
            bar.set_description(link)
            drug_source = self.get_source(link)
            name = self.get_name(drug_source)
            why = self.get_section_info(drug_source,"why")
            how = self.get_section_info(drug_source,"how")
            other_uses = self.get_section_info(drug_source,"other-uses")
            sections.append(why)
            sections.append(how)
            sections.append(other_uses)
            result.append(dict(
                name=name, #create json
                url=link,
                sections = sections
            )),
        return result
    def write_as_json(self,data,filename="result.json"):
        with open(filename,"w",encoding="utf-8") as f:
            f.write(json.dumps(data,indent=2))


if __name__ == '__main__':
    @click.command()
    @click.option("--start",type=int)
    @click.option("--end",type=int)
    @click.option("--filename")
    def run(start,end,filename):
        scraper = MedlineScraper()
        data = scraper.scrape_drugs(start,end)
        scraper.write_as_json(data, filename)
    run()