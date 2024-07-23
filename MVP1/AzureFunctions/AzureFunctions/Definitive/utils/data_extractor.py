import os
import requests
from dotenv import load_dotenv

_ = load_dotenv("./Definitive/config/def_api.env")


class DataExtractor:
    """
    Class to extract data from definitive
    """

    def __init__(self, client_id, map_title, expand):
        """
        init function of class to initialise variables
        """
        self.client_id = client_id
        self.username = os.getenv('DEFINITIVE_USERNAME')
        self.password = os.getenv('DEFINITIVE_PASSWORD')
        self.url = os.getenv('DEFINITIVE_URL')
        self.payload = {"grant_type": "password",
                        "username": self.username,
                        "password": self.password}
        self.client_dict = {}

        self.map_title = map_title[0]['data']
        print("map_title:\t", self.map_title)

        self.expand = expand[0]['data']['expand']
        print("expand:\t", self.expand)
        self.executive_lists = [v for v in self.map_title['Executives'].values()]

    def get_access_token(self):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        r = requests.post(self.url + '/token', data=self.payload, headers=headers)
        access_token = r.json()['access_token']
        return access_token

    def extract_ele_info(self, expand):
        access_token = self.get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.get(f'{self.url}/odata-v4/Hospitals({self.client_id})?$expand={expand}', headers=headers)
        return res.json()

    def extract_all_elemets(self):
        elements_to_extract = [v for sub_dict in self.map_title.values() for v in sub_dict.values()]
        expand_list = self.expand
        # to extract base elsements
        res = self.extract_ele_info(expand_list[0])
        element_data = {k: v for k, v in res.items() if k in elements_to_extract}
        self.client_dict.update(element_data)
        # to extract expand elements
        for category in expand_list:
            res = self.extract_ele_info(category)
            if category == 'Executives':
                x = res['Executives']
                executive_latest_date = sorted(x, key=lambda x: x['DateEntered'], reverse=True)
                exexu = {}
                exist_tit = set()
                for item in executive_latest_date:
                    name = item['Title']
                    if name not in exist_tit:
                        if item['Title'] in self.executive_lists:
                            exexu[name] = item['ExecName']
                            exist_tit.add(name)
                self.client_dict.update(exexu)
            else:
                element_data = {k: v for k, v in res[category].items() if k in elements_to_extract}
                self.client_dict.update(element_data)
        corrected_dict = {
            category: {title: self.client_dict[key] for title, key in mappings.items() if key in self.client_dict} for
            category, mappings in self.map_title.items()}
        print(corrected_dict)
        return corrected_dict


if __name__ == "__main__":
    extract = DataExtractor("4685")
    extract.extract_all_elemets()
