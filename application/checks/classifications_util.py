from check_bsdd import get_domains, get_classifications, get_classification_object


domains = get_domains()

domain = domains[7]["namespaceUri"]
classifications = get_classifications(domain)

for classification in classifications["domains"][0]["classifications"]:
# classification = classifications["domains"][0]["classifications"][16]
    c_uri = classification['namespaceUri']
    c = get_classification_object(c_uri)
    print(c,"\n")


#import pdb; pdb.set_trace()


