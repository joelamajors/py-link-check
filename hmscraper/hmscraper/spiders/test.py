# URL here
base_url = "https://raque.hatfield.marketing"
base_url = base_url.strip("/")
check_url = base_url.replace("http://", '').replace("https://", '').split("/")[0]

print(check_url)