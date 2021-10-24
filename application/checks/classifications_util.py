import requests
import json

base_url = "https://bs-dd-api-prototype.azurewebsites.net/api/"

def get_domains():
    url = "https://bs-dd-api-prototype.azurewebsites.net/api/Domain/v2"
    r = requests.get(url)
    return json.loads(r.text) 



def get_classifications(domain_uri):
    return json.loads(requests.get(base_url + "SearchListOpen/v2/", params={'DomainNamespaceUri': domain_uri}).text)
    

def get_classification(domain_ref, item_ref):
    domain_found = 0
    classification = 0
    for domain in get_domains():
        if domain['name'] == domain_ref:
            domain_uri = domain['namespaceUri']
            params = {'DomainNamespaceUri': domain_uri}
            list_of_classifications = json.loads(requests.get(base_url + "SearchListOpen/v2/", params=params).text)

            if list_of_classifications["numberOfClassificationsFound"] > 0:
                found_ref = 0
                for c in list_of_classifications['domains'][0]['classifications']:
                    # example_classification = [0]
                    ref = c['namespaceUri'].split("/")[-1]
                
                    if ref == item_ref:
                        found_ref = 1
                        return c
                    # else:
                    #     print('errr', ref, '  ', item_ref)
                    
                if found_ref == 0:
                    #print('No classification matched with the reference code provided' , '(',item_ref,')')
                    return 'No classification matched with the reference code provided.'

            else:
                #print('No classification found for the domain ', domain_ref)
                return 'No classification found for this domain.'
        
    if domain_found == 0:
        #print(domain_ref)
        print("The domain", domain_ref,"has not been found in the bSDD.")
        return 'This domain has not been found in the bSDD.'
   
def get_classification_object(uri):
    url = "https://bs-dd-api-prototype.azurewebsites.net/api/Classification/v3"
    base_url = "https://bs-dd-api-prototype.azurewebsites.net/api/"

    r = requests.get(url, {'namespaceUri':uri})
    return json.loads(r.text) 

domains = get_domains()

domain = domains[7]["namespaceUri"]
classifications = get_classifications(domain)

for classification in classifications["domains"][0]["classifications"]:
# classification = classifications["domains"][0]["classifications"][16]
    c_uri = classification['namespaceUri']
    c = get_classification_object(c_uri)
    print(c,"\n")


#import pdb; pdb.set_trace()


